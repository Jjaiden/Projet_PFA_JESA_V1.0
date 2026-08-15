"""
Home page for JESA DMAT – Digital Maturity Assessment Tool.
"""

from pathlib import Path
import base64

import streamlit as st

from components import render_footer


# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="JESA DMAT",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# PATHS
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JESA_LOGO = BASE_DIR / "assets" / "logos" / "logo_jesa.png"
ENSAM_LOGO = BASE_DIR / "assets" / "logos" / "logo_ensam.png"


# ==============================================================================
# HELPER — LOCAL IMAGE → BASE64
# ==============================================================================

def image_to_base64(path: Path) -> str:
    """Convert a local image into a browser-safe base64 data URL."""
    if not path.exists():
        return ""

    mime_type = "image/png"

    if path.suffix.lower() in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"

    elif path.suffix.lower() == ".webp":
        mime_type = "image/webp"

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


jesa_logo_data = image_to_base64(JESA_LOGO)
ensam_logo_data = image_to_base64(ENSAM_LOGO)


# ==============================================================================
# GLOBAL PAGE CSS
# ==============================================================================

st.markdown(
    """
    <style>

    /* ==================================================================
       APP BACKGROUND
       ================================================================== */

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(
                circle at 8% 12%,
                rgba(37, 99, 235, 0.10),
                transparent 26%
            ),
            radial-gradient(
                circle at 92% 18%,
                rgba(13, 148, 136, 0.09),
                transparent 25%
            ),
            radial-gradient(
                circle at 78% 82%,
                rgba(59, 130, 246, 0.07),
                transparent 28%
            ),
            linear-gradient(
                135deg,
                #f7faff 0%,
                #f1f6fb 48%,
                #edf5f8 100%
            ) !important;
    }


    [data-testid="stAppViewContainer"] .main {
        background: transparent !important;
    }


   [data-testid="stAppViewContainer"] .main .block-container {
    max-width: 1380px !important;

    padding-top: 0.75rem !important;
    padding-bottom: 0.15rem !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
}

    /* Streamlit vertical spacing */

    [data-testid="stVerticalBlock"] {
        gap: 0.18rem !important;
    }


    /* ==================================================================
       BUTTON
       ================================================================== */

    [data-testid="stButton"] {
        display: flex;
        justify-content: center;
    }


    [data-testid="stButton"] button {
        min-height: 42px !important;

        border: none !important;
        border-radius: 10px !important;

        background:
            linear-gradient(
                100deg,
                #1557a6 0%,
                #176fc1 48%,
                #168f91 100%
            ) !important;

        color: #ffffff !important;

        box-shadow:
            0 7px 20px rgba(22, 91, 148, 0.20) !important;

        transition:
            transform 0.2s ease,
            box-shadow 0.2s ease !important;
    }


    [data-testid="stButton"] button:hover {
        transform: translateY(-2px) !important;

        box-shadow:
            0 11px 26px rgba(22, 91, 148, 0.26) !important;
    }


    [data-testid="stButton"] button p,
    [data-testid="stButton"] button span {
        color: #ffffff !important;

        font-weight: 700 !important;

        letter-spacing: 0.035em !important;
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# DYNAMIC DIGITAL BACKGROUND
# ==============================================================================

st.html(
    """
    <div class="dmat-background">

        <div class="dmat-grid"></div>

        <div class="dmat-glow glow-left"></div>
        <div class="dmat-glow glow-right"></div>

        <div class="dmat-node node-1"></div>
        <div class="dmat-node node-2"></div>
        <div class="dmat-node node-3"></div>
        <div class="dmat-node node-4"></div>
        <div class="dmat-node node-5"></div>

        <div class="dmat-orbit orbit-1"></div>
        <div class="dmat-orbit orbit-2"></div>

    </div>

    <style>

    .dmat-background {
        position: fixed;
        inset: 0;

        width: 100vw;
        height: 100vh;

        pointer-events: none;

        z-index: -10;

        overflow: hidden;
    }


    .dmat-grid {
        position: absolute;
        inset: 0;

        background-image:
            linear-gradient(
                rgba(23, 63, 105, 0.035) 1px,
                transparent 1px
            ),
            linear-gradient(
                90deg,
                rgba(23, 63, 105, 0.035) 1px,
                transparent 1px
            );

        background-size: 85px 85px;

        mask-image:
            linear-gradient(
                to bottom,
                rgba(0,0,0,0.8),
                rgba(0,0,0,0.25),
                transparent
            );
    }


    .dmat-glow {
        position: absolute;

        border-radius: 50%;

        filter: blur(8px);
    }


    .glow-left {
        width: 430px;
        height: 430px;

        left: -220px;
        top: 12%;

        background:
            radial-gradient(
                circle,
                rgba(37,99,235,0.09),
                transparent 68%
            );
    }


    .glow-right {
        width: 390px;
        height: 390px;

        right: -180px;
        top: 24%;

        background:
            radial-gradient(
                circle,
                rgba(13,148,136,0.08),
                transparent 68%
            );
    }


    .dmat-node {
        position: absolute;

        width: 7px;
        height: 7px;

        border-radius: 50%;

        opacity: 0.45;

        animation:
            dmat-pulse ease-in-out infinite;
    }


    .node-1 {
        left: 13%;
        top: 22%;

        background: #2563eb;

        box-shadow:
            0 0 0 6px rgba(37,99,235,0.08);
    }


    .node-2 {
        left: 28%;
        top: 58%;

        background: #0f8f91;

        animation-delay: 0.8s;
    }


    .node-3 {
        left: 76%;
        top: 26%;

        background: #1769aa;

        animation-delay: 1.3s;
    }


    .node-4 {
        left: 86%;
        top: 68%;

        background: #0f8f91;

        animation-delay: 2s;
    }


    .node-5 {
        left: 57%;
        top: 77%;

        background: #2563eb;

        animation-delay: 2.6s;
    }


    .dmat-orbit {
        position: absolute;

        left: 50%;
        top: 35%;

        transform: translate(-50%, -50%);

        border-radius: 50%;

        border: 1px solid rgba(23,105,170,0.07);

        animation:
            dmat-orbit 10s ease-in-out infinite;
    }


    .orbit-1 {
        width: 420px;
        height: 150px;
    }


    .orbit-2 {
        width: 280px;
        height: 100px;

        animation-delay: -5s;
    }


    @keyframes dmat-pulse {

        0%,
        100% {
            transform: scale(1);
            opacity: 0.35;
        }

        50% {
            transform: scale(1.8);
            opacity: 0.65;
        }
    }


    @keyframes dmat-orbit {

        0%,
        100% {
            transform:
                translate(-50%, -50%)
                rotate(0deg);

            opacity: 0.45;
        }

        50% {
            transform:
                translate(-50%, -50%)
                rotate(180deg);

            opacity: 0.18;
        }
    }

    </style>
    """
)

# ==============================================================================
# INSTITUTIONAL LOGOS
# ==============================================================================

# Convert the local PNG files into Base64 so they can be embedded
# directly inside the HTML rendered by Streamlit.
jesa_logo_b64 = ""
ensam_logo_b64 = ""

if JESA_LOGO.exists():
    jesa_logo_b64 = base64.b64encode(
        JESA_LOGO.read_bytes()
    ).decode("utf-8")

if ENSAM_LOGO.exists():
    ensam_logo_b64 = base64.b64encode(
        ENSAM_LOGO.read_bytes()
    ).decode("utf-8")


st.html(
    f"""
    <div class="institutional-logos">

        <!-- ==========================================================
             JESA LOGO
             ========================================================== -->

        <div class="institutional-logo institutional-logo-jesa">
            {
                f'<img src="data:image/png;base64,{jesa_logo_b64}" alt="JESA">'
                if jesa_logo_b64
                else '<span>JESA</span>'
            }
        </div>


        <!-- ==========================================================
             ENSAM LOGO
             ========================================================== -->

        <div class="institutional-logo institutional-logo-ensam">
            {
                f'<img src="data:image/png;base64,{ensam_logo_b64}" alt="ENSAM Casablanca">'
                if ensam_logo_b64
                else '<span>ENSAM Casablanca</span>'
            }
        </div>

    </div>


    <style>

    /* ==============================================================
       INSTITUTIONAL LOGOS
       ============================================================== */

    .institutional-logos {{

        position: fixed;

        /*
         * Keep the logos below the Streamlit top toolbar.
         */
        top: 4.15rem;

        left: 1.35rem;
        right: 1.35rem;

        display: flex;

        justify-content: space-between;
        align-items: flex-start;

        z-index: 50;

        pointer-events: none;
    }}


    /* ==============================================================
       LOGO CONTAINER
       ============================================================== */

    .institutional-logo {{

        display: flex;

        align-items: flex-start;

        justify-content: center;

        overflow: visible;
    }}


    /* ==============================================================
       LOGO IMAGES
       ============================================================== */

    .institutional-logo img {{

        display: block;

        width: auto;

        height: auto;

        object-fit: contain;

        filter:
            drop-shadow(
                0 2px 5px
                rgba(20, 55, 90, 0.08)
            );
    }}


    /* ==============================================================
       JESA
       ============================================================== */

    .institutional-logo-jesa img {{

        width: 105px;

        max-height: 52px;
    }}


    /* ==============================================================
       ENSAM
       ============================================================== */

    .institutional-logo-ensam img {{

        width: 105px;

        max-height: 52px;
    }}


    /* ==============================================================
       FALLBACK TEXT
       ============================================================== */

    .institutional-logo span {{

        color: #173f69;

        font-weight: 700;

        font-size: 1rem;

        white-space: nowrap;
    }}


    /* ==============================================================
       RESPONSIVE
       ============================================================== */

    @media (max-width: 900px) {{

        .institutional-logos {{

            top: 4.0rem;

            left: 1rem;
            right: 1rem;
        }}


        .institutional-logo-jesa img,
        .institutional-logo-ensam img {{

            width: 82px;

            max-height: 42px;
        }}
    }}


    </style>
    """
)
# ==============================================================================
# HERO
# ==============================================================================

st.html(
    """
    <section class="dmat-hero">

        <div class="hero-kicker">
           
        </div>


        <h1>
            </span>DIGITAL MATURITY ASSESSMENT</span>
        </h1>


        <div class="hero-slogan">
            From Insight to Industrial Impact
        </div>

    </section>


    <style>

    .dmat-hero {
        text-align: center;

        position: relative;

        margin:
            0.42rem
            auto
            0.95rem
            auto;
    }


    .hero-kicker {
        display: inline-flex;

        align-items: center;

        justify-content: center;

        width: 24px;
        height: 12px;

        border-radius: 999px;

        border:
            1px solid
            rgba(23,105,170,0.14);

        background:
            rgba(255,255,255,0.60);
    }




        box-shadow:
            0 0 0 4px
            rgba(15,157,148,0.08);
    }


    .dmat-hero h1 {
        margin:
            0.62rem
            0
            0;

        color: #102f55;

        font-size:
            clamp(
                1.80rem,
                3.0vw,
                2.65rem
            );

        font-weight: 800;

        letter-spacing: 0.050em;

        line-height: 1.08;
    }


    .dmat-hero h1 span {
        color: #1769aa;
    }


    .hero-slogan {
        margin-top: 0.62rem;

        color: #426482;

        font-size: 1.08rem;

        font-style: italic;

        font-weight: 600;

        letter-spacing: 0.012em;

        line-height: 1.35;
    }


    .hero-description {
        max-width: 680px;

        margin:
            0.28rem
            auto
            0;

        color: #66798c;

        font-size: 0.72rem;

        line-height: 1.55;
    }

    </style>
    """
)


# ==============================================================================
# DIGITAL TRANSFORMATION JOURNEY
# ==============================================================================

st.html(
    """
    <section class="journey-section">

        <div class="journey-label">
            THE DIGITAL TRANSFORMATION JOURNEY
        </div>


        <div class="journey">


            <!-- ==========================================================
                 ASSESS
                 ========================================================== -->

            <div class="journey-stage">

                <div class="stage-marker">

                    <span class="stage-number">01</span>

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >

                        <circle
                            cx="10.8"
                            cy="10.8"
                            r="6.6"
                        />

                        <line
                            x1="16"
                            y1="16"
                            x2="21"
                            y2="21"
                        />

                        <circle
                            cx="10.8"
                            cy="10.8"
                            r="2.4"
                        />

                    </svg>

                </div>


                <div class="stage-title">
                    Assess
                </div>


                <div class="stage-description">
                    Establish the current state
                </div>

            </div>


            <div class="journey-arrow">
                
            </div>


            <!-- ==========================================================
                 IDENTIFY
                 ========================================================== -->

            <div class="journey-stage">

                <div class="stage-marker">

                    <span class="stage-number">02</span>

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >

                        <path
                            d="
                                M12 3
                                L20 7
                                L20 17
                                L12 21
                                L4 17
                                L4 7
                                Z
                            "
                        />

                        <path
                            d="
                                M8 12
                                L11 15
                                L16 9
                            "
                        />

                    </svg>

                </div>


                <div class="stage-title">
                    Identify
                </div>


                <div class="stage-description">
                    Reveal transformation gaps
                </div>

            </div>


            <div class="journey-arrow">
                
            </div>


            <!-- ==========================================================
                 PRIORITIZE
                 ========================================================== -->

            <div class="journey-stage">

                <div class="stage-marker">

                    <span class="stage-number">03</span>

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >

                        <path d="M5 19V12" />

                        <path d="M12 19V7" />

                        <path d="M19 19V4" />

                        <path d="M3 21H21" />

                    </svg>

                </div>


                <div class="stage-title">
                    Prioritize
                </div>


                <div class="stage-description">
                    Focus on high-value initiatives
                </div>

            </div>


            <div class="journey-arrow">
               
            </div>


            <!-- ==========================================================
                 TRANSFORM
                 ========================================================== -->

            <div class="journey-stage">

                <div class="stage-marker">

                    <span class="stage-number">04</span>

                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.7"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >

                        <circle
                            cx="6"
                            cy="18"
                            r="2.7"
                        />

                        <circle
                            cx="18"
                            cy="6"
                            r="2.7"
                        />

                        <path d="M8 16L16 8" />

                        <path d="M6 11V6H11" />

                    </svg>

                </div>


                <div class="stage-title">
                    Transform
                </div>


                <div class="stage-description">
                    Turn priorities into action
                </div>

            </div>

        </div>

    </section>


    <style>

    .journey-section {

        max-width: 1140px;

        margin:
            2.60rem
            auto
            0.55rem;

        padding:
            0.72rem
            1.00rem
            0.78rem;

        border-radius: 20px;

        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.74),
                rgba(241,247,251,0.64)
            );

        border:
            1px solid
            rgba(27,91,145,0.09);

        box-shadow:
            0 14px 34px
            rgba(31,65,96,0.050);

        backdrop-filter: blur(12px);
    }


    .journey-label {

        text-align: center;

        color: #6c8298;

        font-size: 0.59rem;

        font-weight: 800;

        letter-spacing: 0.19em;

        text-transform: uppercase;

        margin-bottom: 0.70rem;
    }


    .journey {

        display: grid;

        grid-template-columns:
            1fr
            0.20fr
            1fr
            0.20fr
            1fr
            0.20fr
            1fr;

        align-items: center;

        position: relative;
    }


    .journey::before {

        content: "";

        position: absolute;

        left: 8%;
        right: 8%;

        top: 29px;

        height: 1px;

        background:
            linear-gradient(
                90deg,
                rgba(23,105,170,0.12),
                rgba(15,143,145,0.45),
                rgba(23,105,170,0.35),
                rgba(15,143,145,0.12)
            );

        z-index: 0;
    }


    .journey-stage {

        position: relative;

        z-index: 2;

        display: flex;

        flex-direction: column;

        align-items: center;

        text-align: center;

        min-width: 0;
    }


    .stage-marker {

        position: relative;

        width: 58px;
        height: 58px;

        display: flex;

        align-items: center;
        justify-content: center;

        border-radius: 50%;

        color: #1769aa;

        background:
            linear-gradient(
                145deg,
                #ffffff,
                #edf5f9
            );

        border:
            1.5px solid
            rgba(23,105,170,0.20);

        box-shadow:
            0 7px 18px
            rgba(25,75,115,0.085);

        transition:
            transform 0.25s ease,
            box-shadow 0.25s ease;
    }


    .stage-marker::before {

        content: "";

        position: absolute;

        inset: -6px;

        border-radius: 50%;

        border:
            1px dashed
            rgba(23,105,170,0.13);
    }


    .journey-stage:hover .stage-marker {

        transform:
            translateY(-3px)
            scale(1.035);

        box-shadow:
            0 12px 25px
            rgba(25,75,115,0.14);
    }


    .stage-marker svg {

        width: 23px;
        height: 23px;
    }


    .stage-number {

        position: absolute;

        right: -5px;
        bottom: -2px;

        display: flex;

        align-items: center;
        justify-content: center;

        width: 22px;
        height: 22px;

        border-radius: 50%;

        background:
            linear-gradient(
                135deg,
                #173f69,
                #1769aa
            );

        color: white;

        font-size: 0.48rem;

        font-weight: 800;
    }


    .stage-title {

        margin-top: 0.48rem;

        color: #173b62;

        font-size: 0.70rem;

        font-weight: 800;

        letter-spacing: 0.075em;

        text-transform: uppercase;

        line-height: 1.25;
    }


    .stage-description {

        margin-top: 0.16rem;

        color: #7b8d9d;

        font-size: 0.56rem;

        line-height: 1.45;

        min-height: 1.65em;
    }


    .journey-arrow {

        position: relative;

        z-index: 3;

        display: flex;

        align-items: center;

        justify-content: center;
    }


    .journey-arrow span {

        display: flex;

        align-items: center;

        justify-content: center;

        width: 25px;
        height: 25px;

        border-radius: 50%;

        background:
            rgba(255,255,255,0.90);

        border:
            1px solid
            rgba(23,105,170,0.12);

        color: #6b91ad;

        font-size: 0.86rem;

        box-shadow:
            0 4px 12px
            rgba(30,70,105,0.055);
    }


    </style>
    """
)


# ==============================================================================
# CTA
# ==============================================================================

st.html(
    """
    <div class="home-cta-intro">
        &#x20;
    </div>


    <style>

