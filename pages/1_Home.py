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
# BACKGROUND DYNAMIQUE — RÉSEAU CONNECTÉ 100% CSS
# ==============================================================================

st.markdown(
    '<style>'
    '[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#e8edf5 0%,#f0f4f8 50%,#e4eaf3 100%) !important;}'
    '[data-testid="stAppViewContainer"] .main{background:transparent !important;}'
    '[data-testid="stAppViewContainer"] .main .block-container{background:transparent !important;padding-top:1rem;}'
    'button[kind="primary"]{color:white !important;font-weight:600 !important;}'
    'button[kind="secondary"]{color:white !important;font-weight:600 !important;}'
    '[data-testid="stButton"] button p{font-size:1rem !important;color:white !important;font-weight:600 !important;}'
    '</style>'
    '<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;overflow:hidden;">'
    '<div style="position:absolute;top:15%;left:-50%;width:200%;height:1px;background:linear-gradient(90deg,transparent,rgba(30,58,95,0.18),transparent);animation:gh 14s linear infinite;"></div>'
    '<div style="position:absolute;top:32%;left:-50%;width:200%;height:1px;background:linear-gradient(90deg,transparent,rgba(15,118,110,0.14),transparent);animation:gh 18s linear infinite;animation-delay:-4s;"></div>'
    '<div style="position:absolute;top:55%;left:-50%;width:200%;height:1px;background:linear-gradient(90deg,transparent,rgba(30,58,95,0.16),transparent);animation:gh 16s linear infinite;animation-delay:-9s;"></div>'
    '<div style="position:absolute;top:72%;left:-50%;width:200%;height:1px;background:linear-gradient(90deg,transparent,rgba(217,119,6,0.12),transparent);animation:gh 20s linear infinite;animation-delay:-2s;"></div>'
    '<div style="position:absolute;top:88%;left:-50%;width:200%;height:1px;background:linear-gradient(90deg,transparent,rgba(15,118,110,0.13),transparent);animation:gh 17s linear infinite;animation-delay:-7s;"></div>'
    '<div style="position:absolute;left:12%;top:-50%;width:1px;height:200%;background:linear-gradient(180deg,transparent,rgba(30,58,95,0.15),transparent);animation:gv 15s linear infinite;"></div>'
    '<div style="position:absolute;left:28%;top:-50%;width:1px;height:200%;background:linear-gradient(180deg,transparent,rgba(15,118,110,0.12),transparent);animation:gv 19s linear infinite;animation-delay:-5s;"></div>'
    '<div style="position:absolute;left:48%;top:-50%;width:1px;height:200%;background:linear-gradient(180deg,transparent,rgba(30,58,95,0.14),transparent);animation:gv 16s linear infinite;animation-delay:-11s;"></div>'
    '<div style="position:absolute;left:68%;top:-50%;width:1px;height:200%;background:linear-gradient(180deg,transparent,rgba(217,119,6,0.10),transparent);animation:gv 21s linear infinite;animation-delay:-3s;"></div>'
    '<div style="position:absolute;left:85%;top:-50%;width:1px;height:200%;background:linear-gradient(180deg,transparent,rgba(15,118,110,0.11),transparent);animation:gv 18s linear infinite;animation-delay:-8s;"></div>'
    '<div style="position:absolute;top:15%;left:12%;width:10px;height:10px;border-radius:50%;background:rgba(30,58,95,0.35);box-shadow:0 0 0 0 rgba(30,58,95,0.35);animation:np 3s infinite;"></div>'
    '<div style="position:absolute;top:32%;left:28%;width:8px;height:8px;border-radius:50%;background:rgba(15,118,110,0.35);box-shadow:0 0 0 0 rgba(15,118,110,0.35);animation:np 3.5s infinite;animation-delay:0.5s;"></div>'
    '<div style="position:absolute;top:55%;left:48%;width:12px;height:12px;border-radius:50%;background:rgba(30,58,95,0.30);box-shadow:0 0 0 0 rgba(30,58,95,0.30);animation:np 4s infinite;animation-delay:1s;"></div>'
    '<div style="position:absolute;top:72%;left:68%;width:9px;height:9px;border-radius:50%;background:rgba(217,119,6,0.30);box-shadow:0 0 0 0 rgba(217,119,6,0.30);animation:np 3.2s infinite;animation-delay:1.5s;"></div>'
    '<div style="position:absolute;top:88%;left:85%;width:7px;height:7px;border-radius:50%;background:rgba(15,118,110,0.30);box-shadow:0 0 0 0 rgba(15,118,110,0.30);animation:np 3.8s infinite;animation-delay:2s;"></div>'
    '<div style="position:absolute;top:22%;left:75%;width:10px;height:10px;border-radius:50%;background:rgba(30,58,95,0.25);box-shadow:0 0 0 0 rgba(30,58,95,0.25);animation:np 4.2s infinite;animation-delay:0.8s;"></div>'
    '<div style="position:absolute;top:65%;left:22%;width:8px;height:8px;border-radius:50%;background:rgba(217,119,6,0.25);box-shadow:0 0 0 0 rgba(217,119,6,0.25);animation:np 3.6s infinite;animation-delay:1.2s;"></div>'
    '<div style="position:absolute;top:42%;left:58%;width:11px;height:11px;border-radius:50%;background:rgba(15,118,110,0.28);box-shadow:0 0 0 0 rgba(15,118,110,0.28);animation:np 4.5s infinite;animation-delay:2.5s;"></div>'
    '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:60px;height:60px;border-radius:50%;border:1px solid rgba(30,58,95,0.08);animation:nc 6s ease-in-out infinite;"></div>'
    '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:30px;height:30px;border-radius:50%;border:1px solid rgba(30,58,95,0.12);animation:nc 6s ease-in-out infinite;animation-delay:-3s;"></div>'
    '<div style="position:absolute;top:15%;left:12%;width:4px;height:4px;border-radius:50%;background:#1e3a5f;opacity:0.6;animation:pk1 8s linear infinite;"></div>'
    '<div style="position:absolute;top:32%;left:28%;width:4px;height:4px;border-radius:50%;background:#0f766e;opacity:0.5;animation:pk2 10s linear infinite;"></div>'
    '<div style="position:absolute;top:55%;left:48%;width:4px;height:4px;border-radius:50%;background:#d97706;opacity:0.5;animation:pk3 9s linear infinite;"></div>'
    '<div style="position:absolute;top:72%;left:68%;width:4px;height:4px;border-radius:50%;background:#1e3a5f;opacity:0.4;animation:pk4 11s linear infinite;"></div>'
    '</div>'
    '<style>'
    '@keyframes gh{0%{transform:translateX(-25%);}100%{transform:translateX(25%);}}'
    '@keyframes gv{0%{transform:translateY(-25%);}100%{transform:translateY(25%);}}'
    '@keyframes np{0%{box-shadow:0 0 0 0 rgba(30,58,95,0.35);}70%{box-shadow:0 0 0 12px rgba(30,58,95,0);}100%{box-shadow:0 0 0 0 rgba(30,58,95,0);}}'
    '@keyframes nc{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.6;}50%{transform:translate(-50%,-50%) scale(1.3);opacity:0.2;}}'
    '@keyframes pk1{0%{top:15%;left:12%;opacity:0;}10%{opacity:0.6;}90%{opacity:0.6;}100%{top:55%;left:48%;opacity:0;}}'
    '@keyframes pk2{0%{top:32%;left:28%;opacity:0;}10%{opacity:0.5;}90%{opacity:0.5;}100%{top:72%;left:68%;opacity:0;}}'
    '@keyframes pk3{0%{top:55%;left:48%;opacity:0;}10%{opacity:0.5;}90%{opacity:0.5;}100%{top:88%;left:85%;opacity:0;}}'
    '@keyframes pk4{0%{top:72%;left:68%;opacity:0;}10%{opacity:0.4;}90%{opacity:0.4;}100%{top:15%;left:12%;opacity:0;}}'
    '</style>',
    unsafe_allow_html=True,
)

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
        st.markdown("<div style='font-weight:700;font-size:1.2rem;'>JESA</div>", unsafe_allow_html=True)

