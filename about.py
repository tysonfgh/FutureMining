"""About page — developers, faculty guide, and contributors.

All visible content lives in ABOUT_CONTENT below: swap the placeholder
names/roles for the real ones in a single place.
"""

from __future__ import annotations

import html as _html

import streamlit as st


# ============================================================
# CONTENT — sourced from README.md (team + mentorship).
# ============================================================

ABOUT_CONTENT = {
    "professor": {
        "eyebrow": "Under the guidance of",
        "name": "Dr. Lingampally Sai Vinay",
        "title": "Associate Professor · Department of Mining Engineering",
        "quote": (
            "Project Conception, Supervision, "
            "Technical Guidance & Continuous Motivation"
        ),
        "linkedin": (
            "https://www.linkedin.com/in/"
            "dr-lingampally-sai-vinay-110638118/"
        ),
    },
    "developers": [
        {
            "name": "Sayandeep Guin",
            "headline": "Lead Product Architect",
            "role": "Core Product · Game Logic · NLP Engineering · Data Integrity",
            "linkedin": (
                "https://www.linkedin.com/in/"
                "sayandeep-guin-041576356/"
            ),
            "contributions": [
                "Architected the end-to-end technical foundation, "
                "game architecture & interactive state management",
                "Designed the Streamlit UI/UX, responsive styling "
                "& theme system",
                "Co-developed the KBC game mode with Sabuj — game "
                "engine, lifelines & show experience",
                "Implemented light mode and created the login page, "
                "Remember Me & About sections",
                "Engineered the OCR + Regex pipeline extracting "
                "GATE Mining PDFs into structured CSV datasets",
                "Co-developed the NLP difficulty pipeline "
                "(TF-IDF, Gunning Fog, Ridge) → 15-tier matrix",
                "Built automated database integrity audits "
                "(integrity_check.py) & dataset validation",
            ],
        },
        {
            "name": "Sabuj Kishore Mondal",
            "headline": "Product & Simulation Engineer",
            "role": "Core Product · Game Logic · NLP Engineering",
            "linkedin": (
                "https://www.linkedin.com/in/sabuj-m-392855381/"
            ),
            "contributions": [
                "Co-architected the technical foundation, "
                "UI components & state synchronization",
                "Co-developed the KBC game mode with Sayandeep — "
                "game engine, lifelines & show experience",
                "Built the ExamGoal exam-simulation engine, "
                "timed mock tests & color-coded status palette",
                "Engineered the procedural in-memory audio "
                "synthesizer — zero external audio assets",
                "Co-developed the PDF-to-CSV pipeline & NLP "
                "feature engineering for difficulty classification",
            ],
        },
        {
            "name": "Sagar Pal",
            "headline": "Database Architect",
            "role": "Database Architecture",
            "linkedin": (
                "https://www.linkedin.com/in/sagar-pal-681912383/"
            ),
            "contributions": [
                "Designed the relational schema for questions, "
                "categories, attempts & test sessions",
                "Architected Supabase PostgreSQL clustering, "
                "connection pooling & live cloud synchronization",
                "Managed data migrations & release-time "
                "schema updates",
            ],
        },
        {
            "name": "Arpita Sengupta",
            "headline": "Backend Architect",
            "role": "Backend Architecture & APIs",
            "linkedin": (
                "https://www.linkedin.com/in/"
                "arpita-sengupta-4085913ab/"
            ),
            "contributions": [
                "Engineered high-performance FastAPI REST services "
                "with Pydantic validation & SQLAlchemy ORM",
                "Designed the resilient 3-tier failover routing: "
                "FastAPI → Supabase Direct → Offline CSV",
                "Built salted authentication, session management, "
                "review moderation endpoints & Render deployment",
            ],
        },
    ],
    # The README names no associate contributors — fill this in from
    # the project PDF if needed; the line hides itself while empty.
    "associates": [],
    "project_heading": "What is FutureMining?",
    "project_lines": [
        "FutureMining turns GATE Mining Engineering preparation into a "
        "thrilling Kaun Banega Crorepati-style knowledge challenge — climb "
        "the 15-tier depth ladder, secure milestone safe havens, and strike "
        "gold with every correct answer.",
        "Practice topic-wise, battle through timed mock tests with official "
        "GATE marking, revisit flagged questions in the review queue, and "
        "track mastery on the analytics dashboard — all calibrated by an "
        "NLP difficulty pipeline.",
    ],
}


