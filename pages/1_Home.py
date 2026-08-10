# pages/1_Home.py

"""
Home page for JESA DMAT – Digital Maturity Assessment Tool.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

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

with st.container():

    # --------------------------------------------------------------------------
    # Industrial digital background
    # --------------------------------------------------------------------------

    st.markdown(
        '<div class="home-background">',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # Institutional logos
    # --------------------------------------------------------------------------

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        logo_col1, logo_col2 = st.columns(2)

        with logo_col1:
            if JESA_LOGO.exists():
                st.image(
                    str(JESA_LOGO),
                    width=100,
                )
            else:
                st.markdown(
                    "<strong>JESA</strong>",
                    unsafe_allow_html=True,
                )

        with logo_col2:
            if ENSAM_LOGO.exists():
                st.image(
                    str(ENSAM_LOGO),
                    width=100,
                )
            else:
                st.markdown(
                    "<strong>ENSAM Casablanca</strong>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            """
            <div class="logo-caption">
                JESA × ENSAM Casablanca
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # Hero
    # --------------------------------------------------------------------------

    render_header(
        title="DIGITAL MATURITY ASSESSMENT",
        subtitle="Measure where you are. Decide where to go.",
        align="center",
        compact=False,
    )

    # --------------------------------------------------------------------------
    # Description
    # --------------------------------------------------------------------------

    st.markdown(
        """
        <div class="home-description">
            A decision-support platform for evaluating industrial plant digital maturity,
            identifying transformation gaps, and prioritizing actionable initiatives.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # Transformation process
    # --------------------------------------------------------------------------

    st.markdown(
        """
        <div class="process-flow">

            <div class="step">
                Industrial plant digital maturity assessment
            </div>

            <div class="arrow-down">↓</div>

            <div class="step">
                Identify gaps
            </div>

            <div class="arrow-down">↓</div>

            <div class="step">
                Prioritize initiatives
            </div>

            <div class="arrow-down">↓</div>

            <div class="step">
                Build transformation roadmap
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # Main CTA
    # --------------------------------------------------------------------------

    cta_left, cta_center, cta_right = st.columns([1, 2, 1])

    with cta_center:

        if st.button(
            "+ START NEW ASSESSMENT",
            key="cta_button",
            use_container_width=True,
        ):
            st.switch_page(
                "pages/2_New_Assessment.py"
            )

    # --------------------------------------------------------------------------
    # Strategic transformation line
    # --------------------------------------------------------------------------

    st.markdown(
        """
        <div class="concept-line">
            <span>Assess</span>
            <span class="arrow">→</span>
            <span>Understand</span>
            <span class="arrow">→</span>
            <span>Prioritize</span>
            <span class="arrow">→</span>
            <span>Transform</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # Team attribution
    # --------------------------------------------------------------------------

st.markdown( """ <div class="team-attribution"> Engineering Team : <strong>IGOURZAL Fatima Ezzahrae</strong> & <strong>EL BALJOURI Boutayna</strong> <br> <span>EE-MSEI · ENSAM Casablanca</span> </div> """, unsafe_allow_html=True, )

    # Close background

st.markdown( "</div>",unsafe_allow_html=True,)


# ==============================================================================
# FOOTER
# ==============================================================================

render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {
            "label": "JESA",
            "url": "https://www.jesa.ma",
        },
        {
            "label": "ENSAM Casablanca",
            "url": "https://ensam-casablanca.ma",
        },
    ],
    align="center",
    compact=False,
    show_divider=True,
)