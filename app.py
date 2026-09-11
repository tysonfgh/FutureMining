from __future__ import annotations

import base64
import json
import html
import io
import math
import os
import random
import re
import struct
import tempfile
import wave
from pathlib import Path
import streamlit.components.v1 as components

import pandas as pd
import streamlit as st
import api_client
import examgoal
import about

try:
    from extra_streamlit_components import CookieManager
    COOKIES_AVAILABLE = True
except ImportError:
    CookieManager = None
    COOKIES_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FutureMining | Knowledge Challenge",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS / CONSTANTS
# ============================================================

DATA_PATH = (
    Path(__file__).parent
    / "data"
    / "GATE_800_Questions_Classified.csv"
)

LEGACY_DATA_PATH = (
    Path(__file__).parent
    / "data"
    / "GATE_800_Questions_Classified.csv"
)

REVIEW_QUEUE_PATH = (
    Path(__file__).parent
    / "data"
    / "review_queue.json"
)

LEVELS = list(range(1, 16))

PRIZES = [
    "₹1,000",
    "₹2,000",
    "₹3,000",
    "₹5,000",
    "₹10,000",
    "₹20,000",
    "₹40,000",
    "₹80,000",
    "₹1,60,000",
    "₹3,20,000",
    "₹6,40,000",
    "₹12,50,000",
    "₹25,00,000",
    "₹50,00,000",
    "₹1,00,00,000",
]

OPTION_LETTERS = ("A", "B", "C", "D")


# ============================================================
# AUDIO
# ============================================================

def make_wav_data(
    sequence: list[tuple[float, float]],
    gain: float = 0.16,
) -> str:
    """Create a brighter, layered in-memory game-show audio cue."""

    sample_rate = 22050
    frames = bytearray()

    for frequency, duration in sequence:
        frame_count = int(sample_rate * duration)

        for index in range(frame_count):
            progress = index / max(1, frame_count - 1)

            attack = min(1.0, progress / 0.045)
            release = min(1.0, (1.0 - progress) / 0.18)
            envelope = attack * release

            time = index / sample_rate

            fundamental = math.sin(
                2 * math.pi * frequency * time
            )

            second_harmonic = math.sin(
                2 * math.pi * frequency * 2 * time
            )

            third_harmonic = math.sin(
                2 * math.pi * frequency * 3 * time
            )

            sample = (
                fundamental
                + (second_harmonic * 0.22)
                + (third_harmonic * 0.08)
            ) / 1.3

            frames.extend(
                struct.pack(
                    "<h",
                    int(32767 * gain * envelope * sample),
                )
            )

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(frames)

    return (
        "data:audio/wav;base64,"
        + base64.b64encode(buffer.getvalue()).decode("ascii")
    )


AUDIO_SOURCES = {
    "lifeline": make_wav_data(
        [
            (440, 0.08),
            (660, 0.09),
            (990, 0.16),
        ]
    ),

    "swap": make_wav_data(
        [
            (392, 0.06),
            (523, 0.06),
            (659, 0.06),
            (784, 0.16),
        ]
    ),

    "correct": make_wav_data(
        [
            (523, 0.08),
            (659, 0.08),
            (784, 0.12),
            (1047, 0.22),
        ]
    ),

    "wrong": make_wav_data(
        [
            (330, 0.10),
            (262, 0.13),
            (196, 0.28),
        ],
        gain=0.15,
    ),

    "victory": make_wav_data(
        [
            (523, 0.08),
            (659, 0.08),
            (784, 0.08),
            (1047, 0.11),
            (1319, 0.28),
        ]
    ),
}


def play_sound(event: str | None) -> None:
    if not event or not st.session_state.get("sound_enabled", True):
        return

    audio_source = AUDIO_SOURCES.get(event)

    if not audio_source:
        return

    components.html(
        f"""
        <html>
        <body style="margin:0;padding:0;background:transparent;">
            <audio autoplay>
                <source src="{audio_source}" type="audio/wav">
            </audio>

            <script>
                const audio = document.querySelector("audio");
                if (audio) {{
                    audio.volume = 0.8;
                    audio.play().catch(() => {{}});
                }}
            </script>
        </body>
        </html>
        """,
        height=1,
        scrolling=False,
    )


# ============================================================
# THEME (dark / light)
# ============================================================

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

