import os
import csv
import json
import hashlib
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional, Tuple

import requests

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# ============================================================
# CONFIGURATION
# ============================================================
def get_config_val(key: str, default: str) -> str:
    if STREAMLIT_AVAILABLE:
        try:
            if hasattr(st, "secrets") and key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    return os.getenv(key, default)

import threading

# Detect if running in local development or production cloud
DEFAULT_API_URL = "http://127.0.0.1:8000" if (os.getenv("USE_LOCAL_API") == "true") else "https://futuremining-1.onrender.com"
API_BASE_URL = get_config_val("API_BASE_URL", DEFAULT_API_URL).rstrip("/")
TIMEOUT = 6.0

DB_USER = get_config_val("DB_USER", "postgres.cjlxqfwwdrrqvjlsjoay")
DB_PASSWORD = get_config_val("DB_PASSWORD", "K56*#$jkl565p")
DB_HOST = get_config_val("DB_HOST", "aws-0-ap-northeast-2.pooler.supabase.com")
DB_PORT = get_config_val("DB_PORT", "6543")
DB_NAME = get_config_val("DB_NAME", "postgres")

# Cached direct engine
_direct_engine = None

def get_direct_engine():
    global _direct_engine
    if _direct_engine is not None:
        return _direct_engine
    try:
        from sqlalchemy import create_engine
        encoded_pwd = quote_plus(DB_PASSWORD)
        db_url = f"postgresql+pg8000://{DB_USER}:{encoded_pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        _direct_engine = create_engine(
            db_url,
            connect_args={"ssl_context": True},
            pool_pre_ping=True,
            pool_recycle=300,
        )
        return _direct_engine
    except Exception:
        return None

# ============================================================
# AUTOMATIC BACKGROUND WAKE-UP
# ============================================================
_wakeup_started = False

def wake_up_backend_async():
    """Trigger background wake-up ping to Render if asleep."""
    global _wakeup_started
    if _wakeup_started:
        return
    _wakeup_started = True

    def _ping():
        try:
            requests.get(f"{API_BASE_URL}/health", timeout=60.0)
        except Exception:
            pass

    t = threading.Thread(target=_ping, daemon=True)
    t.start()

# Automatically trigger on module load whenever someone visits the app
wake_up_backend_async()


# ============================================================
# STATUS & CONNECTION MODE (Cached to eliminate lag)
# ============================================================
_cached_conn_mode = None
_cached_mode_timestamp = 0.0

def get_api_status() -> bool:
    """Check if the FastAPI backend is online and responding."""
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=2.0)
        return resp.status_code == 200
    except Exception:
        return False

def get_connection_mode(force_refresh: bool = False) -> str:
    """Returns 'fastapi', 'direct_db', or 'offline' (cached for 60s for speed)."""
    global _cached_conn_mode, _cached_mode_timestamp
    import time
    now = time.time()
    if not force_refresh and _cached_conn_mode is not None and (now - _cached_mode_timestamp) < 60:
        return _cached_conn_mode

    if get_api_status():
        _cached_conn_mode = "fastapi"
    else:
        eng = get_direct_engine()
        if eng:
            try:
                from sqlalchemy import text
                with eng.connect() as conn:
                    conn.execute(text("SELECT 1"))
                _cached_conn_mode = "direct_db"
            except Exception:
                _cached_conn_mode = "offline"
        else:
            _cached_conn_mode = "offline"

    _cached_mode_timestamp = now
    return _cached_conn_mode


