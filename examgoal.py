import time
import pandas as pd
import streamlit as st
import api_client

OPTION_LETTERS = ("A", "B", "C", "D")

# ============================================================
# EXAMGOAL PRACTICE MODE
# ============================================================
def render_practice_mode(question_frame: pd.DataFrame):
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #334155;">
            <h2 style="color: #38bdf8; margin: 0 0 0.5rem 0; font-size: 1.5rem;">📚 GATEMining Practice Portal</h2>
            <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">
                Topic-wise GATE Mining questions with instant answer verification, explanations, and database review reporting.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Filter row
    f_col1, f_col2, f_col3 = st.columns([2, 1.2, 1.5])

    all_topics = ["All Topics"] + sorted([str(t) for t in question_frame["topic"].unique() if str(t).strip()])
    with f_col1:
        selected_topic = st.selectbox("📌 Select Subject / Topic", all_topics, index=0)

    with f_col2:
        diff_options = ["All Difficulties"] + [f"Level {i}" for i in range(1, 16)]
        selected_diff = st.selectbox("⚡ Difficulty Tier", diff_options, index=0)

    with f_col3:
        search_kw = st.text_input("🔍 Search Keyword", placeholder="e.g. eigenvalue, ventilation...")

    # Filter dataframe
    filtered = question_frame.copy()
    if selected_topic != "All Topics":
        filtered = filtered[filtered["topic"] == selected_topic]
    if selected_diff != "All Difficulties":
        level_num = int(selected_diff.split()[1])
        filtered = filtered[filtered["difficulty"] == level_num]
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered = filtered[filtered["question"].astype(str).str.lower().str.contains(kw)]

    total_count = len(filtered)
    st.markdown(f"<p style='color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;'>Showing <strong>{min(total_count, 20)}</strong> of <strong>{total_count}</strong> matching questions</p>", unsafe_allow_html=True)

    if filtered.empty:
        st.info("No questions matched your filters. Try selecting 'All Topics' or clearing the search.")
        return

    # Action Buttons
    display_rows = filtered.head(20)

    for idx, row in display_rows.iterrows():
        q_id = int(row.get("id", idx))
        correct_idx = int(row.get("correct", 0))

        with st.container(border=True):
            hdr_col, badge_col = st.columns([4, 1])
            with hdr_col:
                st.markdown(f"**Q{q_id}. {row.get('topic', 'General')}** &nbsp; <span style='color: #f59e0b; font-size: 0.85rem;'>[Level {row.get('difficulty', 1)}]</span>", unsafe_allow_html=True)
            with badge_col:
                if st.button("🚩 Flag", key=f"flag_prac_{q_id}", help="Report this question for review"):
                    if api_client.flag_question_server(q_id, "Flagged in practice mode"):
                        st.toast(f"Question #{q_id} reported for review!", icon="✅")
                    else:
                        st.toast("Flag recorded locally.", icon="⚠️")

            st.markdown(f"<div style='font-size: 1.05rem; margin: 0.5rem 0 1rem 0; line-height: 1.5;'>{row['question']}</div>", unsafe_allow_html=True)

            opts = [str(row[f"option_{l.lower()}"]) for l in OPTION_LETTERS]

            user_choice = st.radio(
                "Choose your option:",
                options=list(range(4)),
                format_func=lambda i: f"{OPTION_LETTERS[i]}. {opts[i]}",
                key=f"prac_q_{q_id}",
                index=None
            )

            c_btn, c_res = st.columns([1.5, 3])
            with c_btn:
                check = st.button("Check Answer", key=f"check_btn_{q_id}")

            if check:
                with c_res:
                    if user_choice is None:
                        st.warning("Please select an option first.")
                    else:
                        is_right = (user_choice == correct_idx)
                        user = st.session_state.get("user")
                        if user:
                            api_client.record_question_attempt(
                                user_id=user["id"],
                                question_id=q_id,
                                selected_option=user_choice,
                                is_correct=is_right,
                                mode="practice",
                            )
                            st.caption(f"💾 Attempt saved to {user.get('username')}'s profile")
                        if is_right:
                            _xp = api_client.award_xp(user, 15)
                            api_client.notify_xp_gain(_xp["gained"], _xp)
                            st.success(f"✅ Correct! Option {OPTION_LETTERS[correct_idx]} is the right answer.")
                        else:
                            st.error(f"❌ Incorrect. You selected {OPTION_LETTERS[user_choice]}, but the correct answer is {OPTION_LETTERS[correct_idx]}.")

            with st.expander("💡 View Solution & Correct Key"):
                st.markdown(f"**Correct Answer:** Option **{OPTION_LETTERS[correct_idx]}** ({opts[correct_idx]})")
                st.markdown(f"**Topic:** {row.get('topic', 'Mining Engineering')}")