IS_LIGHT_THEME = st.session_state.theme == "light"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

        @import url(
            'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500'
            '&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600'
            '&family=Space+Grotesk:wght@400;500;600;700'
            '&display=swap'
        );


        /* ====================================================
           ROOT
        ==================================================== */

        :root {
            --ink: #f7f3eb;
            --muted: #9197a8;
            --quiet: #5f6476;
            --void: #07080d;
            --surface: #0d0d16;
            --surface-raised: #161522;
            --surface-soft: #1b1a2a;

            --blue: #6e62f6;
            --cyan: #78e0c3;

            --gold: #e8ad55;
            --gold-light: #ffe3ae;

            --green: #4cd7a0;
            --red: #ef7187;

            --rule: rgba(168, 160, 206, .19);
        }


        /* IMPORTANT:
           Do NOT use [class*="css"] here.
           It can interfere with Streamlit's internal DOM.
        */

        html,
        body {
            font-family: 'Space Grotesk', sans-serif;
        }


        /* ====================================================
           APP BACKGROUND
        ==================================================== */

        .stApp {
            min-height: 100vh;

            background:
                radial-gradient(
                    ellipse at 68% -16%,
                    rgba(86, 72, 184, .23),
                    transparent 33rem
                ),

                radial-gradient(
                    ellipse at 16% 30%,
                    rgba(40, 35, 97, .18),
                    transparent 30rem
                ),

                linear-gradient(
                    135deg,
                    rgba(255,255,255,.013) 25%,
                    transparent 25%
                ) 0 0 / 7px 7px,

                var(--void);

            color: var(--ink);
        }


        /* ====================================================
           MAIN CONTAINER
        ==================================================== */

        .block-container {
            max-width: 1500px;
            padding: 2.5rem 4.5rem 3.4rem;
        }


        /* ====================================================
           STREAMLIT HEADER
           
           IMPORTANT:
           Keep the native header available because it contains
           the sidebar open/close control.
        ==================================================== */

        header[data-testid="stHeader"],
        [data-testid="stHeader"] {
            background: transparent !important;
            z-index: 999999 !important;
        }


        /* Don't hide the toolbar anymore. */
        [data-testid="stToolbar"] {
            visibility: visible !important;
        }


        /* Decoration can stay hidden. */
        [data-testid="stDecoration"] {
            display: none !important;
        }


        /* ====================================================
           SIDEBAR TOGGLE FIX
           
           These selectors are deliberately explicit.
           This is the main fix for your missing button.
        ==================================================== */

        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;

            position: fixed !important;

            z-index: 2147483647 !important;
        }


        [data-testid="stSidebarCollapsedControl"] button {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;

            position: relative !important;

            z-index: 2147483647 !important;
        }


        [data-testid="stSidebarCollapseButton"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;

            position: relative !important;

            z-index: 2147483647 !important;
        }


        [data-testid="stSidebarCollapseButton"] button {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;

            z-index: 2147483647 !important;
        }


        /* ====================================================
           SIDEBAR
        ==================================================== */

        section[data-testid="stSidebar"] {
            z-index: 999999 !important;

            border-right:
                1px solid rgba(120, 224, 195, .13);

            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(110, 98, 246, .18),
                    transparent 20rem
                ),

                linear-gradient(
                    180deg,
                    #0b0b17 0%,
                    #07080d 72%
                );
        }


        section[data-testid="stSidebar"] > div:first-child {
            padding: 1.25rem 1rem 2rem;
        }


        /* ====================================================
           TOP BAR
        ==================================================== */

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;

            min-height: 58px;
            margin-bottom: 2.1rem;
            padding: 0 0 1.35rem;

            border-bottom: 1px solid var(--rule);

            transition: border-color .25s ease;
        }


        .topbar:hover {
            border-color: rgba(120, 224, 195, .40);
        }


        /* ====================================================
           SIDEBAR BRAND
        ==================================================== */

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: .65rem;

            padding: .2rem .1rem 1rem;

            border-bottom: 1px solid var(--rule);
        }


        .sidebar-brand-mark {
            display: grid;

            width: 33px;
            height: 33px;

            place-items: center;

            border: 1px solid rgba(232, 173, 85, .72);

            border-radius: 10px 10px 10px 3px;

            background:
                linear-gradient(
                    145deg,
                    rgba(110, 98, 246, .45),
                    rgba(9, 12, 25, .9)
                );

            color: var(--gold-light);

            font-family: 'DM Mono', monospace;
            font-size: .65rem;

            transition:
                transform .25s ease,
                box-shadow .25s ease;
        }


        .sidebar-brand:hover .sidebar-brand-mark {
            transform: rotate(-7deg) scale(1.08);

            box-shadow:
                0 0 22px rgba(120, 224, 195, .28);
        }


        .sidebar-brand-name {
            color: var(--ink);

            font-size: .92rem;
            font-weight: 800;

            letter-spacing: -.06em;
        }


        .sidebar-brand-name span {
            color: var(--cyan);
        }


        .sidebar-brand-note {
            margin-top: .16rem;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .52rem;
            letter-spacing: .12em;

            text-transform: uppercase;
        }


        .sidebar-rule {
            height: 1px;

            margin: 1.05rem 0;

            background: var(--rule);
        }


        .sidebar-section-title {
            margin: .72rem 0 .5rem;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .58rem;
            letter-spacing: .14em;

            text-transform: uppercase;
        }


        .lifeline-title {
            margin-top: 1.15rem;
        }


        .mission-title {
            display: flex;
            justify-content: space-between;

            margin: 1.25rem 0 .75rem;

            color: var(--gold);

            font-family: 'DM Mono', monospace;

            font-size: .61rem;
            letter-spacing: .15em;

            text-transform: uppercase;
        }


        .mission-title span {
            color: var(--green);
            letter-spacing: .06em;
        }


        /* ====================================================
           SIDEBAR HUD
        ==================================================== */

        .sidebar-hud {
            padding: .75rem;

            border: 1px solid rgba(110, 98, 246, .25);

            border-radius: 11px;

            background: rgba(18, 17, 38, .72);

            transition:
                transform .22s ease,
                border-color .22s ease,
                box-shadow .22s ease;
        }


        .sidebar-hud:hover {
            border-color: rgba(120, 224, 195, .5);

            box-shadow:
                0 12px 28px rgba(0,0,0,.25);

            transform: translateY(-2px);
        }


        .sidebar-hud-label {
            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .56rem;
            letter-spacing: .13em;

            text-transform: uppercase;
        }


        .sidebar-hud-value {
            margin-top: .2rem;

            color: var(--gold-light);

            font-size: 1.35rem;
            font-weight: 800;

            letter-spacing: -.06em;
        }


        .sidebar-hud-sub {
            margin-top: .18rem;

            color: var(--quiet);

            font-size: .61rem;
        }


        .sidebar-hud .progress-track {
            margin: .55rem 0 .45rem;
        }


        .sidebar-stats {
            display: grid;

            grid-template-columns: 1fr 1fr;

            gap: .45rem;

            margin-top: .55rem;
        }


        .sidebar-stat {
            padding: .55rem .6rem;

            border: 1px solid rgba(168, 160, 206, .12);

            border-radius: 8px;

            background: rgba(8, 10, 20, .56);

            transition:
                background .2s ease,
                border-color .2s ease,
                transform .2s ease;
        }


        .sidebar-stat:hover {
            border-color: rgba(232, 173, 85, .42);

            background: rgba(44, 34, 23, .52);

            transform: translateY(-2px);
        }


        .sidebar-stat-label {
            color: var(--quiet);

            font-family: 'DM Mono', monospace;

            font-size: .5rem;
            letter-spacing: .1em;

            text-transform: uppercase;
        }


        .sidebar-stat-value {
            margin-top: .22rem;

            color: var(--ink);

            font-size: .88rem;
            font-weight: 700;
        }


        /* ====================================================
           DEPTH MAP
        ==================================================== */

        .depth-map {
            display: grid;

            grid-template-columns:
                repeat(15, 1fr);

            gap: 3px;

            margin-top: .58rem;
        }


        .depth-node {
            height: 8px;

            border-radius: 2px;

            background:
                rgba(117, 134, 163, .25);

            transition:
                transform .2s ease,
                background .2s ease,
                box-shadow .2s ease;
        }


        .depth-node:hover {
            background: var(--cyan);

            box-shadow:
                0 0 9px rgba(120, 224, 195, .72);

            transform: scaleY(1.7);
        }


        .depth-node.passed {
            background: var(--cyan);

            box-shadow:
                0 0 6px rgba(120, 224, 195, .28);
        }


        .depth-node.current {
            background: var(--gold);

            box-shadow:
                0 0 9px rgba(232, 173, 85, .75);

            animation:
                depth-pulse 1.6s ease-in-out infinite;
        }


        @keyframes depth-pulse {
            0%, 100% {
                transform: scaleY(1);
            }

            50% {
                transform: scaleY(1.8);
            }
        }


        .depth-labels {
            display: flex;

            justify-content: space-between;

            margin-top: .38rem;

            color: var(--quiet);

            font-family: 'DM Mono', monospace;

            font-size: .5rem;
        }


        /* ====================================================
           SIDEBAR BUTTONS
        ==================================================== */

        section[data-testid="stSidebar"]
        div[data-testid="stButton"]
        button {
            min-height: 2.35rem;

            border-radius: 9px;

            font-size: .68rem;
        }


        section[data-testid="stSidebar"]
        div[data-testid="stButton"]
        button:hover:not(:disabled) {
            border-color: var(--gold-light);

            box-shadow:
                0 8px 18px rgba(232, 173, 85, .20);
        }


        /* ====================================================
           MAIN BRAND
        ==================================================== */

        .brand-lockup {
            display: flex;
            align-items: center;

            gap: .9rem;
        }


        .brand-mark {
            display: grid;

            width: 47px;
            height: 47px;

            place-items: center;

            border:
                1px solid rgba(232, 185, 61, .76);

            border-radius: 14px 14px 14px 4px;

            background:
                linear-gradient(
                    145deg,
                    rgba(50, 104, 220, .48),
                    rgba(7, 16, 39, .88)
                );

            box-shadow:
                5px 5px 0 rgba(232, 185, 61, .13),
                0 0 34px rgba(91, 71, 218, .18);

            color: var(--gold-light);

            font-family: 'DM Mono', monospace;

            font-size: .88rem;
            font-weight: 500;

            letter-spacing: -.13em;
        }


        .brand-name {
            color: var(--ink);

            font-size: clamp(1.35rem, 2.8vw, 2rem);

            font-weight: 800;

            letter-spacing: -.08em;

            line-height: 1;
        }


        .brand-name span {
            color: var(--cyan);
        }


        .brand-note {
            margin-top: .42rem;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .65rem;
            letter-spacing: .14em;

            text-transform: uppercase;
        }


        .live-label {
            display: flex;

            align-items: center;

            gap: .55rem;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .66rem;
            letter-spacing: .12em;

            text-transform: uppercase;
        }


        .live-dot {
            width: 7px;
            height: 7px;

            border-radius: 50%;

            background: var(--green);

            box-shadow:
                0 0 12px var(--green);
        }


        /* ====================================================
           CONTAINERS
        ==================================================== */

        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--rule) !important;

            border-radius: 18px !important;

            background:
                linear-gradient(
                    145deg,
                    rgba(24, 22, 46, .90),
                    rgba(5, 11, 27, .94)
                ) !important;

            box-shadow:
                0 22px 65px rgba(0, 0, 0, .24),
                inset 0 1px 0 rgba(255,255,255,.035);

            transition:
                transform .24s ease,
                border-color .24s ease,
                box-shadow .24s ease;
        }


        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color:
                rgba(120, 224, 195, .34) !important;

            box-shadow:
                0 28px 76px rgba(0, 0, 0, .32),
                0 0 0 1px rgba(120, 224, 195, .04),
                inset 0 1px 0 rgba(255,255,255,.06);

            transform: translateY(-2px);
        }


        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: inherit;
        }


        /* ====================================================
           RAIL / STAGE
        ==================================================== */

        .rail-kicker,
        .stage-kicker {
            color: var(--gold);

            font-family: 'DM Mono', monospace;

            font-size: .63rem;
            letter-spacing: .16em;

            text-transform: uppercase;
        }


        .rail-heading {
            margin-top: .42rem;

            color: var(--ink);

            font-size: 1.1rem;
            font-weight: 800;

            letter-spacing: -.04em;
        }


        .rail-copy {
            margin-top: .48rem;

            color: var(--muted);

            font-size: .76rem;

            line-height: 1.55;
        }


        .balance-card {
            margin: 1.25rem 0;

            padding: 1rem 1.05rem;

            border:
                1px solid rgba(232, 185, 61, .24);

            border-radius: 13px;

            background:
                linear-gradient(
                    135deg,
                    rgba(232, 185, 61, .12),
                    rgba(7, 15, 33, .42)
                );
        }


        .balance-label {
            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .61rem;
            letter-spacing: .14em;

            text-transform: uppercase;
        }


        .balance-value {
            margin-top: .34rem;

            color: var(--gold-light);

            font-size: 1.42rem;
            font-weight: 800;

            letter-spacing: -.05em;
        }


        .balance-note {
            margin-top: .28rem;

            color: var(--quiet);

            font-size: .68rem;
        }


        .rail-rule {
            height: 1px;

            margin: 1.15rem 0;

            background: var(--rule);
        }


        .rail-section-title {
            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .62rem;
            letter-spacing: .15em;

            text-transform: uppercase;
        }


        /* ====================================================
           SAFETY / FLAGS
        ==================================================== */

        .safety-note {
            display: flex;

            gap: .55rem;

            align-items: flex-start;

            margin-top: 1.1rem;

            padding: .68rem .74rem;

            border-left:
                2px solid var(--gold);

            background:
                rgba(232, 185, 61, .06);

            color: var(--muted);

            font-size: .69rem;

            line-height: 1.45;

            transition:
                background .22s ease,
                border-color .22s ease,
                transform .22s ease;
        }


        .safety-note strong {
            color: var(--gold-light);

            font-weight: 700;
        }


        .safety-note:hover {
            border-color: var(--cyan);

            background:
                rgba(120, 224, 195, .08);

            transform: translateX(3px);
        }


        .flag-summary {
            display: flex;

            align-items: center;

            gap: .5rem;

            margin-top: .8rem;

            padding: .58rem .65rem;

            border:
                1px solid rgba(239, 113, 135, .18);

            border-radius: 9px;

            background:
                rgba(239, 113, 135, .055);

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .57rem;

            line-height: 1.4;

            transition:
                transform .22s ease,
                border-color .22s ease,
                background .22s ease;
        }


        .flag-summary:hover {
            border-color:
                rgba(239, 113, 135, .58);

            background:
                rgba(239, 113, 135, .10);

            transform: translateX(3px);
        }


        .flag-summary strong {
            color: #ffb1be;
        }


        .flag-summary-icon {
            color: var(--red);

            font-size: .9rem;
        }


        .flag-status {
            min-height: 2.35rem;

            display: flex;

            align-items: center;

            padding: 0 .7rem;

            border:
                1px solid rgba(168, 160, 206, .13);

            border-radius: 9px;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .57rem;

            line-height: 1.4;

            transition:
                border-color .22s ease,
                color .22s ease,
                background .22s ease;
        }


        .flag-status:hover {
            border-color:
                rgba(239, 113, 135, .42);

            background:
                rgba(239, 113, 135, .06);

            color: #ffb1be;
        }


        /* ====================================================
           STAGE
        ==================================================== */

        .stage-panel {
            position: relative;

            overflow: hidden;

            border-color:
                rgba(232, 185, 61, .27) !important;
        }


        .stage-panel::before {
            position: absolute;

            top: 0;
            right: 13%;
            left: 13%;

            height: 2px;

            background:
                linear-gradient(
                    90deg,
                    transparent,
                    var(--gold),
                    transparent
                );

            content: "";

            opacity: .8;
        }


        .stage-header {
            display: flex;

            align-items: flex-start;

            justify-content: space-between;

            gap: 1rem;

            margin-bottom: 1.15rem;
        }


        .stage-title {
            margin-top: .38rem;

            color: var(--ink);

            font-size: 1.28rem;
            font-weight: 800;

            letter-spacing: -.055em;
        }


        .stage-meta {
            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .67rem;

            letter-spacing: .08em;

            text-align: right;

            text-transform: uppercase;
        }


        .stage-meta strong {
            color: var(--cyan);

            font-weight: 500;
        }


        .progress-track {
            height: 3px;

            margin: .8rem 0 1.5rem;

            overflow: hidden;

            border-radius: 999px;

            background:
                rgba(255,255,255,.07);
        }


        .progress-fill {
            height: 100%;

            border-radius: inherit;

            background:
                linear-gradient(
                    90deg,
                    var(--gold),
                    var(--gold-light)
                );

            box-shadow:
                0 0 15px rgba(232, 185, 61, .56);
        }


        /* ====================================================
           QUESTION
        ==================================================== */

        .question-card {
            position: relative;

            margin: .7rem 0 1.45rem;

            padding: 1.55rem 1.65rem 1.65rem;

            border:
                1px solid rgba(110, 98, 246, .34);

            border-radius: 14px;

            background:
                linear-gradient(
                    145deg,
                    rgba(19, 35, 72, .68),
                    rgba(3, 10, 25, .74)
                ),

                radial-gradient(
                    circle at 92% 0%,
                    rgba(110, 98, 246, .18),
                    transparent 17rem
                );

            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.04);
        }


        .question-card::after {
            position: absolute;

            top: 15px;
            right: 15px;

            width: 7px;
            height: 7px;

            border-top:
                1px solid var(--gold);

            border-right:
                1px solid var(--gold);

            content: "";

            opacity: .75;
        }


        div[data-testid="stVerticalBlockBorderWrapper"]:has(
            .question-card-marker
        ) {
            border-color:
                rgba(110, 98, 246, .42) !important;

            background:
                linear-gradient(
                    145deg,
                    rgba(25, 28, 59, .82),
                    rgba(8, 10, 23, .88)
                ),

                radial-gradient(
                    circle at 92% 0%,
                    rgba(110, 98, 246, .18),
                    transparent 17rem
                ) !important;

            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.04),
                0 18px 42px rgba(0,0,0,.18);
        }


        .question-card-marker {
            display: none;
        }


        div[data-testid="stVerticalBlockBorderWrapper"]:has(
            .question-card-marker
        )
        [data-testid="stMarkdownContainer"] p {
            margin: .62rem 0 .05rem;

            color: var(--ink);

            font-family: 'Newsreader', Georgia, serif;

            font-size: clamp(1.15rem, 1.8vw, 1.58rem);

            font-weight: 500;

            letter-spacing: -.02em;

            line-height: 1.48;
        }


        .question-kicker {
            color: var(--gold-light);

            font-family: 'DM Mono', monospace;

            font-size: .63rem;
            letter-spacing: .12em;

            text-transform: uppercase;
        }


        .question-text {
            margin-top: .7rem;

            color: var(--ink);

            font-size: clamp(1.08rem, 1.75vw, 1.5rem);

            font-weight: 700;

            letter-spacing: -.035em;

            line-height: 1.5;
        }


        .answer-label {
            margin: 0 0 .7rem .1rem;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .62rem;
            letter-spacing: .15em;

            text-transform: uppercase;
        }


        /* ====================================================
           RESULTS
        ==================================================== */

        .result-box {
            margin-top: 1rem;

            padding: .95rem 1.05rem;

            border: 1px solid;

            border-radius: 12px;

            font-size: .82rem;

            line-height: 1.55;
        }


        .result-box.good {
            border-color:
                rgba(66, 214, 148, .45);

            background:
                rgba(66, 214, 148, .08);
        }


        .result-box.bad {
            border-color:
                rgba(240, 106, 125, .45);

            background:
                rgba(240, 106, 125, .08);
        }


        .result-title {
            margin-bottom: .2rem;

            font-weight: 800;
        }


        .good .result-title {
            color: var(--green);
        }


        .bad .result-title {
            color: var(--red);
        }


        .result-detail {
            color: #c5d0e3;
        }


        /* ====================================================
           ANSWER REVIEW
        ==================================================== */

        .answer-review {
            display: grid;

            grid-template-columns:
                repeat(2, minmax(0, 1fr));

            gap: .75rem;
        }


        .answer-review-choice {
            display: flex;

            align-items: center;

            gap: .65rem;

            min-height: 3.25rem;

            padding: .68rem .8rem;

            border:
                1px solid rgba(104, 143, 207, .20);

            border-radius: 11px;

            background:
                rgba(9, 20, 47, .60);

            color: #b8c8e2;

            font-size: .79rem;

            line-height: 1.38;
        }


        .answer-review-choice.correct {
            border-color:
                rgba(66, 214, 148, .82);

            background:
                linear-gradient(
                    110deg,
                    rgba(28, 128, 91, .42),
                    rgba(14, 68, 59, .55)
                );

            color: #eafff4;

            box-shadow:
                0 0 22px rgba(66, 214, 148, .13);
        }


        .answer-review-choice.wrong {
            border-color:
                rgba(240, 106, 125, .86);

            background:
                linear-gradient(
                    110deg,
                    rgba(141, 38, 61, .48),
                    rgba(67, 21, 42, .58)
                );

            color: #fff0f2;

            box-shadow:
                0 0 22px rgba(240, 106, 125, .12);
        }


        .answer-review-choice.muted {
            opacity: .45;
        }


        .answer-review-badge {
            display: grid;

            flex: 0 0 26px;

            width: 26px;
            height: 26px;

            place-items: center;

            border:
                1px solid currentColor;

            border-radius: 50%;

            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .65rem;
        }


        .correct .answer-review-badge {
            color: var(--green);
        }


        .wrong .answer-review-badge {
            color: var(--red);
        }


        .answer-review-mark {
            margin-left: auto;

            color: currentColor;

            font-family: 'DM Mono', monospace;

            font-size: .61rem;
            font-weight: 700;

            white-space: nowrap;
        }


        /* ====================================================
           LADDER
        ==================================================== */

        .ladder-heading {
            display: flex;

            align-items: baseline;

            justify-content: space-between;

            padding-bottom: .85rem;

            border-bottom: 1px solid var(--rule);
        }


        .ladder-title {
            color: var(--ink);

            font-size: .91rem;
            font-weight: 800;

            letter-spacing: .05em;

            text-transform: uppercase;
        }


        .ladder-caption {
            color: var(--muted);

            font-family: 'DM Mono', monospace;

            font-size: .61rem;
        }


        .ladder-item {
            display: flex;

            align-items: center;

            gap: .45rem;

            margin: .14rem 0;

            padding: .38rem .48rem;

            border-radius: 8px;

            color: #7586a3;

            font-family: 'DM Mono', monospace;

            font-size: .71rem;

            transition:
                background .2s ease,
                color .2s ease,
                transform .2s ease,
                box-shadow .2s ease;
        }


        .ladder-item:hover:not(.current) {
            background:
                rgba(120, 224, 195, .07);

            box-shadow:
                inset 2px 0 0 var(--cyan);

            transform: translateX(3px);
        }


        .ladder-item .level {
            width: 28px;

            color: #536480;

            font-size: .63rem;
        }


        .ladder-item .prize {
            margin-left: auto;
        }


        .ladder-item.safe {
            color: #d6e2f4;
        }


        .ladder-item.safe .level,
        .ladder-item.safe .prize {
            color: var(--gold);
        }


        .ladder-item.passed {
            color:
                rgba(120, 224, 195, .76);
        }


        .ladder-item.passed .level,
        .ladder-item.passed .prize {
            color: var(--cyan);
        }


        .ladder-item.current {
            color: #111a2d;

            background:
                linear-gradient(
                    90deg,
                    var(--gold),
                    var(--gold-light)
                );

            box-shadow:
                0 7px 22px rgba(232, 185, 61, .19);

            font-weight: 800;

            animation:
                current-level-pulse
                2.6s ease-in-out infinite;
        }


        .ladder-item.current .level,
        .ladder-item.current .prize {
            color: #111a2d;
        }


        .safety-line {
            height: 1px;

            margin: .42rem .48rem;

            background:
                rgba(232, 185, 61, .22);
        }


        .toolkit-card {
            margin-top: 1rem;

            padding-top: 1rem;

            border-top:
                1px solid var(--rule);
        }


        .toolkit-title {
            color: var(--cyan);

            font-family: 'DM Mono', monospace;

            font-size: .61rem;
            letter-spacing: .15em;

            text-transform: uppercase;
        }


        .toolkit-copy {
            margin-top: .45rem;

            color: var(--muted);

            font-size: .71rem;

            line-height: 1.5;
        }


        @keyframes current-level-pulse {
            0%, 100% {
                box-shadow:
                    0 7px 22px
                    rgba(232, 185, 61, .17);
            }

            50% {
                box-shadow:
                    0 7px 30px
                    rgba(232, 185, 61, .38);
            }
        }


        /* ====================================================
           BUTTONS
        ==================================================== */

        div[data-testid="stButton"] button {
            position: relative;

            overflow: hidden;

            min-height: 2.55rem;

            border:
                1px solid rgba(103, 150, 226, .32);

            border-radius: 10px;

            background:
                rgba(17, 35, 72, .72) !important;

            color: #dbe8ff !important;

            font-family:
                'Space Grotesk',
                sans-serif;

            font-size: .75rem;

            font-weight: 700;

            transition:
                all .18s ease;
        }


        div[data-testid="stButton"] button::after {
            position: absolute;

            top: 0;
            bottom: 0;
            left: -55%;

            width: 28%;

            background:
                linear-gradient(
                    105deg,
                    transparent,
                    rgba(255,255,255,.27),
                    transparent
                );

            content: "";

            transform: skewX(-18deg);

            transition:
                left .5s ease;
        }


        div[data-testid="stButton"] button:hover:not(:disabled) {
            border-color: var(--cyan);

            background:
                rgba(31, 65, 117, .82) !important;

            color: white !important;

            transform: translateY(-2px);

            box-shadow:
                0 9px 22px
                rgba(53, 107, 194, .22);
        }


        div[data-testid="stButton"] button:hover:not(:disabled)::after {
            left: 125%;
        }


        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
        [data-testid="stBaseButton-primary"] {
            border: 0;

            background:
                linear-gradient(
                    105deg,
                    var(--gold),
                    var(--gold-light)
                ) !important;

            color: #111a2d !important;

            box-shadow:
                0 9px 24px
                rgba(232, 185, 61, .17);
        }


        div[data-testid="stButton"] button:disabled {
            border-color:
                rgba(103, 150, 226, .16) !important;

            background:
                rgba(15, 27, 55, .55) !important;

            color: #667897 !important;

            opacity: .72;
        }

        /* Button labels live on inner spans with their own theme
           color, so paint the spans directly. */

        div[data-testid="stButton"] button span {
            color: #dbe8ff;
        }

        div[data-testid="stButton"] button[kind="primary"] span,
        div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] span,
        [data-testid="stBaseButton-primary"] span {
            color: #111a2d;
        }

        div[data-testid="stButton"] button:disabled span {
            color: #667897;
        }


        /* Sliding theme toggle (single pill button) */

        div[data-testid="stButton"] button[kind="tertiary"],
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] {
            position: relative;

            min-width: 100%;
            width: 100%;

            min-height: 32px;
            height: 32px;

            padding: 0;

            border: 0;

            border-radius: 999px;

            background: transparent !important;

            color: transparent !important;

            font-size: 0;

            box-shadow: none;

            cursor: pointer;
        }

        div[data-testid="stButton"] button[kind="tertiary"]:hover:not(:disabled),
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]:hover:not(:disabled) {
            border: 0;

            background: transparent !important;

            box-shadow: none;

            transform: none;
        }


        /* Hide the text label inside the toggle
           (Streamlit styles the label span directly,
           so the button's own color/font-size can't hide it) */

        div[data-testid="stButton"] button[kind="tertiary"] *,
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] * {
            display: none !important;
        }


        /* Toggle track */

        div[data-testid="stButton"] button[kind="tertiary"]::before,
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]::before {
            position: absolute;

            top: 50%;
            right: 0;

            width: 64px;
            height: 32px;

            border: 1px solid var(--rule);

            border-radius: 999px;

            background: rgba(18, 17, 38, .85);

            content: "";

            transform: translateY(-50%);

            transition:
                border-color .2s ease,
                background .2s ease,
                box-shadow .2s ease;
        }

        div[data-testid="stButton"] button[kind="tertiary"]:hover:not(:disabled)::before,
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]:hover:not(:disabled)::before {
            border-color: var(--cyan);

            box-shadow:
                0 0 16px rgba(120, 224, 195, .25);
        }


        /* Toggle knob — moon, slid right in dark mode */

        div[data-testid="stButton"] button[kind="tertiary"]::after,
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]::after {
            position: absolute;

            top: 50%;
            right: 4px;
            bottom: auto;
            left: auto;

            display: grid;

            place-items: center;

            width: 24px;
            height: 24px;

            border-radius: 50%;

            background: #f5ead6;

            box-shadow:
                0 2px 8px rgba(0, 0, 0, .35);

            color: #33302b;

            font-size: .85rem;

            line-height: 1;

            content: "🌙";

            transform: translateY(-50%);

            transition:
                right .25s ease,
                background .25s ease;
        }

        div[data-testid="stButton"] button[kind="tertiary"]:hover:not(:disabled)::after,
        div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]:hover:not(:disabled)::after {
            right: 4px;
            left: auto;
        }


        /* Top bar rule (brand left, toggle right) */

        .topbar-rule {
            height: 1px;

            margin: 1rem 0 2.1rem;

            background: var(--rule);

            transition: background .25s ease;
        }

        .topbar-rule:hover {
            background: rgba(120, 224, 195, .40);
        }


        /* ====================================================
           RADIO
        ==================================================== */

        div[data-testid="stRadio"]
        div[role="radiogroup"] {
            display: grid;

            grid-template-columns:
                repeat(2, minmax(0, 1fr));

            gap: .75rem;
        }


        div[data-testid="stRadio"]
        div[role="radiogroup"]
        label {
            display: flex;

            min-height: 3.15rem;

            align-items: center;

            padding: .7rem .82rem;

            border:
                1px solid rgba(104, 143, 207, .21);

            border-radius: 11px;

            background:
                rgba(9, 20, 47, .60);

            transition:
                all .18s ease;
        }


        div[data-testid="stRadio"]
        div[role="radiogroup"]
        label:hover {
            border-color:
                rgba(120, 224, 195, .72);

            background:
                rgba(23, 49, 92, .75);

            box-shadow:
                0 8px 18px
                rgba(25, 61, 114, .22);

            transform: translateY(-2px);
        }


        div[data-testid="stRadio"]
        div[role="radiogroup"]
        label:has(input:checked) {
            border-color: var(--gold);

            background:
                linear-gradient(
                    110deg,
                    rgba(84, 64, 29, .62),
                    rgba(38, 31, 22, .78)
                );

            box-shadow:
                0 0 0 1px
                rgba(232, 173, 85, .18),

                0 10px 24px
                rgba(232, 173, 85, .12);

            transform: translateY(-2px);
        }


        div[data-testid="stRadio"]
        div[role="radiogroup"]
        label p,

        div[data-testid="stRadio"]
        div[role="radiogroup"]
        label span,

        div[data-testid="stRadio"]
        div[role="radiogroup"]
        label div {
            color: #d6e2f6 !important;

            font-size: .8rem;

            line-height: 1.4;
        }


        div[data-testid="stRadio"]
        [data-testid="stMarkdownContainer"] p {
            margin-bottom: 0;
        }


        /* ====================================================
           ALERTS
        ==================================================== */

        .stAlert {
            border-radius: 10px;
        }


        /* ====================================================
           RESPONSIVE
        ==================================================== */

        @media (max-width: 1100px) {

            .block-container {
                padding:
                    2rem 2rem 3rem;
            }
        }


        @media (max-width: 900px) {

            .block-container {
                padding:
                    1.2rem 1rem 2rem;
            }


            .topbar {
                align-items: flex-start;

                margin-bottom: 1.4rem;
            }


            .live-label {
                display: none;
            }


            div[data-testid="stRadio"]
            div[role="radiogroup"],

            .answer-review {
                grid-template-columns: 1fr;
            }
        }


        @media (max-width: 560px) {

            .brand-note {
                font-size: .56rem;
                letter-spacing: .08em;
            }


            .brand-name {
                font-size: 1.35rem;
            }


            .question-card {
                padding: 1.1rem;
            }


            .stage-header {
                display: block;
            }


            .stage-meta {
                margin-top: .55rem;

                text-align: left;
            }
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LIGHT MODE — cream + maroon + gold (reference screenshot)
# Override layer only — dark CSS above untouched.
# ============================================================

if IS_LIGHT_THEME:
    st.markdown(
        """
        <style>

            /* ====================================================
               LIGHT PALETTE
            ==================================================== */

            :root {
                --ink: #33302b;
                --muted: #776c62;
                --quiet: #a89c90;
                --void: #f3eee3;
                --surface: #fffdf7;
                --surface-raised: #fffdf7;
                --surface-soft: #ece4d3;

                --blue: #4f46e5;
                --cyan: #9a6b1e;

                --gold: #a8741f;
                --gold-light: #7a4f12;

                --green: #1e7f56;
                --red: #c23a5a;

                --rule: rgba(107, 31, 54, .14);
            }


            /* ====================================================
               APP BACKGROUND (warm cream)
            ==================================================== */

            .stApp {
                background:
                    radial-gradient(
                        ellipse at 68% -16%,
                        rgba(166, 116, 31, .10),
                        transparent 33rem
                    ),

                    radial-gradient(
                        ellipse at 16% 30%,
                        rgba(109, 31, 55, .07),
                        transparent 30rem
                    ),

                    linear-gradient(
                        135deg,
                        rgba(107,31,54,.030) 25%,
                        transparent 25%
                    ) 0 0 / 7px 7px,

                    var(--void);
            }


            /* ====================================================
               TOP BAR / BRAND
            ==================================================== */

            .topbar:hover {
                border-color: rgba(168, 116, 31, .45);
            }

            .brand-mark {
                border-color: rgba(150, 110, 60, .55);

                background:
                    linear-gradient(
                        145deg,
                        #f7ecd9,
                        #e8d3ae
                    );

                box-shadow:
                    5px 5px 0 rgba(168, 116, 31, .14),
                    0 0 24px rgba(166, 116, 31, .12);

                color: #6d1f37;
            }


            /* ====================================================
               CARDS / CONTAINERS
            ==================================================== */

            [data-testid="stVerticalBlockBorderWrapper"] {
                background:
                    linear-gradient(
                        145deg,
                        #fffdf7,
                        #faf5ea
                    ) !important;

                box-shadow:
                    0 18px 45px rgba(107, 31, 54, .08),
                    inset 0 1px 0 rgba(255,255,255,.7);
            }

            [data-testid="stVerticalBlockBorderWrapper"]:hover {
                border-color:
                    rgba(168, 116, 31, .35) !important;

                box-shadow:
                    0 24px 55px rgba(107, 31, 54, .12),
                    0 0 0 1px rgba(168, 116, 31, .06),
                    inset 0 1px 0 rgba(255,255,255,.7);
            }


            /* ====================================================
               RAIL CARDS
            ==================================================== */

            .balance-card {
                border-color: rgba(168, 116, 31, .32);
                background:
                    linear-gradient(
                        135deg,
                        rgba(232, 185, 61, .18),
                        rgba(255, 255, 255, .65)
                    );
            }


            /* ====================================================
               STAGE + PROGRESS + QUESTION
            ==================================================== */

            .stage-panel {
                border-color:
                    rgba(168, 116, 31, .38) !important;
            }

            .progress-track {
                background: rgba(107, 31, 54, .12);
            }

            .progress-fill {
                background:
                    linear-gradient(
                        90deg,
                        #7a2440,
                        #a8506a
                    );

                box-shadow:
                    0 0 12px rgba(122, 36, 64, .35);
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(
                .question-card-marker
            ) {
                border-color:
                    rgba(168, 116, 31, .32) !important;

                background:
                    linear-gradient(
                        145deg,
                        #f9f0de,
                        #fdf8ec
                    ) !important;

                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,.7),
                    0 18px 42px rgba(107,31,54,.08);
            }


            /* ====================================================
               FLAG
            ==================================================== */

            .flag-status {
                border-color: rgba(107, 31, 54, .18);
            }

            .flag-status:hover {
                border-color: rgba(194, 58, 90, .45);
                background: rgba(194, 58, 90, .06);
                color: #9c2b47;
            }


            /* ====================================================
               RESULTS
            ==================================================== */

            .result-box.good {
                border-color: rgba(30, 127, 86, .40);
                background: rgba(30, 127, 86, .08);
            }

            .result-box.bad {
                border-color: rgba(194, 58, 90, .35);
                background: rgba(194, 58, 90, .07);
            }

            .result-detail {
                color: #4a4239;
            }


            /* ====================================================
               ANSWER REVIEW
            ==================================================== */

            .answer-review-choice {
                border-color: rgba(107, 31, 54, .20);
                background: #fbf8f0;
                color: #4a4239;
            }

            .answer-review-choice.correct {
                border-color: rgba(30, 127, 86, .65);
                background:
                    linear-gradient(
                        110deg,
                        rgba(30, 127, 86, .14),
                        rgba(30, 127, 86, .07)
                    );
                color: #0d4f36;
                box-shadow: 0 0 18px rgba(30, 127, 86, .10);
            }

            .answer-review-choice.wrong {
                border-color: rgba(194, 58, 90, .65);
                background:
                    linear-gradient(
                        110deg,
                        rgba(194, 58, 90, .12),
                        rgba(194, 58, 90, .06)
                    );
                color: #7a1f3a;
                box-shadow: 0 0 18px rgba(194, 58, 90, .10);
            }


            /* ====================================================
               LADDER
            ==================================================== */

            .ladder-item {
                color: #6b5f55;
            }

            .ladder-item:hover:not(.current) {
                background: rgba(168, 116, 31, .08);
                box-shadow: inset 2px 0 0 var(--gold);
            }

            .ladder-item .level {
                color: #a89c90;
            }

            .ladder-item.passed {
                color: #9a6b1e;
            }

            .ladder-item.passed .level,
            .ladder-item.passed .prize {
                color: var(--cyan);
            }

            .ladder-item.safe {
                color: #33302b;
            }

            .ladder-item.safe .level,
            .ladder-item.safe .prize {
                color: #7a2440;
            }

            .ladder-item.current {
                color: #fff5e6;

                background:
                    linear-gradient(
                        90deg,
                        #7a2440,
                        #5c1a30
                    );

                box-shadow:
                    0 7px 22px rgba(109, 31, 55, .28);
            }

            .ladder-item.current .level,
            .ladder-item.current .prize {
                color: #ffe9c4;
            }

            .safety-line {
                background: rgba(168, 116, 31, .30);
            }


            /* ====================================================
               MAIN BUTTONS
            ==================================================== */

            div[data-testid="stButton"] button {
                border-color: rgba(107, 31, 54, .28);
                background: #fffdf7 !important;
                color: #6d1f37 !important;
            }

            div[data-testid="stButton"] button:hover:not(:disabled) {
                border-color: var(--gold);
                background: #ffffff !important;
                color: #3d1220 !important;
                box-shadow: 0 9px 22px rgba(107, 31, 54, .12);
            }

            div[data-testid="stButton"] button[kind="primary"],
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
            [data-testid="stBaseButton-primary"] {
                border: 0;

                background:
                    linear-gradient(
                        180deg,
                        #7a2440,
                        #5c1a30
                    ) !important;

                color: #fff5e6 !important;

                box-shadow:
                    0 9px 24px rgba(109, 31, 55, .22);
            }

            div[data-testid="stButton"] button[kind="primary"]:hover:not(:disabled),
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover:not(:disabled) {
                background:
                    linear-gradient(
                        180deg,
                        #8a2a48,
                        #6d1f37
                    ) !important;

                color: #ffffff !important;

                box-shadow:
                    0 12px 28px rgba(109, 31, 55, .30);
            }

            /* Disabled last so it beats primary on ties. */

            div[data-testid="stButton"] button:disabled {
                border-color:
                    rgba(107, 31, 54, .12) !important;

                background: #e8d4dc !important;

                color: #9c7a86 !important;
            }

            /* Streamlit paints button labels on inner spans with
               their own theme color, so paint the spans directly. */

            div[data-testid="stButton"] button span {
                color: #6d1f37 !important;
            }

            div[data-testid="stButton"] button[kind="primary"] span,
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] span {
                color: #ffffff !important;
            }

            div[data-testid="stButton"] button:disabled span {
                color: #9c7a86 !important;
            }


            /* ====================================================
               MAIN RADIO OPTIONS
            ==================================================== */

            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label {
                border-color: rgba(107, 31, 54, .20);
                background: #fffdf7;
            }

            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label:hover {
                border-color: rgba(168, 116, 31, .60);
                background: #ffffff;
                box-shadow: 0 8px 18px rgba(107, 31, 54, .08);
            }

            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label:has(input:checked) {
                border-color: var(--gold);
                background:
                    linear-gradient(
                        110deg,
                        rgba(232, 185, 61, .22),
                        rgba(255, 248, 230, .90)
                    );
                box-shadow:
                    0 0 0 1px rgba(168, 116, 31, .18),
                    0 10px 24px rgba(168, 116, 31, .12);
            }

            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label p,

            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label span,

            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label div {
                color: #33302b !important;
            }


            /* ====================================================
               NATIVE STREAMLIT TEXT + WIDGETS (base theme is dark)
            ==================================================== */

            .stApp [data-testid="stMarkdownContainer"] p,
            .stApp [data-testid="stMarkdownContainer"] h1,
            .stApp [data-testid="stMarkdownContainer"] h2,
            .stApp [data-testid="stMarkdownContainer"] h3,
            .stApp [data-testid="stMarkdownContainer"] h4,
            .stApp [data-testid="stMarkdownContainer"] li {
                color: #33302b;
            }

            .stApp [data-testid="stWidgetLabel"] p {
                color: #33302b !important;
            }

            .stApp [data-testid="stCaptionContainer"] {
                color: #776c62 !important;
            }

            .stApp [data-testid="stDivider"] {
                border-color:
                    rgba(107, 31, 54, .14) !important;
            }

            .stApp [data-testid="stExpander"] {
                background: #fffdf7 !important;
                border-color:
                    rgba(107, 31, 54, .14) !important;
            }

            /* Main expander headers paint via the global markdown
               rules (Streamlit renders them as markdown). */

            .stApp [data-testid="stTabs"] button p {
                color: #776c62 !important;
            }

            .stApp [data-testid="stTabs"] button[aria-selected="true"] p {
                color: #33302b !important;
            }

            .stApp [data-testid="stTextInput"] input {
                background: #fffdf7 !important;
                color: #33302b !important;
                -webkit-text-fill-color: #33302b !important;
            }

            .stApp [data-testid="stTextInput"] div[data-baseweb="input"],
            .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
                background: #fffdf7 !important;
                border-color:
                    rgba(107, 31, 54, .22) !important;
                color: #33302b !important;
            }

            .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] div {
                color: #33302b !important;
            }

            .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] input {
                color: #33302b !important;
                -webkit-text-fill-color: #33302b !important;
            }

            .stApp [data-testid="stTextInput"] svg,
            .stApp [data-testid="stSelectbox"] svg {
                fill: #776c62 !important;
                color: #776c62 !important;
            }

            .stApp [data-testid="stDataFrame"] {
                background: #fffdf7;
                border: 1px solid rgba(107, 31, 54, .14);
                border-radius: 12px;
            }

            .stApp [data-testid="stMetric"] {
                background: #fffdf7 !important;
                border:
                    1px solid rgba(107, 31, 54, .14) !important;
                border-radius: 12px;
            }

            .stApp [data-testid="stMetricValue"] {
                color: #33302b !important;
            }

            .stApp [data-testid="stMetric"] label p {
                color: #776c62 !important;
            }


            /* ====================================================
               HEADER CHROME
            ==================================================== */

            [data-testid="stHeader"] button {
                color: #4a1425 !important;
            }


            /* ====================================================
               SIDEBAR — deep maroon + cream + gold
               (scoped last so it wins every tie)
            ==================================================== */

            section[data-testid="stSidebar"] {
                border-right: 1px solid #38101d;

                background:
                    radial-gradient(
                        circle at 50% 0%,
                        rgba(232, 200, 122, .16),
                        transparent 20rem
                    ),

                    linear-gradient(
                        180deg,
                        #6d1f37 0%,
                        #521627 60%,
                        #431020 100%
                    );
            }


            section[data-testid="stSidebar"]
            .sidebar-brand-mark {
                border-color: rgba(240, 208, 137, .8);

                background:
                    linear-gradient(
                        145deg,
                        #f0d089,
                        #c99a4a
                    );

                color: #4a1425;
            }

            section[data-testid="stSidebar"]
            .sidebar-brand-name {
                color: #f5ead6;
            }

            section[data-testid="stSidebar"]
            .sidebar-brand-name span {
                color: #e8c87a;
            }

            section[data-testid="stSidebar"]
            .sidebar-brand-note,
            section[data-testid="stSidebar"]
            .sidebar-section-title {
                color: #cfae8d;
            }

            section[data-testid="stSidebar"]
            .sidebar-rule {
                background: rgba(232, 200, 122, .20);
            }

            section[data-testid="stSidebar"]
            .mission-title {
                color: #d9b36a;
            }

            section[data-testid="stSidebar"]
            .mission-title span {
                color: #7de0a8;
            }


            section[data-testid="stSidebar"]
            .sidebar-hud {
                border-color: rgba(232, 200, 122, .30);
                background: rgba(40, 8, 18, .45);
            }

            section[data-testid="stSidebar"]
            .sidebar-hud:hover {
                border-color: rgba(240, 208, 137, .55);
                box-shadow: 0 12px 28px rgba(0, 0, 0, .30);
            }

            section[data-testid="stSidebar"]
            .sidebar-hud-label {
                color: #cfae8d;
            }

            section[data-testid="stSidebar"]
            .sidebar-hud-value {
                color: #f7ecd9;
            }

            section[data-testid="stSidebar"]
            .sidebar-hud-sub {
                color: #b99a86;
            }


            section[data-testid="stSidebar"]
            .sidebar-stat {
                border-color: rgba(232, 200, 122, .16);
                background: rgba(40, 8, 18, .40);
            }

            section[data-testid="stSidebar"]
            .sidebar-stat:hover {
                border-color: rgba(232, 200, 122, .50);
                background: rgba(40, 8, 18, .55);
            }

            section[data-testid="stSidebar"]
            .sidebar-stat-label {
                color: #b99a86;
            }

            section[data-testid="stSidebar"]
            .sidebar-stat-value {
                color: #f3e6d3;
            }


            section[data-testid="stSidebar"]
            .depth-node {
                background: rgba(232, 200, 122, .25);
            }

            section[data-testid="stSidebar"]
            .depth-node:hover {
                background: #e8c87a;
                box-shadow: 0 0 9px rgba(232, 200, 122, .72);
            }

            section[data-testid="stSidebar"]
            .depth-node.passed {
                background: #d9a94f;
                box-shadow: 0 0 6px rgba(217, 169, 79, .35);
            }

            section[data-testid="stSidebar"]
            .depth-node.current {
                background: #f0c778;
                box-shadow: 0 0 9px rgba(240, 199, 120, .75);
            }

            section[data-testid="stSidebar"]
            .depth-labels {
                color: #b99a86;
            }


            section[data-testid="stSidebar"]
            .safety-note {
                border-left-color: #d9a94f;
                background: rgba(232, 200, 122, .10);
                color: #e6d3bd;
            }

            section[data-testid="stSidebar"]
            .safety-note strong {
                color: #f7ecd9;
            }

            section[data-testid="stSidebar"]
            .safety-note:hover {
                border-color: #f0c778;
                background: rgba(232, 200, 122, .14);
            }


            section[data-testid="stSidebar"]
            .flag-summary {
                border-color: rgba(232, 200, 122, .20);
                background: rgba(40, 8, 18, .40);
                color: #e6d3bd;
            }

            section[data-testid="stSidebar"]
            .flag-summary:hover {
                border-color: rgba(240, 168, 184, .55);
                background: rgba(40, 8, 18, .55);
            }

            section[data-testid="stSidebar"]
            .flag-summary strong {
                color: #f0d089;
            }

            section[data-testid="stSidebar"]
            .flag-summary-icon {
                color: #f0a8b8;
            }


            /* Sidebar buttons: gold secondary, deep-maroon primary */

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button {
                border-color: rgba(240, 208, 137, .60);

                background:
                    linear-gradient(
                        180deg,
                        #e3b96f,
                        #d2a04e
                    ) !important;

                color: #3d1220 !important;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button:hover:not(:disabled) {
                border-color: #f0d089;

                background:
                    linear-gradient(
                        180deg,
                        #eec987,
                        #d9a94f
                    ) !important;

                color: #3d1220 !important;

                box-shadow:
                    0 8px 18px rgba(217, 169, 79, .30);
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[kind="primary"],
            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[data-testid="stBaseButton-primary"] {
                border:
                    1px solid rgba(232, 200, 122, .45);

                background:
                    rgba(40, 8, 18, .60) !important;

                color: #f5ead6 !important;

                box-shadow: none;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[kind="primary"]:hover:not(:disabled),
            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[data-testid="stBaseButton-primary"]:hover:not(:disabled) {
                border-color: #f0d089;

                background:
                    rgba(40, 8, 18, .80) !important;

                color: #fff5e6 !important;

                box-shadow:
                    0 8px 18px rgba(0, 0, 0, .35);
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button:disabled {
                border-color:
                    rgba(232, 200, 122, .20) !important;

                background:
                    rgba(40, 8, 18, .35) !important;

                color: #a9856f !important;
            }

            /* Sidebar button labels: paint the inner spans. */

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button span {
                color: #3d1220 !important;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[kind="primary"] span,
            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[data-testid="stBaseButton-primary"] span {
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button:disabled span {
                color: #a9856f !important;
            }


            /* Sidebar mode radio */

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label {
                border-color: rgba(232, 200, 122, .22);
                background: rgba(40, 8, 18, .45);
            }

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label:hover {
                border-color: rgba(240, 208, 137, .60);
                background: rgba(40, 8, 18, .60);
                box-shadow: 0 8px 18px rgba(0, 0, 0, .30);
            }

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label:has(input:checked) {
                border-color: #d9a94f;

                background:
                    linear-gradient(
                        110deg,
                        rgba(217, 169, 79, .22),
                        rgba(40, 8, 18, .55)
                    );

                box-shadow:
                    0 0 0 1px rgba(217, 169, 79, .20),
                    0 10px 24px rgba(0, 0, 0, .25);
            }

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label p,

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label span,

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label div {
                color: #f3e6d3 !important;
            }


            /* Sidebar native widgets (dark maroon) */

            section[data-testid="stSidebar"]
            [data-testid="stWidgetLabel"] p {
                color: #f5ead6 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stCaptionContainer"] {
                color: #cfae8d !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stCaptionContainer"] {
                color: #776c62 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stDivider"] {
                border-color:
                    rgba(232, 200, 122, .20) !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stExpander"] {
                background:
                    rgba(40, 8, 18, .45) !important;

                border-color:
                    rgba(232, 200, 122, .22) !important;

                color: #ffffff !important;
            }

            /* Expander headers render as markdown, so override the
               global dark markdown rules explicitly. */

            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] p,
            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] li,
            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] h1,
            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] h2,
            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] h3,
            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] h4 {
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTabs"] button p {
                color: #cfae8d !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTabs"] button[aria-selected="true"] p {
                color: #f5ead6 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] input {
                background:
                    rgba(40, 8, 18, .55) !important;

                color: #f5ead6 !important;

                -webkit-text-fill-color: #f5ead6 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] div[data-baseweb="input"],
            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
                background:
                    rgba(40, 8, 18, .55) !important;

                border-color:
                    rgba(232, 200, 122, .25) !important;

                color: #f5ead6 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] div[data-baseweb="select"] div {
                color: #f5ead6 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] div[data-baseweb="select"] input {
                color: #f5ead6 !important;
                -webkit-text-fill-color: #f5ead6 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] svg,
            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] svg {
                fill: #cfae8d !important;
                color: #cfae8d !important;
            }


            /* Sidebar chrome icons */

            [data-testid="stSidebarCollapseButton"] button {
                color: #f5ead6 !important;
            }

            [data-testid="stSidebarCollapsedControl"] button {
                background: #fffdf7 !important;

                border:
                    1px solid rgba(107, 31, 54, .20) !important;

                color: #4a1425 !important;
            }


            /* Rank progress bar on the maroon sidebar */

            section[data-testid="stSidebar"] .progress-track {
                background: rgba(232, 200, 122, .18);
            }

            section[data-testid="stSidebar"] .progress-fill {
                background:
                    linear-gradient(
                        90deg,
                        #d9a94f,
                        #f0c778
                    );

                box-shadow:
                    0 0 10px rgba(217, 169, 79, .45);
            }


            /* Sliding toggle in light mode — sun, slid left */

            div[data-testid="stButton"] button[kind="tertiary"]::before,
            div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]::before {
                border-color: rgba(107, 31, 54, .25);

                background: #fffdf7;

                box-shadow:
                    0 2px 10px rgba(107, 31, 54, .10);
            }

            div[data-testid="stButton"] button[kind="tertiary"]:hover:not(:disabled)::before,
            div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]:hover:not(:disabled)::before {
                border-color: var(--gold);

                box-shadow:
                    0 0 16px rgba(168, 116, 31, .25);
            }

            div[data-testid="stButton"] button[kind="tertiary"]::after,
            div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]::after {
                right: 36px;
                left: auto;

                background: #6d1f37;

                color: #fff5e6;

                content: "☀️";
            }

            div[data-testid="stButton"] button[kind="tertiary"]:hover:not(:disabled)::after,
            div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"]:hover:not(:disabled)::after {
                right: 36px;
                left: auto;
            }

            .topbar-rule:hover {
                background: rgba(168, 116, 31, .45);
            }


            /* ====================================================
               READABILITY BOOST (light mode)
               Darker secondary text, bolder tiny labels,
               stronger buttons, brighter sidebar text.
            ==================================================== */

            :root {
                --muted: #5f564c;
                --quiet: #7d7268;

                --gold: #8a5a14;
                --gold-light: #6b4210;
                --cyan: #7a5410;

                --green: #166b47;
            }


            /* Tiny uppercase labels read better slightly bolder. */

            .brand-note,
            .live-label,
            .stage-kicker,
            .rail-kicker,
            .question-kicker,
            .answer-label,
            .ladder-caption {
                font-weight: 500;
            }


            /* Prize ladder rows */

            .ladder-item {
                color: #4e453d;
            }

            .ladder-item .level {
                color: #7d7268;
            }

            .ladder-item.passed {
                color: #7a5410;
            }


            /* Main buttons: stronger border, deeper text */

            div[data-testid="stButton"] button {
                border-color: rgba(107, 31, 54, .38);
                color: #521627 !important;
            }

            div[data-testid="stButton"] button:disabled {
                color: #8a6a76 !important;
            }


            /* Native secondary text */

            .stApp [data-testid="stCaptionContainer"] {
                color: #5f564c !important;
            }

            .stApp [data-testid="stTabs"] button p {
                color: #5f564c !important;
            }

            .stApp [data-testid="stMetric"] label p {
                color: #5f564c !important;
            }


            /* Sidebar tans on maroon: brighter */

            section[data-testid="stSidebar"]
            .sidebar-brand-note,
            section[data-testid="stSidebar"]
            .sidebar-section-title,
            section[data-testid="stSidebar"]
            .sidebar-hud-label {
                color: #ddc2a0;
            }

            section[data-testid="stSidebar"]
            .sidebar-hud-sub,
            section[data-testid="stSidebar"]
            .sidebar-stat-label,
            section[data-testid="stSidebar"]
            .depth-labels {
                color: #d3b896;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button:disabled {
                color: #b89a80 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTabs"] button p {
                color: #ddc2a0 !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stCaptionContainer"] {
                color: #5f564c !important;
            }

            section[data-testid="stSidebar"]
            .depth-node {
                background: rgba(232, 200, 122, .32);
            }


            /* ====================================================
               WHITE ON MAROON (sidebar + maroon accents)
               Gold stays for borders, nodes, tiles and buttons.
            ==================================================== */

            section[data-testid="stSidebar"]
            .sidebar-brand-name,
            section[data-testid="stSidebar"]
            .sidebar-brand-name span,
            section[data-testid="stSidebar"]
            .sidebar-brand-note,
            section[data-testid="stSidebar"]
            .sidebar-section-title,
            section[data-testid="stSidebar"]
            .mission-title,
            section[data-testid="stSidebar"]
            .sidebar-hud-label,
            section[data-testid="stSidebar"]
            .sidebar-hud-value,
            section[data-testid="stSidebar"]
            .sidebar-hud-sub,
            section[data-testid="stSidebar"]
            .sidebar-stat-label,
            section[data-testid="stSidebar"]
            .sidebar-stat-value,
            section[data-testid="stSidebar"]
            .depth-labels,
            section[data-testid="stSidebar"]
            .safety-note,
            section[data-testid="stSidebar"]
            .safety-note strong,
            section[data-testid="stSidebar"]
            .flag-summary,
            section[data-testid="stSidebar"]
            .flag-summary strong {
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[kind="primary"],
            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[data-testid="stBaseButton-primary"],
            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[kind="primary"]:hover:not(:disabled),
            section[data-testid="stSidebar"]
            div[data-testid="stButton"]
            button[data-testid="stBaseButton-primary"]:hover:not(:disabled) {
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label p,

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label span,

            section[data-testid="stSidebar"]
            div[data-testid="stRadio"]
            div[role="radiogroup"]
            label div {
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stWidgetLabel"] p,
            section[data-testid="stSidebar"]
            [data-testid="stCaptionContainer"],
            section[data-testid="stSidebar"]
            [data-testid="stExpander"],
            section[data-testid="stSidebar"]
            [data-testid="stExpander"]
            [data-testid="stMarkdownContainer"] p,
            section[data-testid="stSidebar"]
            [data-testid="stTabs"] button p,
            section[data-testid="stSidebar"]
            [data-testid="stTabs"] button[aria-selected="true"] p,
            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] input,
            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] div[data-baseweb="input"],
            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] div[data-baseweb="select"] div {
                color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] input,
            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] div[data-baseweb="select"] input {
                -webkit-text-fill-color: #ffffff !important;
            }

            section[data-testid="stSidebar"]
            [data-testid="stTextInput"] svg,
            section[data-testid="stSidebar"]
            [data-testid="stSelectbox"] svg {
                fill: #ffffff !important;
                color: #ffffff !important;
            }

            /* Maroon buttons + current tier: pure white text */

            div[data-testid="stButton"] button[kind="primary"],
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
            [data-testid="stBaseButton-primary"] {
                color: #ffffff !important;
            }

            .ladder-item.current,
            .ladder-item.current .level,
            .ladder-item.current .prize {
                color: #ffffff !important;
            }

            [data-testid="stSidebarCollapseButton"] button {
                color: #ffffff !important;
            }

        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# MATH FORMATTING
# ============================================================

MATH_SYMBOLS = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "θ": r"\theta",
    "λ": r"\lambda",
    "μ": r"\mu",
    "σ": r"\sigma",
    "φ": r"\phi",
    "Ω": r"\Omega",
    "ω": r"\omega",
}


def clean_text(value: object) -> str:

    text = "" if value is None else str(value)

    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
        " ",
        text,
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def format_math_text(value: object) -> str:
    """Turn common engineering notation into readable inline LaTeX."""

    text = clean_text(value)


    def matrix_replacement(
        match: re.Match[str],
    ) -> str:

        return (
            r"$\begin{bmatrix} "
            + match.group(1)
            + r" & "
            + match.group(2)
            + r" \\ "
            + match.group(3)
            + r" & "
            + match.group(4)
            + r" \end{bmatrix}$"
        )


    text = re.sub(
        r"\[\[\s*([^,\]]+),\s*([^\]]+)\],\s*"
        r"\[\s*([^,\]]+),\s*([^\]]+)\]\]",
        matrix_replacement,
        text,
    )


    text = re.sub(
        r"\[\s*([^,;\]]+),\s*([^;]+);\s*"
        r"([^,;\]]+),\s*([^\]]+)\]",
        matrix_replacement,
        text,
    )


    superscripts = str.maketrans(
        "⁰¹²³⁴⁵⁶⁷⁸⁹⁻",
        "0123456789-",
    )


    def power_replacement(
        match: re.Match[str],
    ) -> str:

        base = MATH_SYMBOLS.get(
            match.group(1),
            match.group(1),
        )

        exponent = (
            match.group(2) or match.group(3)
        ).translate(superscripts)

        return f"${base}^{{{exponent}}}$"


    text = re.sub(
        r"([A-Za-zαβγδεθλμσφΩω])"
        r"(?:\^([0-9]+)|"
        r"([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+))",
        power_replacement,
        text,
    )


    def subscript_replacement(
        match: re.Match[str],
    ) -> str:

        symbol = MATH_SYMBOLS[match.group(1)]

        return (
            f"${symbol}_{{{match.group(2)}}}$"
        )


    text = re.sub(
        r"([σλ])([0-9]+|[A-Za-z])",
        subscript_replacement,
        text,
    )


    for symbol, latex in MATH_SYMBOLS.items():

        text = re.sub(
            rf"(?<![A-Za-z\\$])"
            rf"{re.escape(symbol)}"
            rf"(?![A-Za-z])",

            lambda _match, latex=latex:
                f"${latex}$",

            text,
        )


    text = re.sub(
        r"(?:√|\\sqrt|sqrt)\(([^()]*)\)",

        lambda match:
            f"$\\sqrt{{{match.group(1)}}}$",

        text,
    )


    text = text.replace(
        "±",
        r" $\pm$ ",
    )

    text = text.replace(
        "×",
        r" $\times$ ",
    )

    text = text.replace(
        "÷",
        r" $\div$ ",
    )


    text = re.sub(
        r"(?<![\w$])"
        r"([A-Za-z])\^([0-9]+)",

        lambda match:
            f"${match.group(1)}^{{{match.group(2)}}}$",

        text,
    )


    text = text.replace(
        " * ",
        r" $\times$ ",
    )


    return text


# ============================================================
# LOAD QUESTIONS
# ============================================================

@st.cache_data(show_spinner=False)
def load_questions() -> pd.DataFrame:
    """Load questions instantly from local dataset with caching (0.0s lag)."""
    # 1. Prefer exported comprehensive dataset
    q1000_path = Path(__file__).parent / "data" / "gate_questions_1000.csv"
    source_path = q1000_path if q1000_path.exists() else DATA_PATH

    using_legacy_compatibility_bank = False

    if (
        not source_path.exists()
        and LEGACY_DATA_PATH.exists()
    ):
        source_path = LEGACY_DATA_PATH
        using_legacy_compatibility_bank = True

    if not source_path.exists():
        raise FileNotFoundError(
            "Question dataset not found. Add "
            f"{DATA_PATH.name} to the data folder."
        )

    frame = pd.read_csv(
        source_path,
        keep_default_na=False,
    )


    if using_legacy_compatibility_bank:

        balanced_rows = []

        base_count, remainder = divmod(
            800,
            len(LEVELS),
        )


        for level in LEVELS:

            level_rows = frame[
                frame["difficulty"] == level
            ]

            requested_count = (
                base_count
                + int(level <= remainder)
            )

            balanced_rows.append(
                level_rows.head(requested_count)
            )


        frame = pd.concat(
            balanced_rows,
            ignore_index=True,
        )


    required = {
        "difficulty",
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct",
    }


    if "id" not in frame.columns:

        frame.insert(
            0,
            "id",
            range(1, len(frame) + 1),
        )


    if "subject" not in frame.columns:
        frame["subject"] = "GATE Knowledge"


    if "topic" not in frame.columns:
        frame["topic"] = "Mixed challenge"


    missing = required.difference(
        frame.columns
    )


    if missing:

        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )


    text_columns = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
    ]


    for column in text_columns:

        frame[column] = frame[column].map(
            clean_text
        )


    frame["difficulty"] = pd.to_numeric(
        frame["difficulty"],
        errors="raise",
    ).astype(int)


    correct_labels = {
        "a": 0,
        "b": 1,
        "c": 2,
        "d": 3,
    }


    normalized_correct = frame["correct"].map(
        lambda value:
            correct_labels.get(
                str(value).strip().casefold(),
                value,
            )
    )


    frame["correct"] = pd.to_numeric(
        normalized_correct,
        errors="raise",
    ).astype(int)


    frame = frame[
        frame["difficulty"].between(1, 15)
    ]


    frame = frame[
        frame["correct"].between(0, 3)
    ].copy()


    normalized_options = frame[
        [
            "option_a",
            "option_b",
            "option_c",
            "option_d",
        ]
    ].apply(
        lambda column:
            column.str.casefold()
    )


    invalid_text = frame[
        text_columns
    ].eq("").any(axis=1)


    duplicate_questions = (
        frame["question"]
        .duplicated(keep=False)
    )


    duplicate_options = (
        normalized_options
        .nunique(axis=1)
        .lt(4)
    )


    duplicate_ids = (
        frame["id"]
        .duplicated(keep=False)
    )


    invalid_rows = (
        invalid_text
        | duplicate_questions
        | duplicate_options
        | duplicate_ids
    )


    frame.attrs["rejected_rows"] = int(
        invalid_rows.sum()
    )


    frame = frame.loc[
        ~invalid_rows
    ].copy()


    if frame.empty:

        raise ValueError(
            "The classified dataset has no playable questions."
        )


    return frame


# ============================================================
# REVIEW QUEUE
# ============================================================

@st.cache_data(ttl=120, show_spinner=False)
def load_review_queue() -> set[str]:
    """Load flagged question IDs from FastAPI/Supabase with JSON fallback (cached)."""
    try:
        api_flags = api_client.get_flagged_question_ids()
        if api_flags:
            return api_flags
    except Exception:
        pass

    if not REVIEW_QUEUE_PATH.exists():
        return set()


    try:

        stored_ids = json.loads(
            REVIEW_QUEUE_PATH.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Review queue is not valid JSON: "
            f"{REVIEW_QUEUE_PATH}"
        ) from error


    if not isinstance(
        stored_ids,
        list,
    ):

        raise ValueError(
            "Review queue must contain a JSON list "
            "of question IDs."
        )


    if any(
        isinstance(
            question_id,
            (dict, list, bool)
        )
        or question_id is None

        for question_id in stored_ids
    ):

        raise ValueError(
            "Review queue contains an invalid question ID."
        )


    return {
        str(question_id)
        for question_id in stored_ids
    }


def save_review_queue(
    flagged_questions: set[str],
) -> None:
    """Persist flagged question IDs to Supabase and atomically to disk."""
    for qid in flagged_questions:
        try:
            if str(qid).isdigit():
                api_client.flag_question_server(int(qid), "Flagged in Millionaire challenge")
        except Exception:
            pass

    REVIEW_QUEUE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = None


    try:

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=REVIEW_QUEUE_PATH.parent,
            prefix=".review_queue.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:

            temporary_path = Path(
                temporary_file.name
            )


            json.dump(
                sorted(
                    (
                        str(question_id)
                        for question_id
                        in flagged_questions
                    ),

                    key=lambda question_id:
                        (
                            (0, int(question_id))
                            if question_id.isdigit()
                            else (1, question_id)
                        ),
                ),

                temporary_file,

                indent=2,
            )


            temporary_file.write("\n")


        os.replace(
            temporary_path,
            REVIEW_QUEUE_PATH,
        )


    finally:

        if (
            temporary_path is not None
            and temporary_path.exists()
        ):

            temporary_path.unlink()


# ============================================================
# QUESTION OBJECTS
# ============================================================

def row_to_question(
    row: pd.Series,
    correct_position: int | None = None,
) -> dict:

    original_options = [
        str(
            row[
                f"option_{letter.lower()}"
            ]
        )

        for letter in OPTION_LETTERS
    ]


    original_correct = int(
        row["correct"]
    )


    if correct_position is None:

        correct_position = random.randrange(4)

    else:

        correct_position = (
            int(correct_position) % 4
        )


    distractor_indexes = [
        index

        for index in range(4)

        if index != original_correct
    ]


    random.shuffle(
        distractor_indexes
    )


    shuffled_options: list[str] = []

    distractor_cursor = 0


    for position in range(4):

        if position == correct_position:

            shuffled_options.append(
                original_options[
                    original_correct
                ]
            )

        else:

            shuffled_options.append(
                original_options[
                    distractor_indexes[
                        distractor_cursor
                    ]
                ]
            )

            distractor_cursor += 1


    return {
        "id": str(
            row.get(
                "id",
                f"{row['difficulty']}-"
                f"{hash(row['question'])}",
            )
        ),

        "subject": str(
            row.get(
                "subject",
                "GATE Knowledge",
            )
        ),

        "topic": str(
            row.get(
                "topic",
                "Mixed challenge",
            )
        ),

        "difficulty": int(
            row["difficulty"]
        ),

        "question": str(
            row["question"]
        ),

        "options": shuffled_options,

        "correct": correct_position,
    }


def choose_question(
    frame: pd.DataFrame,
    level: int,
    exclude: str | None = None,
    correct_position: int | None = None,
) -> dict:

    pool = frame[
        frame["difficulty"] == level
    ]


    if (
        exclude is not None
        and len(pool) > 1
    ):

        pool = pool[
            pool["question"].astype(str)
            != exclude
        ]


    if pool.empty:

        pool = frame[
            frame["difficulty"] == level
        ]


    return row_to_question(
        pool.sample(n=1).iloc[0],
        correct_position=correct_position,
    )


# ============================================================
# GAME STATE
# ============================================================

def initialize_game(
    flagged_questions: set[str] | None = None,
) -> None:

    frame = load_questions()


    answer_positions = (
        list(range(4)) * 4
    )

    random.shuffle(
        answer_positions
    )


    st.session_state.questions = {

        level: choose_question(
            frame,
            level,
            correct_position=
                answer_positions[level - 1],
        )

        for level in LEVELS
    }


    st.session_state.answer_positions = {

        level:
            answer_positions[level - 1]

        for level in LEVELS
    }


    st.session_state.current_level = 1

    st.session_state.selected_option = None

    st.session_state.answered = False

    st.session_state.last_result = None

    st.session_state.removed_options = set()

    st.session_state.used_5050 = False

    st.session_state.used_swap = False

    st.session_state.view_version = 0

    st.session_state.sound_event = None


    st.session_state.flagged_questions = (
        set(flagged_questions)

        if flagged_questions is not None

        else load_review_queue()
    )


def new_game() -> None:

    initialize_game()

    st.rerun()


# ============================================================
# INITIAL LOAD
# ============================================================

try:

    question_frame = load_questions()

except Exception as error:

    st.error(
        "Unable to load the classified question bank: "
        f"{error}"
    )

    st.stop()


try:

    persisted_flagged_questions = (
        load_review_queue()
    )

except Exception as error:

    st.error(
        f"Unable to load the review queue: {error}"
    )

    st.stop()


if "questions" not in st.session_state:

    initialize_game(
        flagged_questions=
            persisted_flagged_questions
    )


if "flagged_questions" not in st.session_state:

    st.session_state.flagged_questions = set(
        persisted_flagged_questions
    )


# ============================================================
# CURRENT QUESTION
# ============================================================

current_level = (
    st.session_state.current_level
)

current_question = (
    st.session_state.questions[
        current_level
    ]
)

current_question_key = str(
    current_question["id"]
)


current_question_flagged = (
    current_question_key
    in st.session_state.flagged_questions
)


next_checkpoint = next(
    (
        checkpoint

        for checkpoint in (5, 10, 15)

        if current_level < checkpoint
    ),

    None,
)


sound_event = (
    st.session_state.get(
        "sound_event"
    )
)

st.session_state.sound_event = None

play_sound(sound_event)

pending_celebration = st.session_state.get(
    "pending_celebration"
)
st.session_state.pending_celebration = None

if pending_celebration:
    if pending_celebration.get("leveled_up"):
        st.balloons()

    for toast_msg, toast_icon in pending_celebration.get(
        "toasts",
        [],
    ):
        st.toast(toast_msg, icon=toast_icon)


# ============================================================
# PRIZE LADDER
# ============================================================

def show_ladder() -> None:

    ladder_items = []


    for level in reversed(LEVELS):

        classes = [
            "ladder-item"
        ]


        if level in (5, 10, 15):

            classes.append(
                "safe"
            )


        if level < current_level:

            classes.append(
                "passed"
            )


        if level == current_level:

            classes.append(
                "current"
            )


        label = f"{level:02d}"

        prize = PRIZES[level - 1]


        marker = (
            "◆"
            if level in (5, 10, 15)

            else "✓"
            if level < current_level

            else ""
        )


        ladder_items.append(
            f'<div class="{" ".join(classes)}">'
            f'<span class="level">'
            f'{marker} {label}'
            f'</span>'
            f'<span class="prize">'
            f'{html.escape(prize)}'
            f'</span>'
            f'</div>'
        )


        if level in (5, 10):

            ladder_items.append(
                '<div class="safety-line"></div>'
            )


    st.markdown(
        '<div class="ladder-heading">'
        '<div class="ladder-title">'
        'Prize path'
        '</div>'
        '<div class="ladder-caption">'
        '15 levels'
        '</div>'
        '</div>'

        + "".join(ladder_items)

        + '<div class="toolkit-card">'
        '<div class="toolkit-title">'
        'Strategy desk'
        '</div>'
        '<div class="toolkit-copy">'
        'Two tools. One chance each. '
        'Spend them when the question '
        'deserves a second look.'
        '</div>'
        '</div>',

        unsafe_allow_html=True,
    )


# ============================================================
# AUTH GATE — landing page is login, then home
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None


def render_landing_page() -> None:
    """Full-screen login landing page (light/dark aware)."""

    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }

            [data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }

            .landing-brand {
                text-align: center;
                margin-bottom: 1.4rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if IS_LIGHT_THEME:
        landing_title = "#33302b"
        landing_sub = "#5f564c"
    else:
        landing_title = "#f7f3eb"
        landing_sub = "#9197a8"

    _, landing_col, _ = st.columns([1, 2.2, 1])

    with landing_col:
        st.markdown(
            '<div class="landing-brand">'
            '<div class="brand-mark" style="margin: 0 auto;">'
            'FM'
            '</div>'
            f'<div class="brand-name" '
            f'style="margin-top: .9rem; font-size: 2rem; '
            f'color: {landing_title};">'
            'Future<span>Mining</span>'
            '</div>'
            f'<div class="brand-note" '
            f'style="color: {landing_sub};">'
            'The field test of mining intelligence'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(
                "<div style='text-align: center; "
                "font-weight: 800; font-size: 1.05rem; "
                f"letter-spacing: -.02em; color: {landing_title};'>"
                "Welcome back, miner ⛏️</div>"
                "<div style='text-align: center; "
                f"font-size: .78rem; color: {landing_sub}; "
                "margin: .3rem 0 1rem;'>"
                "Log in to enter the mine</div>",
                unsafe_allow_html=True,
            )

            login_tab, signup_tab = st.tabs(
                ["Login", "Create account"]
            )

            with login_tab:
                landing_user = st.text_input(
                    "Username",
                    key="landing_login_username",
                )
                landing_pass = st.text_input(
                    "Password",
                    type="password",
                    key="landing_login_password",
                )
                landing_remember = st.checkbox(
                    "Remember me on this device",
                    key="landing_remember_me",
                )
                if st.button(
                    "Log In",
                    type="primary",
                    use_container_width=True,
                    key="landing_btn_login",
                ):
                    if landing_user and landing_pass:
                        success, msg, udata = (
                            api_client.login_user(
                                landing_user,
                                landing_pass,
                            )
                        )
                        if success:
                            st.session_state.user = udata
                            if (
                                landing_remember
                                and COOKIES_AVAILABLE
                            ):
                                _remember_token = (
                                    api_client.create_remember_token(
                                        udata
                                    )
                                )
                                if _remember_token:
                                    st.session_state.fm_pending_remember = (
                                        _remember_token
                                    )
                            st.toast(msg, icon="🎉")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning(
                            "Please enter username and password"
                        )

            with signup_tab:
                reg_user = st.text_input(
                    "Choose Username",
                    key="landing_reg_username",
                )
                reg_pass = st.text_input(
                    "Choose Password",
                    type="password",
                    key="landing_reg_password",
                )
                reg_name = st.text_input(
                    "Full Name (Optional)",
                    key="landing_reg_name",
                )
                reg_email = st.text_input(
                    "Email (Optional)",
                    key="landing_reg_email",
                )
                if st.button(
                    "Create Account",
                    type="primary",
                    use_container_width=True,
                    key="landing_btn_register",
                ):
                    if reg_user and reg_pass:
                        success, msg, udata = (
                            api_client.register_user(
                                reg_user,
                                reg_pass,
                                reg_name,
                                reg_email,
                            )
                        )
                        if success:
                            st.session_state.user = udata
                            st.toast(msg, icon="🎉")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning(
                            "Please enter username and password"
                        )

            st.divider()

            if st.button(
                "Continue as Guest",
                use_container_width=True,
                key="landing_btn_guest",
            ):
                st.session_state.user = {
                    "id": None,
                    "username": "guest",
                    "full_name": "Guest Miner",
                    "email": None,
                    "is_guest": True,
                    "auth_source": "guest",
                }
                st.toast(
                    "Entering as guest — "
                    "progress won't be saved.",
                    icon="👤",
                )
                st.rerun()

            st.markdown(
                "<div style='text-align: center; "
                f"font-size: .72rem; color: {landing_sub};'>"
                "Guest mode lets you explore · "
                "Log in to save progress"
                "</div>",
                unsafe_allow_html=True,
            )

        _, landing_theme_col, _ = st.columns([2, 1, 2])

        with landing_theme_col:
            if st.button(
                (
                    "🌙 Dark"
                    if IS_LIGHT_THEME
                    else "☀️ Light"
                ),
                use_container_width=True,
                key="landing_theme_toggle",
            ):
                st.session_state.theme = (
                    "dark"
                    if IS_LIGHT_THEME
                    else "light"
                )
                st.rerun()


# ============================================================
# REMEMBER ME — cookie manager + automatic login
# The manager must be created before the auth gate so its
# (invisible) component renders on the landing page too.
# ============================================================

cookie_manager = (
    CookieManager(key="fm_cookie_manager")
    if COOKIES_AVAILABLE
    else None
)

if cookie_manager is not None:
    pending_token = st.session_state.get("fm_pending_remember")
    if pending_token:
        cookie_manager.set(
            api_client.REMEMBER_COOKIE_NAME,
            pending_token,
            max_age=api_client.REMEMBER_TOKEN_DAYS * 24 * 3600,
            key="fm_remember_set",
        )
        del st.session_state.fm_pending_remember

    if st.session_state.user is None:
        saved_token = cookie_manager.get(
            api_client.REMEMBER_COOKIE_NAME
        )
        if saved_token:
            remembered = api_client.validate_remember_token(
                saved_token
            )
            if remembered:
                st.session_state.user = remembered
                st.toast(
                    "Welcome back, "
                    f"{remembered.get('full_name') or remembered.get('username')}!",
                    icon="🔑",
                )
            else:
                cookie_manager.delete(
                    api_client.REMEMBER_COOKIE_NAME,
                    key="fm_remember_stale",
                )


if st.session_state.user is None:
    render_landing_page()
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    conn_mode = api_client.get_connection_mode()
    if conn_mode == "fastapi":
        st.markdown(
            '<div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.35); padding: 0.55rem 0.85rem; border-radius: 9px; margin-bottom: 0.85rem; display: flex; align-items: center; gap: 8px;">'
            '<span style="display: inline-block; width: 9px; height: 9px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 8px #22c55e;"></span>'
            '<span style="color: #4ade80; font-size: 0.85rem; font-weight: 600;">Connection: Online · Cloud Synced</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif conn_mode == "direct_db":
        st.markdown(
            '<div style="background: rgba(234, 179, 8, 0.12); border: 1px solid rgba(234, 179, 8, 0.35); padding: 0.55rem 0.85rem; border-radius: 9px; margin-bottom: 0.85rem; display: flex; align-items: center; gap: 8px;">'
            '<span style="display: inline-block; width: 9px; height: 9px; background: #eab308; border-radius: 50%; box-shadow: 0 0 8px #eab308;"></span>'
            '<span style="color: #facc15; font-size: 0.85rem; font-weight: 600;">Connection: Connected · Direct</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); padding: 0.55rem 0.85rem; border-radius: 9px; margin-bottom: 0.85rem; display: flex; align-items: center; gap: 8px;">'
            '<span style="display: inline-block; width: 9px; height: 9px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 8px #ef4444;"></span>'
            '<span style="color: #f87171; font-size: 0.85rem; font-weight: 600;">Connection: Offline Mode</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # User Profile / Authentication Section
    user = st.session_state.get("user")
    if user:
        with st.container(border=True):
            u_col1, u_col2 = st.columns([3, 1])
            with u_col1:
                st.markdown(f"**👤 {user.get('full_name') or user.get('username')}**")
                st.caption(
                    f"@{user.get('username')} · "
                    f"{'Guest mode' if user.get('is_guest') else 'GATE Mining'}"
                )
            with u_col2:
                if st.button("🚪", help="Logout"):
                    if cookie_manager is not None:
                        _saved = cookie_manager.get(
                            api_client.REMEMBER_COOKIE_NAME
                        )
                        if _saved:
                            api_client.revoke_remember_token(
                                _saved
                            )
                            cookie_manager.delete(
                                api_client.REMEMBER_COOKIE_NAME,
                                key="fm_remember_del",
                            )
                    st.session_state.user = None
                    st.toast("Logged out successfully.")
                    st.rerun()
    else:
        with st.expander("🔐 Login / Register (Save Progress)", expanded=False):
            auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
            with auth_tab1:
                l_user = st.text_input("Username", key="login_username")
                l_pass = st.text_input("Password", type="password", key="login_password")
                l_remember = st.checkbox("Remember me on this device", key="login_remember_me")
                if st.button("Log In", type="primary", use_container_width=True, key="btn_login_submit"):
                    if l_user and l_pass:
                        success, msg, udata = api_client.login_user(l_user, l_pass)
                        if success:
                            st.session_state.user = udata
                            if l_remember and COOKIES_AVAILABLE:
                                _remember_token = api_client.create_remember_token(udata)
                                if _remember_token:
                                    st.session_state.fm_pending_remember = _remember_token
                            st.toast(msg, icon="🎉")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter username and password")
            with auth_tab2:
                r_user = st.text_input("Choose Username", key="reg_username")
                r_pass = st.text_input("Choose Password", type="password", key="reg_password")
                r_name = st.text_input("Full Name (Optional)", key="reg_name")
                r_email = st.text_input("Email (Optional)", key="reg_email")
                if st.button("Create Account", type="primary", use_container_width=True, key="btn_reg_submit"):
                    if r_user and r_pass:
                        success, msg, udata = api_client.register_user(r_user, r_pass, r_name, r_email)
                        if success:
                            st.session_state.user = udata
                            st.toast(msg, icon="🎉")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please enter username and password")

    app_mode = st.radio(
        "🎯 Select Mode:",
        [
            "🎮 Millionaire Challenge",
            "📚 GATEMining Practice",
            "⏱️ GATEMining Mock Test",
            "📊 GATE Analytics & History",
            "ℹ️ About the Developers",
        ],
        index=0,
        key="global_app_mode",
    )

    st.divider()

    depth_nodes = []


    for depth in LEVELS:

        node_class = (

            "depth-node current"

            if depth == current_level

            else "depth-node passed"

            if depth < current_level

            else "depth-node"
        )


        depth_nodes.append(
            f'<span class="{node_class}" '
            f'title="Question {depth}">'
            f'</span>'
        )


    used_tools = (
        int(st.session_state.used_5050)
        + int(st.session_state.used_swap)
    )


    flagged_count = len(
        st.session_state.flagged_questions
    )


    sound_enabled = (
        st.session_state.get(
            "sound_enabled",
            True,
        )
    )


    sound_label = (
        "♫ Sound on"
        if sound_enabled
        else "♫ Sound off"
    )


    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-mark">'
        'FM'
        '</div>'
        '<div>'
        '<div class="sidebar-brand-name">'
        'Future<span>Mining</span>'
        '</div>'
        '<div class="sidebar-brand-note">'
        'Mission control'
        '</div>'
        '</div>'
        '</div>',

        unsafe_allow_html=True,
    )


    st.markdown(
        '<div class="mission-title">'
        'Mission control'
        '<span>● online</span>'
        '</div>'

        '<div class="sidebar-hud">'

        '<div class="sidebar-hud-label">'
        'Active descent'
        '</div>'

        f'<div class="sidebar-hud-value">'
        f'Tier {current_level:02d}'
        f'</div>'

        f'<div class="sidebar-hud-sub">'
        f'Target seam · '
        f'{html.escape(PRIZES[current_level - 1])}'
        f'</div>'

        '<div class="sidebar-stats">'

        '<div class="sidebar-stat">'
        '<div class="sidebar-stat-label">'
        'Run'
        '</div>'
        '<div class="sidebar-stat-value">'
        f'{max(0, current_level - 1):02d} / 15'
        '</div>'
        '</div>'

        '<div class="sidebar-stat">'
        '<div class="sidebar-stat-label">'
        'Tools'
        '</div>'
        '<div class="sidebar-stat-value">'
        f'{2 - used_tools} left'
        '</div>'
        '</div>'

        '<div class="sidebar-stat">'
        '<div class="sidebar-stat-label">'
        'Flags'
        '</div>'
        '<div class="sidebar-stat-value">'
        f'{flagged_count:02d}'
        '</div>'
        '</div>'

        '<div class="sidebar-stat">'
        '<div class="sidebar-stat-label">'
        'Floor'
        '</div>'
        '<div class="sidebar-stat-value">'
        f'{next_checkpoint or "FINAL"}'
        '</div>'
        '</div>'

        '</div>'
        '</div>',

        unsafe_allow_html=True,
    )


    rank_info = api_client.get_gamification(user)

    rank_streak_label = (
        f"🔥 {rank_info['streak']}"
        if rank_info['streak'] > 0
        else "🔥 —"
    )

    if rank_info["next_name"]:
        rank_next_label = (
            f"Next: {rank_info['next_name']} · "
            f"{rank_info['to_next']} XP to go"
        )
    else:
        rank_next_label = "Max rank achieved 👑"

    st.markdown(
        '<div class="mission-title">'
        'Miner rank'
        f'<span>{rank_streak_label}</span>'
        '</div>'

        '<div class="sidebar-hud">'

        '<div class="sidebar-hud-label">'
        f"{rank_info['rank_icon']} {rank_info['rank_name']}"
        '</div>'

        '<div class="sidebar-hud-value">'
        f"{rank_info['xp']} XP"
        '</div>'

        '<div class="progress-track">'
        f'<div class="progress-fill" '
        f'style="width:{rank_info["progress_pct"]:.1f}%">'
        '</div>'
        '</div>'

        '<div class="sidebar-hud-sub">'
        f'{rank_next_label}'
        '</div>'

        '</div>',

        unsafe_allow_html=True,
    )


    st.markdown(
        '<div class="mission-title">'
        'Shaft depth'
        f'<span>{current_level:02d} / 15</span>'
        '</div>'

        '<div class="depth-map">'
        + "".join(depth_nodes)
        + '</div>'

        '<div class="depth-labels">'
        '<span>surface</span>'
        '<span>deep seam</span>'
        '</div>',

        unsafe_allow_html=True,
    )


    st.markdown(
        '<div class="sidebar-rule"></div>'
        '<div class="sidebar-section-title">'
        'Audio atmosphere'
        '</div>',

        unsafe_allow_html=True,
    )


    if st.button(
        sound_label,
        use_container_width=True,
        key="sidebar_sound_toggle",
    ):

        st.session_state.sound_enabled = (
            not sound_enabled
        )

        st.rerun()


    st.markdown(
        '<div class="sidebar-section-title '
        'lifeline-title">'
        'One-use tools'
        '</div>',

        unsafe_allow_html=True,
    )


    sidebar_life_a, sidebar_life_b = (
        st.columns(2)
    )


    with sidebar_life_a:

        if st.button(
            "◐ 50/50"
            if not st.session_state.used_5050
            else "✓ Used",

            type="primary",

            use_container_width=True,

            disabled=(
                st.session_state.used_5050
                or st.session_state.answered
            ),

            help="Remove two incorrect answers",

            key="sidebar_5050",
        ):

            wrong = [
                index

                for index in range(4)

                if index !=
                current_question["correct"]
            ]


            st.session_state.removed_options = (
                set(
                    random.sample(
                        wrong,
                        2,
                    )
                )
            )


            st.session_state.used_5050 = True

            st.session_state.view_version += 1

            st.session_state.sound_event = (
                "lifeline"
            )

            st.rerun()


    with sidebar_life_b:

        if st.button(
            "⇄ Swap"
            if not st.session_state.used_swap
            else "✓ Used",

            type="primary",

            use_container_width=True,

            disabled=(
                st.session_state.used_swap
                or st.session_state.answered
            ),

            help=(
                "Swap for another question "
                "at the same difficulty"
            ),

            key="sidebar_swap",
        ):

            replacement = choose_question(
                question_frame,
                current_level,

                exclude=
                    current_question[
                        "question"
                    ],

                correct_position=
                    st.session_state
                    .answer_positions[
                        current_level
                    ],
            )


            st.session_state.questions[
                current_level
            ] = replacement


            st.session_state.removed_options = (
                set()
            )

            st.session_state.selected_option = (
                None
            )

            st.session_state.used_swap = True

            st.session_state.view_version += 1

            st.session_state.sound_event = (
                "swap"
            )

            st.rerun()


    st.markdown(
        '<div class="safety-note">'
        '<span>◆</span>'
        '<span>'
        '<strong>Safe floors</strong><br>'
        'Questions 5, 10 and 15 '
        'protect your climb.'
        '</span>'
        '</div>',

        unsafe_allow_html=True,
    )


    st.markdown(
        '<div class="flag-summary">'
        '<span class="flag-summary-icon">'
        '⚑'
        '</span>'
        '<span>'
        f'<strong>{flagged_count}</strong> '
        f'question'
        f'{"s" if flagged_count != 1 else ""} '
        'queued for review'
        '</span>'
        '</div>',

        unsafe_allow_html=True,
    )


    with st.expander(
        f"Review queue · {flagged_count}",
        expanded=flagged_count > 0,
    ):

        if flagged_count:

            question_ids = sorted(
                st.session_state.flagged_questions,

                key=lambda question_id:
                    (
                        (0, int(question_id))
                        if str(question_id).isdigit()
                        else (1, str(question_id))
                    ),
            )


            question_id_values = (
                question_frame["id"]
                .astype(str)
            )


            for question_id in question_ids:

                matching_rows = (
                    question_frame.loc[
                        question_id_values
                        == str(question_id)
                    ]
                )


                if matching_rows.empty:

                    st.caption(
                        f"Question {question_id} "
                        "· no longer in the bank"
                    )

                    continue


                question = (
                    matching_rows.iloc[0]
                )


                st.caption(
                    f"Question {question_id} · "
                    f"{question['subject']} · "
                    f"{question['topic']}"
                )

        else:

            st.caption(
                "No questions are currently "
                "waiting for review."
            )


        if st.button(
            "Clear review queue",

            use_container_width=True,

            disabled=not flagged_count,

            key="sidebar_clear_review_queue",
        ):

            st.session_state.flagged_questions.clear()

            save_review_queue(
                st.session_state.flagged_questions
            )

            st.rerun()


    if st.button(
        "Restart this round",

        use_container_width=True,

        key="sidebar_restart",
    ):

        new_game()


# ============================================================
# TOP BAR
# ============================================================

topbar_left, topbar_right = st.columns([8, 1])

with topbar_left:
    st.markdown(
        '<div class="brand-lockup">'

        '<div class="brand-mark">'
        'FM'
        '</div>'

        '<div>'

        '<div class="brand-name">'
        'Future<span>Mining</span>'
        '</div>'

        '<div class="brand-note">'
        'The field test of mining intelligence'
        '</div>'

        '</div>'

        '</div>'

        '<div class="live-label" style="margin-top:.6rem;">'

        '<span class="live-dot"></span>'

        'GATE question bank · live round'

        '</div>',

        unsafe_allow_html=True,
    )

with topbar_right:
    st.markdown(
        "<div style='height:8px;'></div>",
        unsafe_allow_html=True,
    )

    if st.button(
        "theme",
        type="tertiary",
        use_container_width=True,
        key="home_theme_toggle",
        help=(
            "Switch to dark mode"
            if IS_LIGHT_THEME
            else "Switch to light mode"
        ),
    ):
        st.session_state.theme = (
            "dark"
            if IS_LIGHT_THEME
            else "light"
        )
        st.rerun()

st.markdown(
    '<div class="topbar-rule"></div>',
    unsafe_allow_html=True,
)


# ============================================================
# MAIN LAYOUT
# ============================================================

current_mode = st.session_state.get("global_app_mode", "🎮 Millionaire Challenge")

if current_mode in ("📚 GATEMining Practice", "📚 ExamGoal Practice"):
    examgoal.render_practice_mode(question_frame)

elif current_mode in ("⏱️ GATEMining Mock Test", "⏱️ ExamGoal GATE Mock Test"):
    examgoal.render_mock_test_mode(question_frame)

elif current_mode == "📊 GATE Analytics & History":
    examgoal.render_analytics_dashboard()

elif current_mode == "ℹ️ About the Developers":
    about.render_about_page(light=IS_LIGHT_THEME)

else:
    stage, ladder = st.columns(
        [3.5, 1.25],
        gap="medium",
    )


    # ============================================================
    # STAGE
    # ============================================================

    with stage:

        with st.container(border=True):

            st.markdown(
                '<div class="stage-header">'

                '<div>'

                '<div class="stage-kicker">'
                'Live challenge · round 01 · your move'
                '</div>'

                '<div class="stage-title">'
                'Make the next decision count.'
                '</div>'

                '</div>'

                f'<div class="stage-meta">'
                f'Question '
                f'<strong>{current_level:02d} / 15</strong>'
                f'<br>'
                f'Current prize '
                f'<strong>'
                f'{PRIZES[current_level - 1]}'
                f'</strong>'
                f'</div>'

                '</div>',

                unsafe_allow_html=True,
            )


            st.markdown(
                f'<div class="progress-track">'

                f'<div class="progress-fill" '
                f'style="width:'
                f'{(current_level / 15) * 100:.2f}%">'
                f'</div>'

                f'</div>',

                unsafe_allow_html=True,
            )


            with st.container(border=True):

                st.markdown(
                    '<span class="question-card-marker">'
                    '</span>'

                    f'<div class="question-kicker">'
                    f'{html.escape(current_question["subject"])}'
                    f' · '
                    f'{html.escape(current_question["topic"])}'
                    f'</div>',

                    unsafe_allow_html=True,
                )


                st.markdown(
                    format_math_text(
                        current_question["question"]
                    )
                )


            flag_col, flag_status_col = (
                st.columns([1.15, 2.85])
            )


            with flag_col:

                if st.button(
                    "⚑ Unflag question"
                    if current_question_flagged
                    else "⚑ Flag question",

                    use_container_width=True,

                    key=(
                        f"flag_{current_question_key}_"
                        f"{st.session_state.view_version}"
                    ),

                    help="Mark this question for review",
                ):

                    if current_question_flagged:

                        st.session_state.flagged_questions.discard(
                            current_question_key
                        )

                    else:

                        st.session_state.flagged_questions.add(
                            current_question_key
                        )


                    save_review_queue(
                        st.session_state.flagged_questions
                    )

                    st.rerun()


            with flag_status_col:

                st.markdown(
                    '<div class="flag-status">'

                    + (
                        "Marked for review · thank you "
                        "for keeping the seam clean."

                        if current_question_flagged

                        else
                        "See a questionable prompt? "
                        "Mark it for review."
                    )

                    + "</div>",

                    unsafe_allow_html=True,
                )


            # ====================================================
            # ANSWER OPTIONS
            # ====================================================

            active_options = [
                index

                for index in range(4)

                if index not in
                st.session_state.removed_options
            ]


            option_labels = [

                f"{OPTION_LETTERS[index]}  ·  "
                f"{format_math_text(current_question['options'][index])}"

                for index in active_options
            ]


            widget_key = (
                f"answer_{current_level}_"
                f"{current_question['id']}_"
                f"{st.session_state.view_version}"
            )


            st.markdown(
                '<div class="answer-label">'
                'Choose one answer · '
                'lock it when ready'
                '</div>',

                unsafe_allow_html=True,
            )


            selected_label = None


            if st.session_state.answered:

                review_items = []

                correct_index = (
                    current_question["correct"]
                )

                selected_answer = (
                    st.session_state.selected_option
                )


                for index in active_options:

                    if index == correct_index:

                        state_class = "correct"
                        mark = "✓ CORRECT"

                    elif index == selected_answer:

                        state_class = "wrong"
                        mark = "✕ YOUR PICK"

                    else:

                        state_class = "muted"
                        mark = ""


                    review_items.append(
                        '<div class='
                        f'"answer-review-choice '
                        f'{state_class}">'

                        '<span '
                        'class="answer-review-badge">'

                        f'{OPTION_LETTERS[index]}'

                        '</span>'

                        '<span>'

                        f'{html.escape(current_question["options"][index])}'

                        '</span>'

                        '<span '
                        'class="answer-review-mark">'

                        f'{mark}'

                        '</span>'

                        '</div>'
                    )


                st.markdown(
                    '<div class="answer-review">'
                    + "".join(review_items)
                    + "</div>",

                    unsafe_allow_html=True,
                )


            else:

                selected_label = st.radio(
                    "Answer choices",

                    option_labels,

                    index=None,

                    key=widget_key,

                    label_visibility="collapsed",
                )


            selected_index = None


            if selected_label:

                selected_index = active_options[
                    option_labels.index(
                        selected_label
                    )
                ]


            # ====================================================
            # LOCK ANSWER
            # ====================================================

            lock = st.button(
                "Lock it in",

                type="primary",

                use_container_width=True,

                disabled=st.session_state.answered,
            )


            if lock:

                if selected_index is None:

                    st.warning(
                        "Choose an answer before "
                        "locking it."
                    )

                else:

                    st.session_state.selected_option = (
                        selected_index
                    )

                    st.session_state.answered = True

                    st.session_state.last_result = (
                        selected_index
                        == current_question["correct"]
                    )

                    user = st.session_state.get("user")
                    if user and "id" in current_question:
                        api_client.record_question_attempt(
                            user_id=user["id"],
                            question_id=int(current_question["id"]),
                            selected_option=selected_index,
                            is_correct=st.session_state.last_result,
                            mode="millionaire",
                        )
                        if not st.session_state.last_result or current_level == 15:
                            final_score = float(current_level if st.session_state.last_result else max(0, current_level - 1))
                            api_client.save_test_session(
                                user_id=user["id"],
                                mode="millionaire",
                                score=final_score,
                                total_questions=15,
                                correct_count=int(final_score),
                                incorrect_count=0 if st.session_state.last_result else 1,
                                unattempted_count=max(0, 15 - current_level),
                                details_json=json.dumps({"prize": PRIZES[current_level - 1] if st.session_state.last_result else (PRIZES[current_level - 2] if current_level > 1 else "₹0")})
                            )

                    if st.session_state.last_result:
                        xp_info = api_client.award_xp(
                            user,
                            40 + current_level * 8,
                        )
                        api_client.notify_xp_gain(
                            xp_info["gained"],
                            xp_info,
                        )

                    st.session_state.sound_event = (

                        "victory"

                        if (
                            st.session_state.last_result
                            and current_level == 15
                        )

                        else "correct"

                        if st.session_state.last_result

                        else "wrong"
                    )


                    st.rerun()


            # ====================================================
            # RESULT
            # ====================================================

            if st.session_state.answered:

                correct_index = (
                    current_question["correct"]
                )


                if st.session_state.last_result:

                    st.markdown(
                        f'<div class="result-box good">'

                        f'<div class="result-title">'
                        'Correct answer locked.'
                        '</div>'

                        f'<div class="result-detail">'
                        'You banked '
                        f'{html.escape(PRIZES[current_level - 1])}. '
                        'The next tier is ready.'
                        '</div>'

                        '</div>',

                        unsafe_allow_html=True,
                    )


                    if current_level < 15:

                        if st.button(
                            f"Continue to question "
                            f"{current_level + 1:02d}  →",

                            type="primary",

                            use_container_width=True,
                        ):

                            st.session_state.current_level += 1

                            st.session_state.selected_option = (
                                None
                            )

                            st.session_state.answered = False

                            st.session_state.last_result = (
                                None
                            )

                            st.session_state.removed_options = (
                                set()
                            )

                            st.session_state.view_version += 1

                            st.rerun()


                    else:

                        if st.button(
                            "Play a new challenge",

                            type="primary",

                            use_container_width=True,
                        ):

                            new_game()


                else:

                    correct_text = (
                        current_question["options"][
                            correct_index
                        ]
                    )


                    st.markdown(
                        f'<div class="result-box bad">'

                        f'<div class="result-title">'
                        'Not quite this time.'
                        '</div>'

                        f'<div class="result-detail">'

                        'The correct answer was '

                        f'<strong>'
                        f'{OPTION_LETTERS[correct_index]}'
                        f' · '
                        f'{html.escape(correct_text)}'
                        f'</strong>. '

                        'Your best secured milestone '
                        'is the previous safe floor.'

                        '</div>'

                        '</div>',

                        unsafe_allow_html=True,
                    )


                    if st.button(
                        "Try another challenge",

                        type="primary",

                        use_container_width=True,
                    ):

                        new_game()


    # ============================================================
    # LADDER
    # ============================================================

    with ladder:

        with st.container(border=True):

            show_ladder()