# ============================================================
# PALETTES
# ============================================================

_DARK = {
    "HERO_BG": "linear-gradient(115deg, #0e1533 0%, #1d1445 48%, #3d1633 100%)",
    "HERO_BORDER": "rgba(232, 173, 85, .55)",
    "HERO_TITLE": "#fff9ef",
    "HERO_ACCENT": "#ffd98a",
    "HERO_SUB": "#d8cfc2",
    "PILL_BG": "rgba(232, 173, 85, .13)",
    "PILL_BORDER": "rgba(232, 173, 85, .65)",
    "PILL_TEXT": "#ffe3ae",
    "PROF_BG": "linear-gradient(180deg, rgba(232, 173, 85, .13), rgba(232, 173, 85, .04))",
    "PROF_BORDER": "#e8ad55",
    "PROF_GLOW": "0 0 0 1px rgba(232, 173, 85, .35), 0 18px 55px rgba(232, 173, 85, .16)",
    "PROF_NAME": "#ffe3ae",
    "PROF_TITLE": "#cfc6b8",
    "CARD_BG": "#0f0f1e",
    "DEV_NAME": "#f7f3eb",
    "DEV_ROLE": "#a09eb2",
    "AVATAR_BG": "linear-gradient(135deg, #ffd98a, #c46a2e)",
    "AVATAR_TEXT": "#2a1503",
    "SECTION_TITLE": "#f7f3eb",
    "EYEBROW": "#78e0c3",
    "RULE": "linear-gradient(90deg, transparent, rgba(232, 173, 85, .75), transparent)",
    "BODY_TEXT": "#d9d3c5",
    "ASSOC": "#5f6476",
    "FOOT_PILL_BG": "linear-gradient(90deg, #e8ad55, #ff7a59)",
    "FOOT_PILL_TEXT": "#2a1503",
    "GHOST": "rgba(232, 173, 85, .13)",
    "GB1": "#e8ad55",
    "GB2": "#ff7a59",
    "GB3": "#78e0c3",
    "TICKER_BG": "rgba(232, 173, 85, .08)",
    "TICKER_BORDER": "rgba(232, 173, 85, .4)",
    "TICKER_TEXT": "#ffd98a",
}

_LIGHT = {
    "HERO_BG": "linear-gradient(115deg, #4a1426 0%, #7a2440 50%, #b4502e 100%)",
    "HERO_BORDER": "rgba(255, 255, 255, .35)",
    "HERO_TITLE": "#ffffff",
    "HERO_ACCENT": "#ffd98a",
    "HERO_SUB": "#ffe9d2",
    "PILL_BG": "rgba(255, 255, 255, .14)",
    "PILL_BORDER": "rgba(255, 217, 138, .85)",
    "PILL_TEXT": "#ffe9c4",
    "PROF_BG": "linear-gradient(180deg, #fffdf6, #fdf1da)",
    "PROF_BORDER": "#8a5a14",
    "PROF_GLOW": "0 0 0 4px #fffdf6, 0 0 0 6px rgba(122, 36, 64, .55), 0 18px 50px rgba(122, 36, 64, .22)",
    "PROF_NAME": "#5c1a30",
    "PROF_TITLE": "#6b5d4f",
    "CARD_BG": "#ffffff",
    "DEV_NAME": "#3d1220",
    "DEV_ROLE": "#7d7268",
    "AVATAR_BG": "linear-gradient(135deg, #7a2440, #c46a2e)",
    "AVATAR_TEXT": "#ffffff",
    "SECTION_TITLE": "#3d1220",
    "EYEBROW": "#8a5a14",
    "RULE": "linear-gradient(90deg, transparent, rgba(138, 90, 20, .65), transparent)",
    "BODY_TEXT": "#4c443c",
    "ASSOC": "#b3a48f",
    "FOOT_PILL_BG": "linear-gradient(90deg, #7a2440, #c46a2e)",
    "FOOT_PILL_TEXT": "#ffffff",
    "GHOST": "rgba(122, 36, 64, .1)",
    "GB1": "#8a5a14",
    "GB2": "#c46a2e",
    "GB3": "#0e7c66",
    "TICKER_BG": "rgba(122, 36, 64, .07)",
    "TICKER_BORDER": "rgba(138, 90, 20, .45)",
    "TICKER_TEXT": "#7a2440",
}