# ============================================================
# EXAMGOAL GATE MOCK TEST MODE
# ============================================================
def render_mock_test_mode(question_frame: pd.DataFrame):
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #334155;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="color: #10b981; margin: 0 0 0.25rem 0; font-size: 1.5rem;">⏱️ GATEMining Mock Test</h2>
                    <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">
                        Official GATE pattern: +1.0 Mark for Correct, -0.33 Mark for Incorrect. Color-coded question palette & database score saving.
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Mock Test Configuration (before test starts)
    if "mock_test_started" not in st.session_state:
        st.session_state.mock_test_started = False

    if not st.session_state.mock_test_started and not st.session_state.get("mock_submitted", False):
        st.markdown("### 📋 Select Test Pattern")
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.markdown("#### ⚡ Quick Sprint")
                st.markdown("**10 Questions** · 15 Mins")
                st.caption("Ideal for rapid concept testing")
                if st.button("Start 10 Q Test", key="btn_start_10", type="primary", use_container_width=True):
                    sample_size = min(10, len(question_frame))
                    st.session_state.mock_questions = question_frame.sample(n=sample_size, random_state=int(time.time()) % 10000).to_dict(orient="records")
                    st.session_state.mock_answers = {}
                    st.session_state.mock_marked_review = set()
                    st.session_state.mock_current_idx = 0
                    st.session_state.mock_submitted = False
                    st.session_state.mock_saved_to_db = False
                    st.session_state.mock_start_time = time.time()
                    st.session_state.mock_test_started = True
                    st.rerun()

        with c2:
            with st.container(border=True):
                st.markdown("#### 📖 Sectional Mock")
                st.markdown("**25 Questions** · 45 Mins")
                st.caption("Comprehensive multi-subject test")
                if st.button("Start 25 Q Test", key="btn_start_25", type="primary", use_container_width=True):
                    sample_size = min(25, len(question_frame))
                    st.session_state.mock_questions = question_frame.sample(n=sample_size, random_state=int(time.time()) % 10000).to_dict(orient="records")
                    st.session_state.mock_answers = {}
                    st.session_state.mock_marked_review = set()
                    st.session_state.mock_current_idx = 0
                    st.session_state.mock_submitted = False
                    st.session_state.mock_saved_to_db = False
                    st.session_state.mock_start_time = time.time()
                    st.session_state.mock_test_started = True
                    st.rerun()

        with c3:
            with st.container(border=True):
                st.markdown("#### 🏆 Full GATE Simulation")
                st.markdown("**65 Questions** · 180 Mins")
                st.caption("Full length GATE Mining test")
                if st.button("Start 65 Q Test", key="btn_start_65", type="primary", use_container_width=True):
                    sample_size = min(65, len(question_frame))
                    st.session_state.mock_questions = question_frame.sample(n=sample_size, random_state=int(time.time()) % 10000).to_dict(orient="records")
                    st.session_state.mock_answers = {}
                    st.session_state.mock_marked_review = set()
                    st.session_state.mock_current_idx = 0
                    st.session_state.mock_submitted = False
                    st.session_state.mock_saved_to_db = False
                    st.session_state.mock_start_time = time.time()
                    st.session_state.mock_test_started = True
                    st.rerun()
        return

    questions = st.session_state.get("mock_questions", [])
    current_idx = st.session_state.get("mock_current_idx", 0)
    total_q = len(questions)

    # 1. SUMMARY VIEW AFTER SUBMISSION
    if st.session_state.get("mock_submitted", False):
        st.balloons()
        st.markdown("### 🏆 GATE Mock Test Performance Report")

        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0

        for idx, q in enumerate(questions):
            ans = st.session_state.mock_answers.get(idx)
            corr = int(q.get("correct", 0))
            if ans is None:
                unattempted_count += 1
            elif ans == corr:
                correct_count += 1
            else:
                incorrect_count += 1

        total_score = round((correct_count * 1.0) - (incorrect_count * 0.33), 2)
        accuracy = round((correct_count / max(1, correct_count + incorrect_count)) * 100, 1) if (correct_count + incorrect_count) > 0 else 0.0

        # Auto-save to database if logged in
        if not st.session_state.get("mock_saved_to_db", False):
            user = st.session_state.get("user")
            if user:
                time_taken = int(time.time() - st.session_state.get("mock_start_time", time.time()))
                api_client.save_test_session(
                    user_id=user["id"],
                    mode="mock_test",
                    score=total_score,
                    total_questions=total_q,
                    correct_count=correct_count,
                    incorrect_count=incorrect_count,
                    unattempted_count=unattempted_count,
                    time_taken_seconds=time_taken,
                )
                for idx, q in enumerate(questions):
                    ans = st.session_state.mock_answers.get(idx)
                    if ans is not None:
                        api_client.record_question_attempt(
                            user_id=user["id"],
                            question_id=int(q["id"]),
                            selected_option=ans,
                            is_correct=(ans == int(q["correct"])),
                            mode="mock_test",
                        )
                if correct_count > 0:
                    _mxp = api_client.award_xp(user, 25 * correct_count)
                    api_client.notify_xp_gain(_mxp["gained"], _mxp)
                st.session_state.mock_saved_to_db = True
                st.toast("Test results saved to your profile!", icon="💾")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Score", f"{total_score} / {total_q}", delta=f"{accuracy}% Accuracy")
        m2.metric("Correct Answers", f"{correct_count} (+{correct_count} marks)", delta_color="normal")
        m3.metric("Wrong Answers", f"{incorrect_count} (-{round(incorrect_count*0.33, 2)} marks)", delta_color="inverse")
        m4.metric("Unattempted", f"{unattempted_count}")

        if st.button("🔄 Take Another Mock Test", type="primary"):
            st.session_state.mock_test_started = False
            st.session_state.mock_submitted = False
            st.session_state.mock_saved_to_db = False
            st.rerun()

        st.divider()
        st.markdown("#### 📝 Question Review")
        for idx, q in enumerate(questions):
            user_ans = st.session_state.mock_answers.get(idx)
            corr = int(q.get("correct", 0))
            opts = [str(q[f"option_{l.lower()}"]) for l in OPTION_LETTERS]

            status_icon = "✅ Correct" if user_ans == corr else ("❌ Incorrect" if user_ans is not None else "⚪ Unattempted")
            with st.expander(f"Q{idx+1}: {q['question'][:75]}... [{status_icon}]"):
                st.markdown(f"**Question:** {q['question']}")
                for i in range(4):
                    prefix = f"{OPTION_LETTERS[i]}. {opts[i]}"
                    if i == corr:
                        st.markdown(f"<span style='color: #10b981; font-weight: bold;'>{prefix} (Correct Answer)</span>", unsafe_allow_html=True)
                    elif i == user_ans:
                        st.markdown(f"<span style='color: #ef4444;'>{prefix} (Your Choice)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color: #94a3b8;'>{prefix}</span>", unsafe_allow_html=True)
        return

    # 2. ACTIVE TEST INTERFACE
    cur_q = questions[current_idx]
    q_opts = [str(cur_q[f"option_{l.lower()}"]) for l in OPTION_LETTERS]

    q_col, pal_col = st.columns([3.2, 1.2], gap="large")

    with q_col:
        t_col, m_col = st.columns([3, 1])
        with t_col:
            st.markdown(f"### Question {current_idx + 1} of {total_q}")
            st.caption(f"Topic: {cur_q.get('topic', 'Mining Engineering')} · Difficulty: Level {cur_q.get('difficulty', 1)}")
        with m_col:
            st.markdown("<div style='text-align: right; color: #10b981; font-weight: bold;'>+1.0 / -0.33</div>", unsafe_allow_html=True)

        st.divider()
        st.markdown(f"<div style='font-size: 1.15rem; line-height: 1.6; margin-bottom: 1.5rem;'>{cur_q['question']}</div>", unsafe_allow_html=True)

        prev_ans = st.session_state.mock_answers.get(current_idx)
        selected_opt = st.radio(
            "Select Answer:",
            options=list(range(4)),
            format_func=lambda i: f"{OPTION_LETTERS[i]}. {q_opts[i]}",
            key=f"mock_opt_{current_idx}",
            index=prev_ans
        )

        st.divider()

        b1, b2, b3, b4 = st.columns([1.5, 1.8, 1.2, 1.2])

        with b1:
            if st.button("💾 Save & Next", type="primary", use_container_width=True):
                if selected_opt is not None:
                    st.session_state.mock_answers[current_idx] = selected_opt
                st.session_state.mock_marked_review.discard(current_idx)
                if current_idx + 1 < total_q:
                    st.session_state.mock_current_idx += 1
                st.rerun()

        with b2:
            if st.button("🟣 Mark for Review", use_container_width=True):
                if selected_opt is not None:
                    st.session_state.mock_answers[current_idx] = selected_opt
                st.session_state.mock_marked_review.add(current_idx)
                if current_idx + 1 < total_q:
                    st.session_state.mock_current_idx += 1
                st.rerun()

        with b3:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.mock_answers.pop(current_idx, None)
                st.session_state.mock_marked_review.discard(current_idx)
                st.rerun()

        with b4:
            if st.button("🚩 Flag", use_container_width=True, help="Report question for review"):
                api_client.flag_question_server(cur_q["id"], "Flagged during mock test")
                st.toast("Question flagged for review!", icon="🚩")

    with pal_col:
        with st.container(border=True):
            st.markdown("#### Question Palette")
            st.markdown("""
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 0.8rem; margin-bottom: 0.75rem;">
                    <div>🟢 Answered</div>
                    <div>🟣 Review</div>
                    <div>⚪ Not Visited</div>
                    <div>▶ Current</div>
                </div>
            """, unsafe_allow_html=True)

            grid_cols = st.columns(5)
            for i in range(total_q):
                col_idx = i % 5
                is_ans = i in st.session_state.mock_answers
                is_rev = i in st.session_state.mock_marked_review
                is_cur = i == current_idx

                btn_label = f"{i+1}"
                if is_rev:
                    btn_label = f"🟣{i+1}"
                elif is_ans:
                    btn_label = f"🟢{i+1}"
                elif is_cur:
                    btn_label = f"▶{i+1}"

                with grid_cols[col_idx]:
                    if st.button(btn_label, key=f"pal_btn_{i}", use_container_width=True):
                        st.session_state.mock_current_idx = i
                        st.rerun()

            st.divider()

            if st.button("🏁 Submit Test", type="primary", use_container_width=True):
                st.session_state.mock_submitted = True
                st.rerun()


