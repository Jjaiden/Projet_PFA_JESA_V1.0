"""
Home page for JESA DMAT – Digital Maturity Assessment Tool.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components import render_footer, render_header


# ==============================================================================
# ASSET PATHS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JESA_LOGO = BASE_DIR / "assets" / "logos" / "logo_jesa.png"
ENSAM_LOGO = BASE_DIR / "assets" / "logos" / "logo_ensam.png"


# ==============================================================================
# HOME PAGE
# ==============================================================================

# ------------------------------------------------------------------------------
# Institutional logos – top corners
# ------------------------------------------------------------------------------

logo_left, logo_spacer, logo_right = st.columns([1, 6, 1])

with logo_left:
    if JESA_LOGO.exists():
        st.image(str(JESA_LOGO), width=200)
    else:
        st.markdown(
            "<div style='font-weight:700; font-size:1.2rem;'>JESA</div>",
            unsafe_allow_html=True,
        )

with logo_right:
    if ENSAM_LOGO.exists():
        st.image(str(ENSAM_LOGO), width=200)
    else:
        st.markdown(
            "<div style='font-weight:700; font-size:1.2rem; text-align:right;'>"
            "ENSAM"
            "</div>",
            unsafe_allow_html=True,
        )


# ==============================================================================
# HERO – TITRE CENTRÉ
# ==============================================================================

st.markdown(
    """
    <div style="text-align: center; margin-top: 1rem; margin-bottom: 0.3rem;">
        <h1 style="
            font-size: 2.4rem;
            font-weight: 800;
            color: #1e3a5f;
            letter-spacing: 1.5px;
            margin: 0;
        ">
            DIGITAL MATURITY ASSESSMENT
        </h1>
        <p style="
            font-size: 1.1rem;
            color: #5a6c7d;
            margin-top: 0.4rem;
        ">
            Measure where you are. Decide where to go.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# DESCRIPTION
# ==============================================================================

st.markdown(
    """
    <div style="
        text-align: center;
        max-width: 900px;
        margin: 0.8rem auto 2.5rem auto;
        color: #4a5568;
        font-size: 1.05rem;
        line-height: 1.6;
    ">
        A decision-support platform for evaluating industrial plant digital maturity,
        identifying transformation gaps, and prioritizing actionable initiatives.
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# PROCESSUS HORIZONTAL – ICÔNES PRIMITIVES + PALETTE TEAL→AMBER
# ==============================================================================

# On utilise components.html pour éviter tout problème d'indentation markdown
components.html(
    """
    <style>
        .process-chain {
            display: flex;
            justify-content: center;
            align-items: stretch;
            flex-wrap: wrap;
            gap: 0;
            margin: 2.5rem 0;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        .process-step {
            display: flex;
            align-items: center;
            margin: 0.4rem 0;
        }
        .step-box {
            padding: 1.2rem 1.5rem;
            border-radius: 16px;
            text-align: center;
            min-width: 170px;
            max-width: 200px;
            position: relative;
            overflow: hidden;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            cursor: default;
        }
        .step-box:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(0,0,0,0.15) !important;
        }
        .step-orb {
            position: absolute;
            top: -12px;
            right: -12px;
            width: 52px;
            height: 52px;
            background: rgba(255,255,255,0.08);
            border-radius: 50%;
        }
        .step-icon svg {
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.08));
        }
        .step-text {
            font-weight: 700;
            font-size: 0.82rem;
            line-height: 1.35;
            color: white;
        }
        .step-arrow {
            color: #94a3b8;
            font-size: 1.5rem;
            margin: 0 0.8rem;
            font-weight: 300;
            user-select: none;
        }
        @media (max-width: 768px) {
            .process-chain { flex-direction: column; align-items: center; }
            .step-arrow { transform: rotate(90deg); margin: 0.4rem 0; }
        }
    </style>

    <div class="process-chain">

        <div class="process-step">
            <div class="step-box" style="background: linear-gradient(145deg, #0f766e 0%, #14b8a6 100%); box-shadow: 0 6px 18px rgba(15,118,110,0.18);">
                <div class="step-orb"></div>
                <div class="step-icon">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="7"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        <circle cx="11" cy="11" r="3" stroke-opacity="0.5" stroke-width="1.5"></circle>
                    </svg>
                </div>
                <div class="step-text">Assess</div>
            </div>
            <div class="step-arrow">→</div>
        </div>

        <div class="process-step">
            <div class="step-box" style="background: linear-gradient(145deg, #047857 0%, #10b981 100%); box-shadow: 0 6px 18px rgba(4,120,87,0.18);">
                <div class="step-orb"></div>
                <div class="step-icon">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                    </svg>
                </div>
                <div class="step-text">Understand</div>
            </div>
            <div class="step-arrow">→</div>
        </div>

        <div class="process-step">
            <div class="step-box" style="background: linear-gradient(145deg, #65a30d 0%, #84cc16 100%); box-shadow: 0 6px 18px rgba(101,163,13,0.18);">
                <div class="step-orb"></div>
                <div class="step-icon">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="12" y1="20" x2="12" y2="10"></line>
                        <line x1="18" y1="20" x2="18" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="16"></line>
                    </svg>
                </div>
                <div class="step-text">Prioritize</div>
            </div>
            <div class="step-arrow">→</div>
        </div>

        <div class="process-step">
            <div class="step-box" style="background: linear-gradient(145deg, #d97706 0%, #f59e0b 100%); box-shadow: 0 6px 18px rgba(217,119,6,0.18);">
                <div class="step-orb"></div>
                <div class="step-icon">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="6" cy="19" r="3"></circle>
                        <path d="M6 8v8"></path>
                        <circle cx="18" cy="5" r="3"></circle>
                        <path d="M18 8v11"></path>
                        <path d="M9 14l6-4"></path>
                    </svg>
                </div>
                <div class="step-text">Transform</div>
            </div>
        </div>

    </div>
    """,
    height=280,
)


# ==============================================================================
# MAIN CTA
# ==============================================================================

cta_left, cta_center, cta_right = st.columns([1, 2, 1])

with cta_center:
    if st.button(
        "+ START NEW ASSESSMENT",
        key="cta_button",
        use_container_width=True,
    ):
        st.switch_page("pages/2_New_Assessment.py")


# ==============================================================================
# TEAM ATTRIBUTION
# ==============================================================================

st.markdown(
    """
    <div style="
        text-align: center;
        margin-top: 0.6rem;
        margin-bottom: 0.6rem;
        color: #5a6c7d;
        font-size: 0.85rem;
    ">
        Engineering Team :
        <strong>IGOURZAL Fatima Ezzahrae</strong>
        &
        <strong>EL BALJOURI Boutayna</strong>
        <br>
        <span style="color: #94a3b8;">EE-MSEI · ENSAM Casablanca</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# FOOTER
# ==============================================================================

render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {"label": "JESA", "url": "https://www.jesagroup.com/"},
        {"label": "ENSAM Casablanca", "url": "https://ensam-casa.ma/"},
    ],
    align="center",
    compact=False,
    show_divider=True,
)