_CSS_TEMPLATE = """
<style>
.fm-about-wrap {
    font-family: 'Space Grotesk', sans-serif;
    max-width: 980px;
    margin: 0 auto;
    padding-bottom: 2.5rem;
}

@keyframes fm-about-rise {
    from { opacity: 0; transform: translateY(22px); }
    to { opacity: 1; transform: translateY(0); }
}

.fm-about-reveal {
    animation: fm-about-rise .7s cubic-bezier(.2, .7, .3, 1) both;
}

/* ---------- hero ---------- */

.fm-about-hero {
    background: {{HERO_BG}};
    border: 1px solid {{HERO_BORDER}};
    border-radius: 26px;
    padding: 3.2rem 2.2rem 2.6rem;
    text-align: center;
    box-shadow: 0 24px 70px rgba(0, 0, 0, .35);
    position: relative;
    overflow: hidden;
}

.fm-about-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(600px 200px at 50% -60px, rgba(255, 217, 138, .22), transparent 70%);
    pointer-events: none;
}

.fm-about-eyebrow {
    color: {{HERO_ACCENT}};
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .32em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.fm-about-title {
    color: {{HERO_TITLE}};
    font-family: 'Newsreader', serif;
    font-size: clamp(2.4rem, 5.5vw, 3.9rem);
    font-weight: 600;
    line-height: 1.05;
    margin: 0 0 .9rem;
}

.fm-about-title em {
    font-style: normal;
    color: {{HERO_ACCENT}};
}

.fm-about-sub {
    color: {{HERO_SUB}};
    font-size: 1.02rem;
    max-width: 620px;
    margin: 0 auto 1.6rem;
    line-height: 1.65;
}

.fm-about-pill {
    display: inline-block;
    background: {{PILL_BG}};
    border: 1px solid {{PILL_BORDER}};
    color: {{PILL_TEXT}};
    font-size: .85rem;
    font-weight: 700;
    letter-spacing: .04em;
    border-radius: 999px;
    padding: .55rem 1.4rem;
    box-shadow: 0 0 26px rgba(232, 173, 85, .18);
}

.fm-about-pill .fm-about-heart {
    color: #ff6b81;
}

/* ---------- sections ---------- */

.fm-about-section {
    text-align: center;
    margin: 3rem 0 1.6rem;
}

.fm-about-section-eyebrow {
    color: {{EYEBROW}};
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .3em;
    text-transform: uppercase;
    margin-bottom: .5rem;
}

.fm-about-section-title {
    color: {{SECTION_TITLE}};
    font-family: 'Newsreader', serif;
    font-size: clamp(1.7rem, 3.6vw, 2.5rem);
    font-weight: 600;
    margin: 0;
}

.fm-about-rule {
    height: 2px;
    width: min(420px, 70%);
    margin: 1.1rem auto 0;
    background: {{RULE}};
    border-radius: 2px;
}

/* ---------- professor spotlight ---------- */

.fm-about-prof {
    background: {{PROF_BG}};
    border: 2px solid {{PROF_BORDER}};
    box-shadow: {{PROF_GLOW}};
    border-radius: 24px;
    max-width: 720px;
    margin: 0 auto;
    padding: 2.4rem 2rem 2.2rem;
    text-align: center;
}

.fm-about-prof-eyebrow {
    color: {{EYEBROW}};
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .28em;
    text-transform: uppercase;
    margin-bottom: .8rem;
}

.fm-about-prof-name {
    color: {{PROF_NAME}};
    font-family: 'Newsreader', serif;
    font-size: clamp(2.1rem, 5vw, 3.3rem);
    font-weight: 600;
    line-height: 1.1;
    margin: 0 0 .6rem;
    text-shadow: 0 2px 30px rgba(232, 173, 85, .25);
}

.fm-about-prof-title {
    color: {{PROF_TITLE}};
    font-size: 1rem;
    letter-spacing: .02em;
}

/* ---------- developer cards ---------- */

.fm-about-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.4rem;
    margin-top: .4rem;
}

.fm-about-card {
    background:
        linear-gradient({{CARD_BG}}, {{CARD_BG}}) padding-box,
        conic-gradient(from 135deg, {{GB1}}, {{GB2}}, {{GB3}}, {{GB1}}) border-box;
    border: 2px solid transparent;
    border-radius: 22px;
    padding: 2.2rem 1.4rem 1.9rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform .25s ease, box-shadow .25s ease;
}

.fm-about-card:hover {
    transform: translateY(-6px);
    box-shadow:
        0 20px 48px rgba(0, 0, 0, .3),
        0 0 26px rgba(232, 173, 85, .16);
}

.fm-about-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(280px 150px at 50% -40px, rgba(255, 217, 138, .14), transparent 70%);
    pointer-events: none;
}

.fm-about-ghost {
    position: absolute;
    top: .2rem;
    right: .9rem;
    font-size: 3.4rem;
    font-weight: 700;
    line-height: 1;
    color: {{GHOST}};
    letter-spacing: -.02em;
    pointer-events: none;
}

.fm-about-dev-index {
    color: {{EYEBROW}};
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .3em;
    text-transform: uppercase;
    margin-bottom: .9rem;
    position: relative;
}

.fm-about-avatar {
    width: 86px;
    height: 86px;
    margin: 0 auto 1.1rem;
    border-radius: 50%;
    background: {{AVATAR_BG}};
    color: {{AVATAR_TEXT}};
    font-size: 1.7rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    letter-spacing: .03em;
    box-shadow:
        0 0 0 3px {{CARD_BG}},
        0 0 0 5px {{GB1}},
        0 12px 30px rgba(0, 0, 0, .3);
    transition: transform .3s ease;
    position: relative;
}

.fm-about-card:hover .fm-about-avatar {
    transform: scale(1.07);
}

.fm-about-dev-name {
    color: {{DEV_NAME}};
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0 0 .6rem;
    position: relative;
}

.fm-about-dev-role {
    display: inline-block;
    background: linear-gradient(90deg, #e8ad55, #ff9a5c);
    color: #2a1503;
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .04em;
    line-height: 1.5;
    border-radius: 999px;
    padding: .42rem 1.05rem;
    box-shadow: 0 6px 18px rgba(232, 173, 85, .3);
    position: relative;
}

/* ---------- project blurb ---------- */

.fm-about-blurb {
    color: {{BODY_TEXT}};
    font-size: 1rem;
    line-height: 1.75;
    text-align: center;
    max-width: 720px;
    margin: 0 auto;
}

.fm-about-blurb p {
    margin: 0 0 .8rem;
}

/* ---------- associates: deliberately quiet ---------- */

.fm-about-assoc {
    color: {{ASSOC}};
    font-size: .78rem;
    text-align: center;
    letter-spacing: .03em;
    margin-top: 2.6rem;
}

/* ---------- footer ---------- */

.fm-about-footer {
    text-align: center;
    margin-top: 2.2rem;
}

.fm-about-foot-pill {
    display: inline-block;
    background: {{FOOT_PILL_BG}};
    color: {{FOOT_PILL_TEXT}};
    font-size: 1.02rem;
    font-weight: 700;
    letter-spacing: .05em;
    border-radius: 999px;
    padding: .85rem 2.4rem;
    box-shadow: 0 14px 40px rgba(0, 0, 0, .3);
}

.fm-about-foot-pill .fm-about-heart {
    color: #ffd9de;
}

.fm-about-credit {
    color: {{ASSOC}};
    font-size: .75rem;
    margin-top: 1rem;
    letter-spacing: .06em;
}

/* ---------- mentor quote ---------- */

.fm-about-quote {
    color: {{PROF_NAME}};
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-size: 1.05rem;
    max-width: 560px;
    margin: 1rem auto 0;
    line-height: 1.6;
}

/* ---------- linkedin buttons ---------- */

.fm-about-linkedin {
    display: inline-block;
    margin-top: 1.1rem;
    background: #0a66c2;
    color: #ffffff !important;
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .03em;
    border-radius: 999px;
    padding: .5rem 1.35rem;
    text-decoration: none !important;
    box-shadow: 0 8px 22px rgba(10, 102, 194, .35);
    transition: transform .2s ease, box-shadow .2s ease, background .2s ease;
}

.fm-about-linkedin:hover {
    background: #084e96;
    transform: translateY(-2px);
    box-shadow: 0 12px 28px rgba(10, 102, 194, .45);
}

.fm-about-card .fm-about-linkedin {
    margin-top: .9rem;
    padding: .42rem 1.1rem;
    font-size: .76rem;
}

/* ---------- contribution expanders ---------- */

.fm-about-contrib {
    margin-top: 1rem;
    text-align: left;
}

.fm-about-contrib summary {
    cursor: pointer;
    color: {{EYEBROW}};
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .05em;
    text-align: center;
    list-style: none;
    outline: none;
}

.fm-about-contrib summary::-webkit-details-marker {
    display: none;
}

.fm-about-contrib summary:hover {
    text-decoration: underline;
}

.fm-about-contrib ul {
    margin: .7rem 0 0;
    padding-left: 1.1rem;
    color: {{DEV_ROLE}};
    font-size: .8rem;
    line-height: 1.65;
}

.fm-about-contrib li {
    margin-bottom: .45rem;
}

.fm-about-contrib summary .fm-about-arrow {
    display: inline-block;
    transition: transform .25s ease;
}

.fm-about-contrib[open] summary .fm-about-arrow {
    transform: rotate(90deg);
}

.fm-about-contrib::details-content {
    block-size: 0;
    overflow: hidden;
    transition: block-size .35s ease, content-visibility .35s ease;
    transition-behavior: allow-discrete;
}

.fm-about-contrib[open]::details-content {
    block-size: auto;
}

/* ---------- tech ticker ---------- */

@keyframes fm-about-tick {
    to { transform: translateX(-50%); }
}

.fm-about-ticker {
    margin-top: 2rem;
    overflow: hidden;
    background: {{TICKER_BG}};
    border: 1px solid {{TICKER_BORDER}};
    border-radius: 999px;
    padding: .7rem 0;
    -webkit-mask-image:
        linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
    mask-image:
        linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
}

.fm-about-ticker-track {
    display: inline-flex;
    white-space: nowrap;
    animation: fm-about-tick 26s linear infinite;
}

.fm-about-ticker:hover .fm-about-ticker-track {
    animation-play-state: paused;
}

.fm-about-ticker-track span {
    color: {{TICKER_TEXT}};
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .22em;
    padding-right: .5rem;
}

@media (prefers-reduced-motion: reduce) {
    .fm-about-card,
    .fm-about-dev-name,
    .fm-about-ticker-track,
    .fm-about-reveal {
        animation: none;
    }
}

/* ---------- smooth in-page navigation ---------- */

html,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] section {
    scroll-behavior: smooth;
}

div[id^="fm-about-"] {
    scroll-margin-top: 1rem;
}

/* ---------- hero CTA ---------- */

a.fm-about-pill {
    text-decoration: none !important;
    transition: transform .2s ease, box-shadow .2s ease;
}

a.fm-about-pill:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 34px rgba(232, 173, 85, .3);
}

.fm-about-cta {
    margin-left: .6rem;
}

/* ---------- sticky section nav ---------- */

.fm-about-nav {
    position: sticky;
    top: 0;
    z-index: 50;
    display: flex;
    justify-content: center;
    gap: .4rem;
    padding: .55rem;
    margin: 1.2rem auto 0;
    max-width: 480px;
    background: {{CARD_BG}};
    background: color-mix(in srgb, {{CARD_BG}} 86%, transparent);
    -webkit-backdrop-filter: blur(10px);
    backdrop-filter: blur(10px);
    border: 1px solid {{TICKER_BORDER}};
    border-radius: 999px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, .18);
}

.fm-about-nav a {
    color: {{DEV_ROLE}} !important;
    font-size: .82rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-decoration: none !important;
    border-radius: 999px;
    padding: .45rem 1.2rem;
    transition: background .2s ease, color .2s ease, transform .2s ease;
}

.fm-about-nav a:hover {
    background: {{FOOT_PILL_BG}};
    color: {{FOOT_PILL_TEXT}} !important;
    transform: translateY(-1px);
}

/* ---------- stats band ---------- */

.fm-about-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin-top: .4rem;
}

.fm-about-stat {
    background: {{CARD_BG}};
    border: 1px solid {{TICKER_BORDER}};
    border-radius: 18px;
    padding: 1.5rem 1rem 1.3rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform .25s ease, box-shadow .25s ease;
}

.fm-about-stat::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 3px;
    background: linear-gradient(90deg, {{GB1}}, {{GB2}});
    transform: scaleX(0);
    transform-origin: left;
    transition: transform .3s ease;
}

.fm-about-stat:hover {
    transform: translateY(-5px);
    box-shadow: 0 16px 36px rgba(0, 0, 0, .25);
}

.fm-about-stat:hover::after {
    transform: scaleX(1);
}

.fm-about-stat-num {
    font-family: 'Newsreader', serif;
    font-size: 2.4rem;
    font-weight: 600;
    color: {{SECTION_TITLE}};
    line-height: 1;
}

.fm-about-stat-num small {
    font-size: 1.3rem;
    color: {{GB1}};
}

.fm-about-stat-label {
    color: {{DEV_ROLE}};
    font-size: .78rem;
    letter-spacing: .04em;
    margin-top: .55rem;
    line-height: 1.5;
}

/* ---------- pillars ---------- */

.fm-about-pillars {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: .4rem;
}

.fm-about-pillar {
    background: {{CARD_BG}};
    border: 1px solid {{TICKER_BORDER}};
    border-radius: 18px;
    padding: 1.6rem 1.2rem 1.5rem;
    text-align: center;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}

.fm-about-pillar:hover {
    transform: translateY(-5px);
    border-color: {{GB1}};
    box-shadow: 0 16px 36px rgba(0, 0, 0, .25);
}

.fm-about-pillar-icon {
    font-size: 1.9rem;
    line-height: 1;
    margin-bottom: .8rem;
}

.fm-about-pillar-title {
    color: {{DEV_NAME}};
    font-size: 1.02rem;
    font-weight: 700;
    margin-bottom: .5rem;
}

.fm-about-pillar-text {
    color: {{DEV_ROLE}};
    font-size: .85rem;
    line-height: 1.65;
}

/* ---------- back to top ---------- */

.fm-about-top {
    position: fixed;
    right: 1.4rem;
    bottom: 1.4rem;
    z-index: 60;
    width: 46px;
    height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: {{FOOT_PILL_BG}};
    color: {{FOOT_PILL_TEXT}} !important;
    font-size: 1.2rem;
    font-weight: 700;
    border-radius: 50%;
    text-decoration: none !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, .35);
    transition: transform .2s ease;
}

.fm-about-top:hover {
    transform: translateY(-3px);
}
</style>
"""