# ============================================================
# AUTHENTICATION
# ============================================================
def hash_password_local(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return pwd_hash, salt

def verify_password_local(password: str, pwd_hash: str, salt: str) -> bool:
    calc_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return secrets.compare_digest(calc_hash, pwd_hash)


# ============================================================
# LOCAL OFFLINE STORE (accounts + progress, no backend needed)
# Local account ids are negative ints; guests use None.
# ============================================================
LOCAL_USERS_PATH = Path(__file__).parent / "data" / "local_users.json"
LOCAL_PROGRESS_PATH = Path(__file__).parent / "data" / "local_progress.json"
_local_store_lock = threading.Lock()
_local_topic_cache: Optional[Dict[str, str]] = None


def _is_local_user_id(user_id: Any) -> bool:
    return isinstance(user_id, bool) is False and isinstance(user_id, int) and user_id < 0


def _read_json_list(path: Path) -> List[Dict[str, Any]]:
    try:
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(stored, list):
                return stored
    except Exception:
        pass
    return []


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            json.dump(payload, tmp_file, indent=2)
            tmp_file.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def _local_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _local_topic_map() -> Dict[str, str]:
    """Map question id -> topic from the bundled CSVs (cached)."""
    global _local_topic_cache
    if _local_topic_cache is not None:
        return _local_topic_cache
    mapping: Dict[str, str] = {}
    data_dir = Path(__file__).parent / "data"
    for csv_name in ("gate_questions_1000.csv", "GATE_800_Questions_Classified.csv"):
        csv_path = data_dir / csv_name
        if not csv_path.exists():
            continue
        try:
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    qid = str(row.get("id", "")).strip()
                    if qid and qid not in mapping:
                        mapping[qid] = str(row.get("topic", "") or "General").strip() or "General"
        except Exception:
            continue
    _local_topic_cache = mapping
    return mapping


def _public_local_user(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": record["id"],
        "username": record["username"],
        "full_name": record.get("full_name") or record["username"],
        "email": record.get("email"),
        "auth_source": "local",
    }


def register_local_user(
    username: str,
    password: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Create an account in the on-device store (offline mode)."""
    clean_name = (username or "").strip()
    if not clean_name or not password:
        return False, "Please enter username and password", None
    try:
        with _local_store_lock:
            users = _read_json_list(LOCAL_USERS_PATH)
            lowered = clean_name.lower()
            if any(str(u.get("username", "")).lower() == lowered for u in users):
                return False, f"Username '{clean_name}' is already taken", None
            pwd_hash, salt = hash_password_local(password)
            next_id = min([int(u.get("id", 0)) for u in users] + [0]) - 1
            record = {
                "id": next_id,
                "username": clean_name,
                "full_name": (full_name or "").strip() or clean_name,
                "email": (email or "").strip() or None,
                "password_hash": pwd_hash,
                "salt": salt,
                "created_at": _local_now(),
            }
            users.append(record)
            _write_json_atomic(LOCAL_USERS_PATH, users)
        return True, "Account created on this device (offline mode). Welcome!", _public_local_user(record)
    except Exception as exc:
        return False, f"Could not create local account: {exc}", None


def login_local_user(
    username: str,
    password: str,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Authenticate against the on-device store (offline mode)."""
    clean_name = (username or "").strip()
    if not clean_name or not password:
        return False, "Please enter username and password", None
    with _local_store_lock:
        users = _read_json_list(LOCAL_USERS_PATH)
    for record in users:
        if str(record.get("username", "")).lower() == clean_name.lower():
            if verify_password_local(password, record.get("password_hash", ""), record.get("salt", "")):
                return True, f"Welcome back, {record.get('full_name') or record['username']}! (offline mode)", _public_local_user(record)
            return False, "Invalid username or password", None
    return False, "Invalid username or password", None


def _record_local_attempt(
    user_id: int,
    question_id: int,
    selected_option: int,
    is_correct: bool,
    mode: str,
) -> bool:
    try:
        with _local_store_lock:
            progress = _read_json_list(LOCAL_PROGRESS_PATH)
            # Progress file holds a list of mixed records; attempts carry kind="attempt".
            progress.append({
                "kind": "attempt",
                "user_id": user_id,
                "question_id": question_id,
                "topic": _local_topic_map().get(str(question_id), "General"),
                "selected_option": selected_option,
                "is_correct": bool(is_correct),
                "mode": mode,
                "created_at": _local_now(),
            })
            _write_json_atomic(LOCAL_PROGRESS_PATH, progress)
        return True
    except Exception:
        return False


def _save_local_session(
    user_id: int,
    mode: str,
    score: float,
    total_questions: int,
    correct_count: int,
    incorrect_count: int,
    unattempted_count: int,
    time_taken_seconds: int = 0,
    details_json: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    try:
        with _local_store_lock:
            progress = _read_json_list(LOCAL_PROGRESS_PATH)
            session_id = sum(1 for r in progress if r.get("kind") == "session") + 1
            record = {
                "kind": "session",
                "id": session_id,
                "user_id": user_id,
                "mode": mode,
                "score": float(score),
                "total_questions": total_questions,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "unattempted_count": unattempted_count,
                "time_taken_seconds": time_taken_seconds,
                "details_json": details_json,
                "created_at": _local_now(),
            }
            progress.append(record)
            _write_json_atomic(LOCAL_PROGRESS_PATH, progress)
        return {k: v for k, v in record.items() if k != "kind"}
    except Exception:
        return None


def _local_user_summary(user_id: int) -> Optional[Dict[str, Any]]:
    """Build the analytics summary shape from the on-device store."""
    with _local_store_lock:
        users = _read_json_list(LOCAL_USERS_PATH)
        progress = _read_json_list(LOCAL_PROGRESS_PATH)
    user_row = next((u for u in users if u.get("id") == user_id), None)
    if not user_row:
        return None
    attempts = [r for r in progress if r.get("kind") == "attempt" and r.get("user_id") == user_id]
    sessions = [r for r in progress if r.get("kind") == "session" and r.get("user_id") == user_id]

    total_att = len(attempts)
    total_corr = sum(1 for r in attempts if r.get("is_correct"))
    acc_pct = round((total_corr / max(1, total_att)) * 100, 1) if total_att > 0 else 0.0

    mock_sessions = [s for s in sessions if s.get("mode") == "mock_test"]
    best_score = float(max([s.get("score", 0.0) for s in mock_sessions] + [0.0]))

    by_topic: Dict[str, Dict[str, int]] = {}
    for attempt in attempts:
        topic = str(attempt.get("topic") or "General")
        bucket = by_topic.setdefault(topic, {"attempted": 0, "correct": 0})
        bucket["attempted"] += 1
        if attempt.get("is_correct"):
            bucket["correct"] += 1

    topic_breakdown = []
    strong: List[str] = []
    weak: List[str] = []
    for topic in sorted(by_topic, key=lambda t: by_topic[t]["attempted"], reverse=True):
        bucket = by_topic[topic]
        t_acc = round((bucket["correct"] / max(1, bucket["attempted"])) * 100, 1)
        topic_breakdown.append({
            "topic": topic,
            "attempted": bucket["attempted"],
            "correct": bucket["correct"],
            "accuracy_pct": t_acc,
        })
        if bucket["attempted"] >= 3:
            if t_acc >= 70.0:
                strong.append(topic)
            elif t_acc < 50.0:
                weak.append(topic)

    recent = sorted(sessions, key=lambda s: str(s.get("created_at", "")), reverse=True)[:10]
    recent_sessions = []
    for session in recent:
        recent_sessions.append({
            "id": session.get("id"),
            "user_id": session.get("user_id"),
            "mode": session.get("mode"),
            "score": session.get("score"),
            "total_questions": session.get("total_questions"),
            "correct_count": session.get("correct_count"),
            "incorrect_count": session.get("incorrect_count"),
            "unattempted_count": session.get("unattempted_count"),
            "time_taken_seconds": session.get("time_taken_seconds", 0),
            "created_at": session.get("created_at"),
        })

    return {
        "user_id": user_row["id"],
        "username": user_row["username"],
        "full_name": user_row.get("full_name"),
        "total_attempted": total_att,
        "total_correct": total_corr,
        "accuracy_pct": acc_pct,
        "mock_tests_taken": len(mock_sessions),
        "best_mock_score": best_score,
        "strong_topics": strong[:5],
        "weak_topics": weak[:5],
        "topic_breakdown": topic_breakdown,
        "recent_sessions": recent_sessions,
    }

# ============================================================
# GAMIFICATION — XP, miner ranks, daily streaks (on-device)
# ============================================================
MINER_RANKS = [
    (0, "⛏️", "Trainee Miner"),
    (150, "🪨", "Stone Chipper"),
    (400, "🛠️", "Shaft Worker"),
    (800, "💡", "Vein Finder"),
    (1400, "🥈", "Silver Prospector"),
    (2200, "🥇", "Gold Prospector"),
    (3200, "💎", "Diamond Foreman"),
    (4500, "👑", "Mining Tycoon"),
]

GAMIFICATION_PATH = Path(__file__).parent / "data" / "local_gamification.json"


def _read_json_dict(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                return stored
    except Exception:
        pass
    return {}


def gamification_key(user: Optional[Dict[str, Any]]) -> str:
    if not user:
        return "guest:anonymous"
    source = str(user.get("auth_source") or "cloud")
    name = str(user.get("username") or "anonymous").lower()
    return f"{source}:{name}"


def _rank_for_xp(xp: int) -> int:
    idx = 0
    for i, (threshold, _icon, _name) in enumerate(MINER_RANKS):
        if xp >= threshold:
            idx = i
    return idx


def get_gamification(user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Current XP / rank / streak snapshot for a user (never raises)."""
    try:
        key = gamification_key(user)
        with _local_store_lock:
            store = _read_json_dict(GAMIFICATION_PATH)
        xp = int((store.get("xp") or {}).get(key, 0))
        streak = int((store.get("streaks") or {}).get(key, {}).get("count", 0))
    except Exception:
        xp, streak = 0, 0
    rank_idx = _rank_for_xp(xp)
    _threshold, icon, name = MINER_RANKS[rank_idx]
    if rank_idx + 1 < len(MINER_RANKS):
        next_threshold, _next_icon, next_name = MINER_RANKS[rank_idx + 1]
        span = max(1, next_threshold - MINER_RANKS[rank_idx][0])
        pct = min(100.0, max(0.0, (xp - MINER_RANKS[rank_idx][0]) / span * 100.0))
        to_next = max(0, next_threshold - xp)
    else:
        next_name = ""
        pct = 100.0
        to_next = 0
    return {
        "xp": xp,
        "streak": streak,
        "rank_idx": rank_idx,
        "rank_icon": icon,
        "rank_name": name,
        "next_name": next_name,
        "to_next": to_next,
        "progress_pct": round(pct, 1),
    }


def award_xp(user: Optional[Dict[str, Any]], amount: int) -> Dict[str, Any]:
    """Add XP + streak bonus and touch the daily streak. Returns fresh stats."""
    key = gamification_key(user)
    today = datetime.now().date().isoformat()
    with _local_store_lock:
        store = _read_json_dict(GAMIFICATION_PATH)
        xp_map = store.get("xp") or {}
        streak_map = store.get("streaks") or {}

        old_xp = int(xp_map.get(key, 0))
        old_rank = _rank_for_xp(old_xp)

        entry = streak_map.get(key) or {"count": 0, "last": ""}
        last = str(entry.get("last") or "")
        if last == today:
            streak = int(entry.get("count", 0)) or 1
        else:
            yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
            streak = int(entry.get("count", 0)) + 1 if last == yesterday else 1
        streak_map[key] = {"count": streak, "last": today}

        bonus = min(5 * streak, 50)
        gained = int(amount) + bonus
        new_xp = old_xp + gained
        xp_map[key] = new_xp

        store["xp"] = xp_map
        store["streaks"] = streak_map
        try:
            _write_json_atomic(GAMIFICATION_PATH, store)
        except Exception:
            pass

    new_rank = _rank_for_xp(new_xp)
    info = get_gamification(user)
    info["gained"] = gained
    info["bonus"] = bonus
    info["leveled_up"] = new_rank > old_rank
    info["old_rank_name"] = MINER_RANKS[old_rank][2]
    return info


def notify_xp_gain(gained: int, info: Dict[str, Any]) -> None:
    """Queue XP toasts (and rank-up balloons) for the next rerun."""
    if not STREAMLIT_AVAILABLE:
        return
    try:
        pending = st.session_state.get("pending_celebration") or {"toasts": []}
        toasts = list(pending.get("toasts", []))
        toasts.append((f"+{gained} XP", "⛏️"))
        if info.get("leveled_up"):
            toasts.append(
                (f"Rank up! You are now {info['rank_icon']} {info['rank_name']}", "🎉")
            )
        st.session_state.pending_celebration = {
            "leveled_up": bool(pending.get("leveled_up") or info.get("leveled_up")),
            "toasts": toasts[-4:],
        }
    except Exception:
        pass


def register_user(username: str, password: str, full_name: Optional[str] = None, email: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Register a new user via FastAPI or direct DB."""
    # 1. Try FastAPI
    try:
        payload = {
            "username": username.strip(),
            "password": password,
            "full_name": full_name.strip() if full_name else None,
            "email": email.strip() if email else None,
        }
        resp = requests.post(f"{API_BASE_URL}/api/auth/register", json=payload, timeout=TIMEOUT)
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            return True, data.get("message", "Registered successfully"), data.get("user")
        elif resp.status_code in (400, 409):
            return False, data.get("detail", "Registration failed"), None
    except Exception:
        pass

    # 2. Direct DB Fallback
    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            clean_username = username.strip().lower()
            with eng.connect() as conn:
                existing = conn.execute(
                    text("SELECT id FROM users WHERE LOWER(username) = :u"),
                    {"u": clean_username}
                ).first()
                if existing:
                    return False, f"Username '{username}' is already taken", None

                pwd_hash, salt = hash_password_local(password)
                result = conn.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, salt, full_name)
                        VALUES (:u, :e, :h, :s, :fn)
                        RETURNING id, username, full_name, email
                    """),
                    {
                        "u": username.strip(),
                        "e": email.strip() if email else None,
                        "h": pwd_hash,
                        "s": salt,
                        "fn": full_name.strip() if full_name else username.strip(),
                    }
                )
                conn.commit()
                row = result.mappings().first()
                if row:
                    return True, "Registered successfully! Welcome to FutureMining.", dict(row)
        except Exception as e:
            return False, f"Database error: {e}", None

    # 3. Offline fallback: on-device account store
    return register_local_user(username, password, full_name, email)

def login_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Authenticate user via FastAPI or direct DB."""
    # 1. Try FastAPI
    try:
        payload = {"username": username.strip(), "password": password}
        resp = requests.post(f"{API_BASE_URL}/api/auth/login", json=payload, timeout=TIMEOUT)
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            return True, data.get("message", "Login successful"), data.get("user")
        elif resp.status_code == 401:
            return False, data.get("detail", "Invalid username or password"), None
    except Exception:
        pass

    # 2. Direct DB Fallback
    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            clean_username = username.strip().lower()
            with eng.connect() as conn:
                row = conn.execute(
                    text("SELECT id, username, password_hash, salt, full_name, email FROM users WHERE LOWER(username) = :u"),
                    {"u": clean_username}
                ).mappings().first()

                if not row or not verify_password_local(password, row["password_hash"], row["salt"]):
                    return False, "Invalid username or password", None

                user_dict = {
                    "id": row["id"],
                    "username": row["username"],
                    "full_name": row["full_name"],
                    "email": row["email"],
                }
                return True, f"Welcome back, {row['full_name'] or row['username']}!", user_dict
        except Exception as e:
            return False, f"Database error: {e}", None

    # 3. Offline fallback: on-device account store
    return login_local_user(username, password)
<<<<<<< HEAD
=======


# ============================================================
# REMEMBER ME (persistent login tokens)
# Only a SHA-256 hash of each token is stored server-side;
# the raw token lives in the visitor's own browser cookie.
# ============================================================
REMEMBER_COOKIE_NAME = "fm_remember"
REMEMBER_TOKENS_PATH = Path(__file__).parent / "data" / "remember_tokens.json"
REMEMBER_TOKEN_DAYS = 30


def _remember_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _prune_remember_tokens(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now_stamp = _local_now()
    return [t for t in tokens if str(t.get("expires_at", "")) > now_stamp]


def create_remember_token(user: Optional[Dict[str, Any]]) -> Optional[str]:
    """Mint a persistent login token for `user` (None for guests)."""
    if not user or user.get("id") is None or user.get("is_guest"):
        return None
    token = secrets.token_urlsafe(32)
    snapshot = {key: user.get(key) for key in ("id", "username", "full_name", "email", "auth_source")}
    snapshot["auth_source"] = user.get("auth_source") or "server"
    record = {
        "token_hash": _remember_token_hash(token),
        "user": snapshot,
        "created_at": _local_now(),
        "expires_at": (datetime.now() + timedelta(days=REMEMBER_TOKEN_DAYS)).strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        with _local_store_lock:
            tokens = _prune_remember_tokens(_read_json_list(REMEMBER_TOKENS_PATH))
            tokens.append(record)
            _write_json_atomic(REMEMBER_TOKENS_PATH, tokens)
        return token
    except Exception:
        return None


def validate_remember_token(token: str) -> Optional[Dict[str, Any]]:
    """Return the remembered user dict if `token` is valid, else None."""
    if not token:
        return None
    wanted = _remember_token_hash(token)
    try:
        with _local_store_lock:
            tokens = _read_json_list(REMEMBER_TOKENS_PATH)
            fresh = _prune_remember_tokens(tokens)
            if len(fresh) != len(tokens):
                _write_json_atomic(REMEMBER_TOKENS_PATH, fresh)
            match = next((t for t in fresh if t.get("token_hash") == wanted), None)
        if not match:
            return None
        user = dict(match.get("user") or {})
        if user.get("id") is None:
            return None
        # Local accounts: make sure the account still exists.
        if user.get("auth_source") == "local":
            with _local_store_lock:
                users = _read_json_list(LOCAL_USERS_PATH)
            if not any(u.get("id") == user.get("id") for u in users):
                revoke_remember_token(token)
                return None
        user["is_guest"] = False
        return user
    except Exception:
        return None


def revoke_remember_token(token: str) -> None:
    """Delete a persistent login token (logout / stale cookie)."""
    if not token:
        return
    try:
        wanted = _remember_token_hash(token)
        with _local_store_lock:
            tokens = _read_json_list(REMEMBER_TOKENS_PATH)
            kept = [t for t in tokens if t.get("token_hash") != wanted]
            if len(kept) != len(tokens):
                _write_json_atomic(REMEMBER_TOKENS_PATH, kept)
    except Exception:
        pass
>>>>>>> origin/arena/01a08e34-futuremining


# ============================================================
# QUESTIONS & GAME LADDER
# ============================================================
def fetch_questions(
    topic: Optional[str] = None,
    difficulty: Optional[int] = None,
    limit: int = 1000,
    skip: int = 0,
) -> List[Dict[str, Any]]:
    """Fetch questions from FastAPI backend with direct DB fallback."""
    # 1. Try FastAPI
    try:
        params: Dict[str, Any] = {"limit": limit, "skip": skip}
        if topic:
            params["topic"] = topic
        if difficulty is not None:
            params["difficulty"] = difficulty
        resp = requests.get(f"{API_BASE_URL}/api/questions", params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # 2. Direct DB Fallback
    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            query_str = "SELECT id, subject, topic, difficulty, question, option_a, option_b, option_c, option_d, correct FROM gate_questions WHERE 1=1"
            params_dict: Dict[str, Any] = {"limit": limit, "skip": skip}
            if topic:
                query_str += " AND topic = :topic"
                params_dict["topic"] = topic
            if difficulty is not None:
                query_str += " AND difficulty = :diff"
                params_dict["diff"] = difficulty
            query_str += " ORDER BY id OFFSET :skip LIMIT :limit"

            with eng.connect() as conn:
                rows = conn.execute(text(query_str), params_dict).mappings().all()
                return [dict(r) for r in rows]
        except Exception:
            pass

    return []

def fetch_topics() -> List[Dict[str, Any]]:
    """Fetch topics with question counts."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/topics", timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                rows = conn.execute(text("""
                    SELECT topic, COUNT(id)
                    FROM gate_questions
                    WHERE topic IS NOT NULL
                    GROUP BY topic
                    ORDER BY COUNT(id) DESC
                """)).fetchall()
                return [{"topic": r[0], "question_count": r[1]} for r in rows if r[0]]
        except Exception:
            pass

    return []

def fetch_game_ladder() -> Optional[List[Dict[str, Any]]]:
    """Fetch 15 progressive difficulty questions for the Millionaire challenge."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/game/ladder", timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            sql = text("""
                SELECT id, subject, topic, difficulty, question, option_a, option_b, option_c, option_d, correct
                FROM (
                    SELECT DISTINCT ON (difficulty) *
                    FROM gate_questions
                    ORDER BY difficulty, random()
                ) sub
                ORDER BY difficulty;
            """)
            with eng.connect() as conn:
                rows = conn.execute(sql).mappings().all()
                return [dict(r) for r in rows]
        except Exception:
            pass

    return None

def fetch_swap_question(level: int, exclude_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Fetch an alternate question for a specific level."""
    try:
        params = {"level": level}
        if exclude_id is not None:
            params["exclude_id"] = exclude_id
        resp = requests.get(f"{API_BASE_URL}/api/game/swap", params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            sql = "SELECT id, subject, topic, difficulty, question, option_a, option_b, option_c, option_d, correct FROM gate_questions WHERE difficulty = :level"
            params_dict: Dict[str, Any] = {"level": level}
            if exclude_id is not None:
                sql += " AND id != :ex_id"
                params_dict["ex_id"] = exclude_id
            sql += " ORDER BY random() LIMIT 1"

            with eng.connect() as conn:
                row = conn.execute(text(sql), params_dict).mappings().first()
                if row:
                    return dict(row)
        except Exception:
            pass

    return None

def verify_answer_server(question_id: int, selected_option: int) -> Optional[Dict[str, Any]]:
    """Verify an answer securely via FastAPI backend or direct DB."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/game/verify",
            json={"question_id": question_id, "selected_option": selected_option},
            timeout=TIMEOUT
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                row = conn.execute(
                    text("SELECT correct FROM gate_questions WHERE id = :qid"),
                    {"qid": question_id}
                ).mappings().first()
                if row:
                    corr = int(row["correct"])
                    return {
                        "is_correct": (selected_option == corr),
                        "correct_option": corr,
                        "explanation": f"The correct answer is Option {chr(65 + corr)}."
                    }
        except Exception:
            pass

    return None


# ============================================================
# PROGRESS TRACKING & ANALYTICS
# ============================================================
def _record_question_attempt_sync(
    user_id: int,
    question_id: int,
    selected_option: int,
    is_correct: bool,
    mode: str = "practice"
) -> bool:
    """Internal synchronous saver for question attempts."""
    try:
        payload = {
            "user_id": user_id,
            "question_id": question_id,
            "selected_option": selected_option,
            "is_correct": is_correct,
            "mode": mode,
        }
        resp = requests.post(f"{API_BASE_URL}/api/progress/attempt", json=payload, timeout=TIMEOUT)
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO user_question_attempts (user_id, question_id, selected_option, is_correct, mode)
                        VALUES (:uid, :qid, :opt, :corr, :m)
                    """),
                    {
                        "uid": user_id,
                        "qid": question_id,
                        "opt": selected_option,
                        "corr": is_correct,
                        "m": mode,
                    }
                )
                conn.commit()
                return True
        except Exception:
            pass

    return False

def record_question_attempt(
    user_id: int,
    question_id: int,
    selected_option: int,
    is_correct: bool,
    mode: str = "practice",
    async_save: bool = True
) -> bool:
    """Record single question attempt (runs in background for zero lag)."""
    if user_id is None:
        return False  # guest: nothing to persist
    if _is_local_user_id(user_id):
        return _record_local_attempt(user_id, question_id, selected_option, is_correct, mode)
    if async_save:
        t = threading.Thread(
            target=_record_question_attempt_sync,
            args=(user_id, question_id, selected_option, is_correct, mode),
            daemon=True
        )
        t.start()
        return True
    return _record_question_attempt_sync(user_id, question_id, selected_option, is_correct, mode)

def save_test_session(
    user_id: int,
    mode: str,
    score: float,
    total_questions: int,
    correct_count: int,
    incorrect_count: int,
    unattempted_count: int,
    time_taken_seconds: int = 0,
    details_json: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Persist a completed mock exam or game session to database."""
    if user_id is None:
        return None  # guest: nothing to persist
    if _is_local_user_id(user_id):
        return _save_local_session(
            user_id, mode, score, total_questions, correct_count,
            incorrect_count, unattempted_count, time_taken_seconds, details_json,
        )
    payload = {
        "user_id": user_id,
        "mode": mode,
        "score": float(score),
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "unattempted_count": unattempted_count,
        "time_taken_seconds": time_taken_seconds,
        "details_json": details_json,
    }

    try:
        resp = requests.post(f"{API_BASE_URL}/api/progress/test-session", json=payload, timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                res = conn.execute(
                    text("""
                        INSERT INTO user_test_sessions (user_id, mode, score, total_questions, correct_count, incorrect_count, unattempted_count, time_taken_seconds, details_json)
                        VALUES (:uid, :m, :s, :tq, :cc, :ic, :uc, :tts, :dj)
                        RETURNING id, user_id, mode, score, total_questions, correct_count, incorrect_count, unattempted_count, time_taken_seconds, created_at
                    """),
                    {
                        "uid": user_id,
                        "m": mode,
                        "s": score,
                        "tq": total_questions,
                        "cc": correct_count,
                        "ic": incorrect_count,
                        "uc": unattempted_count,
                        "tts": time_taken_seconds,
                        "dj": details_json,
                    }
                )
                conn.commit()
                row = res.mappings().first()
                if row:
                    return dict(row)
        except Exception:
            pass

    return None

def get_user_summary(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full analytics summary for a user."""
    if _is_local_user_id(user_id):
        return _local_user_summary(user_id)
    try:
        resp = requests.get(f"{API_BASE_URL}/api/progress/{user_id}/summary", timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                user_row = conn.execute(text("SELECT id, username, full_name FROM users WHERE id = :uid"), {"uid": user_id}).mappings().first()
                if not user_row:
                    return None

                att_row = conn.execute(text("""
                    SELECT COUNT(*), SUM(CASE WHEN is_correct THEN 1 ELSE 0 END)
                    FROM user_question_attempts
                    WHERE user_id = :uid
                """), {"uid": user_id}).fetchone()

                total_att = int(att_row[0] or 0)
                total_corr = int(att_row[1] or 0)
                acc_pct = round((total_corr / max(1, total_att)) * 100, 1) if total_att > 0 else 0.0

                mock_rows = conn.execute(text("""
                    SELECT COUNT(*), COALESCE(MAX(score), 0)
                    FROM user_test_sessions
                    WHERE user_id = :uid AND mode = 'mock_test'
                """), {"uid": user_id}).fetchone()

                mock_count = int(mock_rows[0] or 0)
                best_score = float(mock_rows[1] or 0.0)

                topic_rows = conn.execute(text("""
                    SELECT q.topic, COUNT(a.id) AS att, SUM(CASE WHEN a.is_correct THEN 1 ELSE 0 END) AS corr
                    FROM user_question_attempts a
                    JOIN gate_questions q ON a.question_id = q.id
                    WHERE a.user_id = :uid AND q.topic IS NOT NULL
                    GROUP BY q.topic
                    ORDER BY att DESC
                """), {"uid": user_id}).fetchall()

                topic_breakdown = []
                strong = []
                weak = []
                for tr in topic_rows:
                    tname = tr[0]
                    t_att = int(tr[1])
                    t_corr = int(tr[2] or 0)
                    t_acc = round((t_corr / max(1, t_att)) * 100, 1)
                    topic_breakdown.append({
                        "topic": tname,
                        "attempted": t_att,
                        "correct": t_corr,
                        "accuracy_pct": t_acc,
                    })
                    if t_att >= 3:
                        if t_acc >= 70.0:
                            strong.append(tname)
                        elif t_acc < 50.0:
                            weak.append(tname)

                sess_rows = conn.execute(text("""
                    SELECT id, user_id, mode, score, total_questions, correct_count, incorrect_count, unattempted_count, time_taken_seconds, created_at
                    FROM user_test_sessions
                    WHERE user_id = :uid
                    ORDER BY created_at DESC
                    LIMIT 10
                """), {"uid": user_id}).mappings().all()

                return {
                    "user_id": user_row["id"],
                    "username": user_row["username"],
                    "full_name": user_row["full_name"],
                    "total_attempted": total_att,
                    "total_correct": total_corr,
                    "accuracy_pct": acc_pct,
                    "mock_tests_taken": mock_count,
                    "best_mock_score": best_score,
                    "strong_topics": strong[:5],
                    "weak_topics": weak[:5],
                    "topic_breakdown": topic_breakdown,
                    "recent_sessions": [dict(sr) for sr in sess_rows],
                }
        except Exception:
            pass

    return None


# ============================================================
# REVIEW QUEUE
# ============================================================
def flag_question_server(question_id: int, reason: str = "Flagged by user") -> bool:
    """Flag a question in review queue."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/reviews/flag",
            json={"question_id": int(question_id), "reason": reason},
            timeout=TIMEOUT
        )
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                existing = conn.execute(
                    text("SELECT id FROM review_queue WHERE question_id = :qid"),
                    {"qid": int(question_id)}
                ).first()
                if not existing:
                    conn.execute(
                        text("INSERT INTO review_queue (question_id, reason) VALUES (:qid, :r)"),
                        {"qid": int(question_id), "r": reason}
                    )
                    conn.commit()
                return True
        except Exception:
            pass

    return False

def get_flagged_question_ids() -> set[str]:
    """Retrieve all flagged question IDs."""
    try:
        resp = requests.get(f"{API_BASE_URL}/api/reviews/flagged", timeout=TIMEOUT)
        if resp.status_code == 200:
            return set(resp.json())
    except Exception:
        pass

    eng = get_direct_engine()
    if eng:
        try:
            from sqlalchemy import text
            with eng.connect() as conn:
                rows = conn.execute(text("SELECT question_id FROM review_queue")).fetchall()
                return {str(r[0]) for r in rows}
        except Exception:
            pass

    return set()