.home-cta-intro {
    text-align: center;

    margin:
        2.3rem
        auto
        0.60rem;

    color: #6b8093;
    font-size: 0.67rem;
    letter-spacing: 0.018em;
    line-height: 1.45;

    }

    </style>
    """
)


cta_left, cta_center, cta_right = st.columns(
    [1.9, 2.35, 1.9]
)


with cta_center:

    if st.button(
        "◆  START NEW ASSESSMENT",
        key="cta_button",
        use_container_width=True,
        type="primary",
    ):

        st.switch_page(
            "pages/2_New_Assessment.py"
        )


# ==============================================================================
# TEAM
# ==============================================================================

st.html(
    """
    <div class="team-credit">

        <div>
            Engineering Team :
            <strong>IGOURZAL Fatima Ezzahrae</strong>
            &
            <strong>EL BALJOURI Boutayna</strong>
        </div>


        <div class="team-school">
            EE-MSEI · ENSAM Casablanca
        </div>

    </div>


    <style>

.team-credit {
    text-align: center;

    margin:
        0.60rem
        auto
        0;

    color: #718396;

    font-size: 1.2rem;

    font-size: 0.60rem;

    }


    .team-credit strong {

        color: #365979;

        font-weight: 700;
    }


    .team-school {

        color: #8a9aaa;

        font-size: 0.58rem;

        margin-top: 0.08rem;
    }

    </style>
    """
)


# ==============================================================================
# FOOTER
# ==============================================================================

# Small reduction of the gap immediately before the footer.
st.html(
    """
    <style>

    /* Keep the footer visually closer to the engineering team. */
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-bottom: 1rem !important;
    }

    </style>
    """
)


render_footer(
    product_name="JESA DMAT",
    version="v1.0.0",
    organization="JESA · ENSAM Casablanca",
    tagline="Internship Project · Digital Transformation & Industry 5.0",
    links=[
        {
            "label": "JESA",
            "url": "https://www.jesagroup.com/",
        },
        {
            "label": "ENSAM Casablanca",
            "url": "https://ensam-casa.ma/",
        },
    ],
    align="center",
    compact=True,
    show_divider=True,
)