def _initials(name: str) -> str:
    parts = [p for p in str(name).split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def render_about_page(light: bool = False) -> None:
    """Render the About the Developers page (theme-aware)."""
    palette = _LIGHT if light else _DARK
    css = _CSS_TEMPLATE
    for key, val in palette.items():
        css = css.replace("{{" + key + "}}", val)
    st.markdown(css, unsafe_allow_html=True)

    content = ABOUT_CONTENT
    prof = content["professor"]
    prof_name = _html.escape(str(prof.get("name", "")))
    prof_title = _html.escape(str(prof.get("title", "")))
    prof_eyebrow = _html.escape(str(prof.get("eyebrow", "")))
    prof_quote = _html.escape(str(prof.get("quote", "")))
    prof_linkedin = _html.escape(str(prof.get("linkedin", "")))
    prof_extra = ""
    if prof_quote:
        prof_extra += (
            "<div class=\"fm-about-quote\">"
            f"\u201c{prof_quote}\u201d</div>"
        )
    if prof_linkedin:
        prof_extra += (
            f"<a class=\"fm-about-linkedin\" href=\"{prof_linkedin}\" "
            "target=\"_blank\" rel=\"noopener\">"
            "<strong>in</strong>&nbsp;&nbsp;Connect on LinkedIn</a>"
        )

    st.markdown(
        "<div class=\"fm-about-wrap\" id=\"fm-about-top\">"
        "<div class=\"fm-about-hero fm-about-reveal\">"
        "<div class=\"fm-about-eyebrow\">FutureMining · Knowledge Challenge</div>"
        "<h1 class=\"fm-about-title\">About the <em>Developers</em></h1>"
        "<div class=\"fm-about-sub\">"
        "The miners behind the mine — the team that designed, built, and "
        "polished every ladder, lamp, and gold nugget of this game."
        "</div>"
        "<span class=\"fm-about-pill\">Made with "
        "<span class=\"fm-about-heart\">♥</span> by IIESTIANS</span>"
        "<a class=\"fm-about-pill fm-about-cta\" href=\"#fm-about-team\">"
        "Meet the team \u2193</a>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<nav class=\"fm-about-nav fm-about-reveal\" style=\"animation-delay:.04s\">"
        "<a href=\"#fm-about-guide\">Guide</a>"
        "<a href=\"#fm-about-team\">Developers</a>"
        "<a href=\"#fm-about-project\">Project</a>"
        "</nav>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class=\"fm-about-section fm-about-reveal\" id=\"fm-about-guide\" style=\"animation-delay:.08s\">"
        "<div class=\"fm-about-section-eyebrow\">✦ Faculty Guide ✦</div>"
        "<h2 class=\"fm-about-section-title\">Guided to Gold</h2>"
        "<div class=\"fm-about-rule\"></div>"
        "</div>"
        "<div class=\"fm-about-prof fm-about-reveal\" style=\"animation-delay:.16s\">"
        f"<div class=\"fm-about-prof-eyebrow\">✦ {prof_eyebrow} ✦</div>"
        f"<div class=\"fm-about-prof-name\">{prof_name}</div>"
        f"<div class=\"fm-about-prof-title\">{prof_title}</div>"
        f"{prof_extra}"
        "</div>",
        unsafe_allow_html=True,
    )

    cards = []
    for i, dev in enumerate(content["developers"]):
        name = _html.escape(str(dev.get("name", "")))
        role = _html.escape(str(dev.get("role", "")))
        linkedin = _html.escape(str(dev.get("linkedin", "")))
        items = "".join(
            f"<li>{_html.escape(str(c))}</li>"
            for c in (dev.get("contributions") or [])
        )
        card_extra = ""
        if linkedin:
            card_extra += (
                f"<a class=\"fm-about-linkedin\" href=\"{linkedin}\" "
                "target=\"_blank\" rel=\"noopener\">"
                "<strong>in</strong>&nbsp;&nbsp;LinkedIn</a>"
            )
        if items:
            card_extra += (
                "<details class=\"fm-about-contrib\">"
                "<summary><span class=\"fm-about-arrow\">\u25b8</span>"
                "&nbsp; Key contributions</summary>"
                f"<ul>{items}</ul>"
                "</details>"
            )
        delay = .24 + i * .08
        num = f"{i + 1:02d}"
        headline = _html.escape(str(dev.get("headline", "")))
        cards.append(
            f"<div class=\"fm-about-card fm-about-reveal\" style=\"animation-delay:{delay:.2f}s\">"
            f"<div class=\"fm-about-ghost\">{num}</div>"
            f"<div class=\"fm-about-dev-index\">{headline}</div>"
            f"<div class=\"fm-about-avatar\">{_initials(name)}</div>"
            f"<div class=\"fm-about-dev-name\">{name}</div>"
            f"<div class=\"fm-about-dev-role\">{role}</div>"
            f"{card_extra}"
            "</div>"
        )

    st.markdown(
        "<div class=\"fm-about-section fm-about-reveal\" id=\"fm-about-team\" style=\"animation-delay:.2s\">"
        "<div class=\"fm-about-section-eyebrow\">⛏ The Core Team</div>"
        "<h2 class=\"fm-about-section-title\">Meet the Developers</h2>"
        "<div class=\"fm-about-rule\"></div>"
        "</div>"
        f"<div class=\"fm-about-grid\">{''.join(cards)}</div>"
        "<div class=\"fm-about-ticker fm-about-reveal\" style=\"animation-delay:.5s\">"
        "<div class=\"fm-about-ticker-track\">"
        "<span>KBC GAME ENGINE \u2726 15-TIER LADDER \u2726 NLP DIFFICULTY PIPELINE "
        "\u2726 FASTAPI BACKEND \u2726 SUPABASE POSTGRESQL \u2726 EXAMGOAL MOCKS "
        "\u2726 ANALYTICS DASHBOARD \u2726&nbsp;</span>"
        "<span aria-hidden=\"true\">KBC GAME ENGINE \u2726 15-TIER LADDER \u2726 NLP "
        "DIFFICULTY PIPELINE \u2726 FASTAPI BACKEND \u2726 SUPABASE POSTGRESQL "
        "\u2726 EXAMGOAL MOCKS \u2726 ANALYTICS DASHBOARD \u2726&nbsp;</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class=\"fm-about-section fm-about-reveal\" style=\"animation-delay:.56s\">"
        "<div class=\"fm-about-section-eyebrow\">✦ By the Numbers</div>"
        "<h2 class=\"fm-about-section-title\">The Platform in Figures</h2>"
        "<div class=\"fm-about-rule\"></div>"
        "</div>"
        "<div class=\"fm-about-stats\">"
        "<div class=\"fm-about-stat fm-about-reveal\" style=\"animation-delay:.6s\">"
        "<div class=\"fm-about-stat-num\">15</div>"
        "<div class=\"fm-about-stat-label\">Difficulty tiers,<br>NLP-calibrated</div>"
        "</div>"
        "<div class=\"fm-about-stat fm-about-reveal\" style=\"animation-delay:.66s\">"
        "<div class=\"fm-about-stat-num\">800<small>+</small></div>"
        "<div class=\"fm-about-stat-label\">ML-classified<br>questions</div>"
        "</div>"
        "<div class=\"fm-about-stat fm-about-reveal\" style=\"animation-delay:.72s\">"
        "<div class=\"fm-about-stat-num\">4</div>"
        "<div class=\"fm-about-stat-label\">Game lifelines<br>&amp; counting</div>"
        "</div>"
        "<div class=\"fm-about-stat fm-about-reveal\" style=\"animation-delay:.78s\">"
        "<div class=\"fm-about-stat-num\">3</div>"
        "<div class=\"fm-about-stat-label\">Tier resilient<br>architecture</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class=\"fm-about-section fm-about-reveal\" style=\"animation-delay:.84s\">"
        "<div class=\"fm-about-section-eyebrow\">✦ What We Stand For</div>"
        "<h2 class=\"fm-about-section-title\">Why It Works</h2>"
        "<div class=\"fm-about-rule\"></div>"
        "</div>"
        "<div class=\"fm-about-pillars\">"
        "<div class=\"fm-about-pillar fm-about-reveal\" style=\"animation-delay:.88s\">"
        "<div class=\"fm-about-pillar-icon\">\u26cf</div>"
        "<div class=\"fm-about-pillar-title\">Play to Learn</div>"
        "<div class=\"fm-about-pillar-text\">"
        "A high-stakes KBC-style show format with lifelines, "
        "milestones &amp; fanfare.</div>"
        "</div>"
        "<div class=\"fm-about-pillar fm-about-reveal\" style=\"animation-delay:.94s\">"
        "<div class=\"fm-about-pillar-icon\">\U0001f3af</div>"
        "<div class=\"fm-about-pillar-title\">True GATE Pattern</div>"
        "<div class=\"fm-about-pillar-text\">"
        "Official marking (+1.0 / \u22120.33), timed mocks &amp; a "
        "color-coded palette.</div>"
        "</div>"
        "<div class=\"fm-about-pillar fm-about-reveal\" style=\"animation-delay:1s\">"
        "<div class=\"fm-about-pillar-icon\">\U0001f6e1</div>"
        "<div class=\"fm-about-pillar-title\">Always Online</div>"
        "<div class=\"fm-about-pillar-text\">"
        "FastAPI \u2192 Supabase \u2192 offline CSV: automatic failover, "
        "zero downtime.</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    blurb_paras = "".join(
        f"<p>{_html.escape(str(line))}</p>"
        for line in content["project_lines"]
    )
    heading = _html.escape(str(content["project_heading"]))
    st.markdown(
        "<div class=\"fm-about-section fm-about-reveal\" id=\"fm-about-project\" style=\"animation-delay:.3s\">"
        "<div class=\"fm-about-section-eyebrow\">✦ The Project</div>"
        f"<h2 class=\"fm-about-section-title\">{heading}</h2>"
        "<div class=\"fm-about-rule\"></div>"
        "</div>"
        f"<div class=\"fm-about-blurb fm-about-reveal\" style=\"animation-delay:.36s\">{blurb_paras}</div>",
        unsafe_allow_html=True,
    )

    assoc_names = content["associates"] or []
    assoc_html = ""
    if assoc_names:
        assoc = ", ".join(
            _html.escape(str(a)) for a in assoc_names
        )
        assoc_html = (
            "<div class=\"fm-about-assoc\">"
            f"Associate contributors · {assoc}</div>"
        )
    st.markdown(
        f"{assoc_html}"
        "<div class=\"fm-about-footer fm-about-reveal\" style=\"animation-delay:.42s\">"
        "<span class=\"fm-about-foot-pill\">Made with "
        "<span class=\"fm-about-heart\">♥</span> by IIESTIANS</span>"
        "<div class=\"fm-about-credit\">FUTUREMINING · IIEST SHIBPUR</div>"
        "</div>"
        "<a class=\"fm-about-top\" href=\"#fm-about-top\" title=\"Back to top\">\u2191</a>"
        "</div>",
        unsafe_allow_html=True,
    )