with logo_right:
    if ENSAM_LOGO.exists():
        st.image(str(ENSAM_LOGO), width=200)
    else:
        st.markdown("<div style='font-weight:700;font-size:1.2rem;text-align:right;'>ENSAM</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# HERO – TITRE CENTRÉ
# ------------------------------------------------------------------------------

st.markdown(
    '<div style="text-align:center;margin-top:1.5rem;margin-bottom:0.3rem;">'
    '<h1 style="font-size:2.6rem;font-weight:800;color:#1e3a5f;letter-spacing:1.5px;margin:0;">'
    'DIGITAL MATURITY ASSESSMENT'
    '</h1>'
    '<p style="font-size:1.15rem;color:#4a6582;margin-top:0.5rem;font-weight:500;">'
    'From Insight to Industrial Impact'
    '</p>'
    '</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# DESCRIPTION — PLUS D'ESPACE EN BAS
# ------------------------------------------------------------------------------

st.markdown(
    '<div style="text-align:center;max-width:850px;margin:1rem auto 4rem auto;color:#4a5568;font-size:1.05rem;line-height:1.7;">'
    ''
    '</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# PROCESSUS HORIZONTAL — BOXS PLUS PETITES
# ------------------------------------------------------------------------------

step_data = [
    {
        "gradient": "linear-gradient(145deg, #0f766e 0%, #14b8a6 100%)",
        "shadow": "rgba(15,118,110,0.18)",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><circle cx="11" cy="11" r="3" stroke-opacity="0.5" stroke-width="1.5"></circle></svg>',
        "text": "Assess",
    },
    {
        "gradient": "linear-gradient(145deg, #047857 0%, #10b981 100%)",
        "shadow": "rgba(4,120,87,0.18)",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
        "text": "Identify",
    },
    {
        "gradient": "linear-gradient(145deg, #65a30d 0%, #84cc16 100%)",
        "shadow": "rgba(101,163,13,0.18)",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>',
        "text": "Prioritize",
    },
    {
        "gradient": "linear-gradient(145deg, #d97706 0%, #f59e0b 100%)",
        "shadow": "rgba(217,119,6,0.18)",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="19" r="3"></circle><path d="M6 8v8"></path><circle cx="18" cy="5" r="3"></circle><path d="M18 8v11"></path><path d="M9 14l6-4"></path></svg>',
        "text": "Transform",
    },
]

cols = st.columns([2.2, 0.35, 2.2, 0.35, 2.2, 0.35, 2.2])

for idx, step in enumerate(step_data):
    col_idx = idx * 2
    with cols[col_idx]:
        card = (
            f'<div style="background:{step["gradient"]};padding:0.6rem 0.6rem;border-radius:12px;'
            f'text-align:center;min-height:68px;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;box-shadow:0 4px 14px {step["shadow"]};'
            f'position:relative;overflow:hidden;">'
            f'<div style="position:absolute;top:-8px;right:-8px;width:32px;height:32px;'
            f'background:rgba(255,255,255,0.08);border-radius:50%;"></div>'
            f'<div style="margin-bottom:0.25rem;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.1));">'
            f'{step["icon"]}</div>'
            f'<div style="font-weight:700;font-size:0.72rem;line-height:1.1;color:white;">'
            f'{step["text"]}</div>'
            f'</div>'
        )
        st.markdown(card, unsafe_allow_html=True)

    if idx < 3:
        with cols[col_idx + 1]:
            st.markdown(
                '<div style="text-align:center;color:#94a3b8;font-size:1.2rem;font-weight:300;'
                'padding-top:1.2rem;user-select:none;">→</div>',
                unsafe_allow_html=True,
            )

# ------------------------------------------------------------------------------
# ESPACE CHAINE → BOUTON (plus large)
# ------------------------------------------------------------------------------

st.markdown('<div style="margin-top:5.5rem;"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MAIN CTA
# ------------------------------------------------------------------------------

cta_left, cta_center, cta_right = st.columns([1, 2, 1])

with cta_center:
    if st.button(
        "+ START NEW ASSESSMENT",
        key="cta_button",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/2_New_Assessment.py")

# ------------------------------------------------------------------------------
# ESPACE BOUTON → TEXTE STRATÉGIQUE (plus large)
# ------------------------------------------------------------------------------

st.markdown('<div style="margin-top:3rem;"></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TEAM ATTRIBUTION
# ------------------------------------------------------------------------------

st.markdown(
    '<div style="text-align:center;margin-top:0.8rem;margin-bottom:0.8rem;'
    'color:#5a6c7d;font-size:0.85rem;">'
    'Engineering Team : <strong>IGOURZAL Fatima Ezzahrae</strong> & '
    '<strong>EL BALJOURI Boutayna</strong><br>'
    '<span style="color:#94a3b8;">EE-MSEI · ENSAM Casablanca</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------------------

render_footer(
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