# ============================================================
# EXAMGOAL ANALYTICS & PERFORMANCE DASHBOARD
# ============================================================
def render_analytics_dashboard():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #334155;">
            <h2 style="color: #a855f7; margin: 0 0 0.25rem 0; font-size: 1.5rem;">📊 GATEMining Performance & Progress Analytics</h2>
            <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">
                Real-time tracking of your personal progress: topic strengths, mock test scores, and revision priorities.
            </p>
        </div>
    """, unsafe_allow_html=True)

    user = st.session_state.get("user")
    if not user:
        st.info("💡 **Log in or create an account** in the sidebar to track your GATE questions, save mock test history, and view personalized strength analysis!")
        return

    summary = api_client.get_user_summary(user["id"])
    if not summary:
        st.warning("Could not load user analytics. Attempt some questions in Practice or Mock mode first!")
        return

    # 1. KPI Top Bar
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Questions Attempted", summary.get("total_attempted", 0))
    k2.metric("Overall Accuracy", f"{summary.get('accuracy_pct', 0.0)}%")
    k3.metric("Mock Tests Taken", summary.get("mock_tests_taken", 0))
    k4.metric("Best Mock Score", summary.get("best_mock_score", 0.0))

    g1, g2, g3 = st.columns(3)
    _g = api_client.get_gamification(user)
    g1.metric("Miner Rank", f"{_g['rank_icon']} {_g['rank_name']}")
    g2.metric("Total XP", f"{_g['xp']} XP")
    g3.metric("Day Streak", f"🔥 {_g['streak']}")

    st.divider()

    # 2. Topic Strengths & Weaknesses
    c_strong, c_weak = st.columns(2)
    with c_strong:
        with st.container(border=True):
            st.markdown("#### 🌟 Strong Topics (Accuracy ≥ 70%)")
            strong_list = summary.get("strong_topics", [])
            if strong_list:
                for t in strong_list:
                    st.markdown(f"🟢 **{t}**")
            else:
                st.caption("Keep practicing to unlock your strong topic badges!")

    with c_weak:
        with st.container(border=True):
            st.markdown("#### 🎯 Focus & Revision Needed (< 50%)")
            weak_list = summary.get("weak_topics", [])
            if weak_list:
                for t in weak_list:
                    st.markdown(f"🔴 **{t}**")
            else:
                st.caption("No critical weak topics detected! Great job.")

    st.divider()

    # 3. Topic-wise Breakdown Table
    st.markdown("#### 📚 Topic-wise Performance Breakdown")
    breakdown = summary.get("topic_breakdown", [])
    if breakdown:
        b_data = []
        for b in breakdown:
            b_data.append({
                "Topic": b["topic"],
                "Attempted": b["attempted"],
                "Correct": b["correct"],
                "Accuracy (%)": f"{b['accuracy_pct']}%",
            })
        st.dataframe(pd.DataFrame(b_data), use_container_width=True)
    else:
        st.caption("No topic data yet. Solve questions in Practice Mode to see detailed breakdown.")

    st.divider()

    # 4. Recent Test Sessions
    st.markdown("#### ⏱️ Recent Test & Game Sessions")
    sessions = summary.get("recent_sessions", [])
    if sessions:
        s_data = []
        for s in sessions:
            s_data.append({
                "Mode": "Mock Test" if s.get("mode") == "mock_test" else "Millionaire Game",
                "Score": s.get("score"),
                "Total Qs": s.get("total_questions"),
                "Correct": s.get("correct_count"),
                "Wrong": s.get("incorrect_count"),
                "Unattempted": s.get("unattempted_count"),
                "Date": str(s.get("created_at", ""))[:19],
            })
        st.dataframe(pd.DataFrame(s_data), use_container_width=True)
    else:
        st.caption("No mock tests completed yet. Start your first mock test from the sidebar!")

