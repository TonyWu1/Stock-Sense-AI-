"""StockSense AI 2.0 — polished Streamlit UI with local draft creation.

Replace only your project's app.py with this file. Keep backend_adapter.py,
assistant_page.py, and the SQLite data/files unchanged. No paid API is required.
"""
from __future__ import annotations

from html import escape
import csv
from io import StringIO
from decimal import Decimal, ROUND_HALF_UP

import streamlit as st
from assistant_page import render_assistant_page
from backend_adapter import InventoryBackend
from visual_workflows import render_inventory_gallery, render_visual_purchase_builder, product_symbol


# -----------------------------------------------------------------------------
# APP CONFIGURATION & VISUAL DESIGN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="StockSense AI | Operations Console",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ss-navy: #0b1630;
        --ss-ink: #14243d;
        --ss-muted: #64748b;
        --ss-line: #e6edf5;
        --ss-cyan: #05b6d3;
        --ss-blue: #2563eb;
    }
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .stApp { background: #f5f8fd; color: var(--ss-ink); }
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3.5rem;
        max-width: 1450px;
    }
    h1, h2, h3 { color: #132540; letter-spacing: -.035em; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b142b 0%, #132644 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }
    [data-testid="stSidebar"] .block-container,
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 1.6rem;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #a7b9d0;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: #dce8f9;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label {
        border-radius: 11px;
        padding: 10px 12px;
        margin-bottom: 4px;
        transition: background .15s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover {
        background: rgba(255,255,255,.09);
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
        background: rgba(32, 178, 217, .17);
        outline: 1px solid rgba(45, 201, 230, .35);
    }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        color: #9fb3cc;
    }
    .ss-brand {
        display:flex; align-items:center; gap:11px;
        padding: 7px 0 20px;
    }
    .ss-brand-icon {
        height: 43px; width: 43px; display:grid; place-items:center;
        border-radius: 13px;
        background:linear-gradient(145deg,#11bfd4,#2563eb);
        color:white; font-size:23px; font-weight:800;
        box-shadow:0 7px 18px rgba(3,166,200,.23);
    }
    .ss-brand-name { font-size: 21px; font-weight: 800; color: white;
                     letter-spacing:-.045em; line-height:1.1; }
    .ss-brand-name span { color:#3bd8e9; }
    .ss-brand-note { color:#93a8c4; font-size:10px; font-weight:750;
                     letter-spacing:.16em; margin-top:5px; }
    .ss-nav-title { color:#7f97b8; font-size:10px; font-weight:800;
                    letter-spacing:.19em; margin:10px 0 9px; }
    .ss-side-foot {
        border:1px solid rgba(130,164,204,.23);
        border-radius:14px; padding:14px;
        background:rgba(255,255,255,.035); margin-top:14px;
    }
    .ss-live-dot { color:#51e2bc; font-size:12px; }
    .ss-side-title {font-size:12px; color:#eff6ff; font-weight:750;}
    .ss-side-description {font-size:11px; color:#9eb1cb;
                          margin-top:6px; line-height:1.55;}
    .ss-topline { color:#7185a3; font-size:11px; font-weight:800;
                  letter-spacing:.16em; text-transform:uppercase;
                  margin:3px 0 15px; }
    .ss-hero {
        overflow:hidden; border-radius:21px;
        background:radial-gradient(circle at 90% 8%,rgba(16,198,215,.24),transparent 37%),
                   linear-gradient(115deg,#101d3d 0%,#133c63 100%);
        box-shadow:0 16px 35px rgba(29,56,102,.12);
        min-height:207px;
        padding:29px 33px 27px;
        color:#f8fbff; margin:0 0 24px;
        position:relative;
    }
    .ss-hero:after {
        content:""; position:absolute; right:-58px; top:-92px;
        height:275px; width:275px; border:1px solid rgba(150,235,255,.18);
        border-radius:50%; pointer-events:none;
    }
    .ss-hero-kicker {font-size:10px; color:#82e3f4; font-weight:850;
                      letter-spacing:.19em; text-transform:uppercase;}
    .ss-hero h1 {font-size:clamp(29px,3vw,43px); color:#fff !important;
                 letter-spacing:-.055em; line-height:1.12;
                 margin:11px 0 10px; font-weight:820;}
    .ss-hero h1 span {color:#55ddea;}
    .ss-hero p {color:#b6cbe2; font-size:14px; line-height:1.55;
                margin:0; max-width:690px;}
    .ss-hero-meta {display:flex; flex-wrap:wrap; gap:11px; margin-top:19px;}
    .ss-hero-tag {border:1px solid rgba(196,221,246,.22);
                  background:rgba(255,255,255,.06); border-radius:100px;
                  padding:6px 11px; color:#e0f2fe; font-size:11px; font-weight:650;}
    .ss-stat {
        background:#fff; border:1px solid #e7edf5; border-radius:17px;
        padding:17px 18px 16px; min-height:142px;
        box-shadow:0 5px 20px rgba(26,54,94,.035);
        margin-bottom:10px;
    }
    .ss-stat-top {display:flex; justify-content:space-between; align-items:center;}
    .ss-stat-label {color:#64748b; font-size:12px; font-weight:700;}
    .ss-stat-icon {background:#edf6ff; color:#367ed5; border-radius:10px;
                   height:30px; width:30px; display:grid; place-items:center;
                   font-size:15px;}
    .ss-stat-number {font-weight:850; color:#132540; font-size:clamp(24px,2.2vw,33px);
                     letter-spacing:-.05em; margin-top:14px; line-height:1.1;}
    .ss-stat-foot {color:#8697af; font-size:11px; margin-top:7px;}
    .ss-stat-alert .ss-stat-icon {background:#fff2e9; color:#df803c;}
    .ss-stat-alert .ss-stat-number {color:#b75426;}
    .ss-sec-kicker {color:#2c98b3; font-size:10px; font-weight:850;
                    text-transform:uppercase; letter-spacing:.17em;}
    .ss-sec-heading {color:#18304f; font-size:19px; font-weight:800;
                     letter-spacing:-.035em; margin:3px 0 3px;}
    .ss-sec-subtitle {font-size:12px; color:#8190a5; margin:0 0 12px; line-height:1.6;}
    .ss-note {
        border-radius:10px; background:#f0f8fc; color:#35637a;
        border:1px solid #dcebf3; padding:11px 13px;
        font-size:12px; line-height:1.5; margin-top:5px;
    }
    .ss-note-warn {background:#fff8ed; color:#946027; border-color:#f9e7c7;}
    .ss-health {display:flex; align-items:center; gap:16px; padding:7px 0 12px;}
    .ss-health-ring {width:92px; height:92px; border-radius:50%;
        background:conic-gradient(#24b8b5 0 var(--health),#e8eff6 var(--health) 100%);
        display:grid; place-items:center; flex:none;}
    .ss-health-hole {width:68px; height:68px; border-radius:50%;
         background:white; display:flex; flex-direction:column;
         align-items:center; justify-content:center;}
    .ss-health-value {font-weight:850; font-size:19px; color:#163252; line-height:1.1;}
    .ss-health-label {font-size:9px; color:#8a9bb0; font-weight:700;}
    .ss-health-copy {font-size:12px; color:#70839b; line-height:1.7;}
    .ss-health-copy strong {color:#244765; font-size:13px;}
    .ss-bar-row {margin-top:10px;}
    .ss-bar-head {display:flex; justify-content:space-between; gap:10px;
                  font-size:11px; color:#556c87; margin-bottom:5px;}
    .ss-bar-head strong {font-weight:800; color:#193654;}
    .ss-bar-track {height:7px; background:#edf2f8; border-radius:12px; overflow:hidden;}
    .ss-bar-fill {height:100%; background:linear-gradient(90deg,#25bdc6,#3376e2);
                  border-radius:12px; min-width:2px;}
    .ss-lab-lead {font-size:13px; color:#64748b; line-height:1.6;
                  margin:0 0 14px;}
    .ss-lab-tip {background:#f5f8ff; border:1px solid #e5ecf8;
                 border-radius:13px; padding:14px 15px; margin-bottom:12px;}
    .ss-lab-tip-title {font-size:12px; font-weight:780; color:#203958;}
    .ss-lab-tip-copy {font-size:12px; color:#71859e; line-height:1.55;
                      margin-top:5px;}
    .ss-footnote {color:#8292a7; font-size:11px; line-height:1.6; margin-top:20px;}
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius:17px;
    }
    /* Decision Lab: force readable labels when Streamlit is using a dark theme.
       The rest of the app has a light surface, so relying on the active theme
       made text appear nearly white on white in the previous UI. */
    [data-testid="stForm"] {
        border: 1px solid #dce5f0;
        background: #ffffff !important;
        border-radius: 16px;
        padding: 18px 20px 16px;
        box-shadow: 0 5px 20px rgba(24, 50, 85, .035);
    }
    [data-testid="stForm"] [data-testid="stWidgetLabel"],
    [data-testid="stForm"] [data-testid="stWidgetLabel"] *,
    [data-testid="stForm"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stForm"] label,
    [data-testid="stForm"] label * {
        color: #273c58 !important;
        opacity: 1 !important;
    }
    [data-testid="stForm"] [data-testid="stWidgetLabel"] p {
        font-size: 13px !important;
        font-weight: 700 !important;
        line-height: 1.5 !important;
    }
    /* BaseWeb number inputs inherit dark surfaces from browser theme otherwise. */
    [data-testid="stForm"] [data-testid="stNumberInput"] [data-baseweb="input"],
    [data-testid="stForm"] [data-testid="stNumberInput"] [data-baseweb="input"] > div {
        background: #fff !important;
        border-color: #cedbeb !important;
    }
    [data-testid="stForm"] [data-testid="stNumberInput"] input {
        background: #fff !important;
        color: #142a49 !important;
        -webkit-text-fill-color: #142a49 !important;
        font-weight: 650;
    }
    [data-testid="stForm"] [data-testid="stNumberInput"] button {
        background: #edf4fc !important;
        color: #173b68 !important;
        border-color: #dce5f0 !important;
    }
    [data-testid="stForm"] [data-testid="stNumberInput"] button svg {
        fill: #173b68 !important;
    }
    [data-testid="stForm"] [data-testid="stSlider"] span,
    [data-testid="stForm"] [data-testid="stSlider"] [data-testid="stTickBar"],
    [data-testid="stForm"] [data-testid="stSlider"] [data-testid="stTickBar"] * {
        color: #516986 !important;
        opacity: 1 !important;
    }
    [data-testid="stForm"] [data-testid="stSlider"] [role="slider"] {
        background-color: #2477e1 !important;
        border-color: #2477e1 !important;
    }
    [data-testid="stForm"] [data-testid="stThumbValue"],
    [data-testid="stForm"] [data-testid="stThumbValue"] * {
        color: #1d68c4 !important;
    }
    [data-testid="stDataFrame"] {
        border:1px solid #e8edf5; border-radius:10px; overflow:hidden;
    }
    .stButton > button[kind="primary"],
    [data-testid="stFormSubmitButton"] button,
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-formSubmit"] {
        background: linear-gradient(95deg, #145ed2, #1588c9) !important;
        color: #ffffff !important;
        border: 0 !important;
        border-radius: 10px !important;
        font-weight: 750 !important;
        min-height: 44px;
        box-shadow: 0 6px 15px rgba(29, 110, 200, .12);
    }
    /* Keep primary button text readable even if form labels are dark. */
    [data-testid="stFormSubmitButton"] button *,
    button[data-testid="stBaseButton-primary"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    [data-testid="stFormSubmitButton"] button:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(95deg, #0f4da9, #106da4) !important;
    }
    /* Inventory workspace: legible regardless of Streamlit's active theme. */
    .ss-inventory-hero {
        border-radius: 20px; padding: 26px 30px;
        background: linear-gradient(115deg,#112444,#164c6b);
        border: 1px solid rgba(110,208,227,.17);
        box-shadow: 0 12px 28px rgba(19,56,89,.09);
        margin: 0 0 22px;
    }
    .ss-inventory-hero .eyebrow {
        color:#6de0ea; letter-spacing:.17em; font-size:10px; font-weight:850;
    }
    .ss-inventory-hero h1 {
        color:white !important; font-size:clamp(25px,3vw,36px);
        margin:8px 0; letter-spacing:-.045em;
    }
    .ss-inventory-hero p {
        color:#bbd6e8; font-size:13px; line-height:1.65;
        margin:0; max-width:790px;
    }
    .ss-inventory-tally {
        color:#607793; font-size:12px; padding:10px 2px 12px;
    }
    .ss-inventory-table-shell {
        background:white; border:1px solid #dfe8f3;
        border-radius:15px; overflow:hidden;
        box-shadow:0 8px 22px rgba(22,55,94,.035);
    }
    .ss-inventory-table-scroll { width:100%; overflow-x:auto; }
    .ss-inventory-table {
        border-collapse:separate; border-spacing:0;
        min-width:1050px; width:100%; color:#243a56;
        font-size:12px; background:white;
    }
    .ss-inventory-table thead th {
        background:#eef5fc; padding:14px 14px;
        white-space:nowrap; text-transform:uppercase; letter-spacing:.08em;
        font-size:10px; font-weight:800; color:#5c728d;
        border-bottom:1px solid #dce7f3; text-align:left;
    }
    .ss-inventory-table tbody td {
        border-bottom:1px solid #edf1f7; padding:13px 14px;
        vertical-align:middle; color:#435774; line-height:1.45;
    }
    .ss-inventory-table tbody tr:last-child td {border-bottom:0;}
    .ss-inventory-table tbody tr:nth-child(even) {background:#fafcff;}
    .ss-inventory-table tbody tr:hover {background:#f0f8ff;}
    .ss-inventory-table .name {color:#142b48;font-weight:780;min-width:165px;}
    .ss-inventory-table .number {font-weight:800;color:#213b5c;white-space:nowrap;}
    .ss-inventory-table .muted {color:#8395ab;}
    .ss-inventory-table .right {text-align:right;}
    .ss-inventory-pill {
        display:inline-block; white-space:nowrap; border-radius:100px;
        padding:5px 9px; font-size:10px; font-weight:800;
    }
    .ss-pill-good {color:#087c60;background:#e5f7ee;}
    .ss-pill-low {color:#9c6217;background:#fff4dc;}
    .ss-pill-out {color:#b23f3f;background:#ffeded;}
    .ss-inventory-empty {
        padding:28px;text-align:center;color:#64748b;
        border-radius:14px;border:1px dashed #d1dfec;background:white;
    }
    .ss-inventory-help {font-size:12px;color:#7e90a7;margin-top:14px;line-height:1.7;}
    /* Contrast for Inventory text/select controls, with light page backgrounds. */
    [data-testid="stTextInput"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p {
        color:#273c58 !important; opacity:1 !important; font-weight:700 !important;
    }
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background:#ffffff !important;
        color:#1f3553 !important;
        -webkit-text-fill-color:#1f3553 !important;
        border-color:#cedbec !important;
    }
    [data-testid="stSelectbox"] [data-baseweb="select"] * {
        color:#1f3553 !important;
    }
    @media (max-width: 800px) {
        .ss-inventory-hero {padding:22px;}
        .ss-inventory-table {min-width:950px;}
    }
    @media (max-width: 800px) {
        .block-container {padding-top:1rem;}
        .ss-hero {padding:24px 22px; min-height:0;}
        .ss-hero h1 {font-size:29px;}
        .ss-stat {min-height:128px;}
    }

    /* Purchase Orders — light, consistent with Dashboard and Inventory. */
    .ss-orders-hero {
        border-radius:20px; padding:27px 30px; margin-bottom:22px;
        background: radial-gradient(circle at 96% 0%,rgba(25,197,218,.24),transparent 36%),
                    linear-gradient(112deg,#10213f,#16476b);
        border:1px solid rgba(110,208,227,.2);
        box-shadow:0 12px 28px rgba(19,56,89,.09);
    }
    .ss-orders-hero .eyebrow {
        font-size:10px; font-weight:850; letter-spacing:.17em; color:#79dfea;
    }
    .ss-orders-hero h1 {
        margin:9px 0; color:#fff !important;
        font-size:clamp(27px,3vw,37px); letter-spacing:-.05em;
    }
    .ss-orders-hero p {
        margin:0; max-width:790px; color:#c6d8e9;
        font-size:13px; line-height:1.65;
    }
    .ss-orders-panel {
        background:white; border:1px solid #dfe8f3; border-radius:17px;
        padding:22px; margin-bottom:15px;
        box-shadow:0 7px 20px rgba(22,55,94,.035);
    }
    .ss-orders-panel h3 {
        color:#193250 !important; font-size:19px;
        margin:0 0 8px; letter-spacing:-.025em;
    }
    .ss-orders-copy {font-size:13px; color:#6c7f99; line-height:1.7;}
    .ss-orders-empty-mark {
        display:grid; place-items:center; width:46px; height:46px;
        border-radius:14px; color:#1b70bd; background:#e9f5ff;
        font-size:22px; margin-bottom:13px;
    }
    .ss-orders-step {
        display:flex; gap:12px; align-items:flex-start; padding:11px 0;
        border-bottom:1px solid #eef2f7;
    }
    .ss-orders-step:last-child {border-bottom:0;}
    .ss-orders-step-number {
        display:grid; place-items:center; flex:none; border-radius:9px;
        width:26px; height:26px; font-weight:800; font-size:12px;
        background:#ebf3ff; color:#235db0;
    }
    .ss-orders-step-title {color:#203a58;font-size:12px;font-weight:800;}
    .ss-orders-step-desc {color:#7b8da4;font-size:12px;line-height:1.5;margin-top:3px;}
    .ss-order-status {
        display:inline-block; border-radius:99px; padding:5px 11px;
        font-size:11px; font-weight:800; white-space:nowrap;
    }
    .ss-order-draft {color:#946217;background:#fff2d8;}
    .ss-order-approved {color:#087956;background:#e7f8ef;}
    .ss-order-other {color:#566c87;background:#edf3f9;}
    .ss-orders-table-wrap {
        overflow-x:auto; border:1px solid #dfe8f3;
        border-radius:14px; background:#fff;
    }
    .ss-orders-table {border-collapse:collapse; width:100%; min-width:640px; font-size:12px;}
    .ss-orders-table th {
        text-align:left; padding:13px 15px; background:#eef5fc;
        font-size:10px; text-transform:uppercase; letter-spacing:.09em;
        color:#57708c; border-bottom:1px solid #dde7f2;
    }
    .ss-orders-table td {padding:14px 15px; color:#3d5570; border-bottom:1px solid #edf1f7;}
    .ss-orders-table tr:last-child td {border-bottom:0;}
    .ss-orders-table tr:nth-child(even) td {background:#fbfdff;}
    .ss-orders-table .emph {color:#183453; font-weight:800;}
    .ss-orders-important {
        background:#f1f7ff;border:1px solid #d9e8fa;
        color:#365e86;border-radius:12px;padding:13px 15px;
        font-size:12px;line-height:1.65;
    }
    @media (max-width: 800px) {
        .ss-orders-hero {padding:22px;}
        .ss-orders-panel {padding:17px;}
    }

    /* Dashboard command center — scoped so Inventory & Purchase Orders stay intact. */
    .ss-command-top {display:flex;justify-content:space-between;align-items:center;
        gap:12px;flex-wrap:wrap;font-size:10px;letter-spacing:.17em;font-weight:800;
        color:#7184a0;margin:0 0 14px;}
    .ss-command-top b {color:#b4c2d4;padding:0 6px;}
    .ss-command-live {display:flex;align-items:center;gap:7px;color:#0d8b70;
        background:#e8f9f3;border:1px solid #caefe4;padding:8px 11px;
        border-radius:50px;letter-spacing:.06em;}
    .ss-command-live i {width:7px;height:7px;background:#13b981;border-radius:50%;display:block;}
    .ss-command-hero {border-radius:22px;padding:27px 28px 27px 32px;
        color:#fff;background:radial-gradient(circle at 82% 3%,rgba(11,186,213,.22),transparent 40%),
        linear-gradient(105deg,#101f3d 0%,#164265 100%);
        box-shadow:0 16px 28px rgba(17,44,77,.13);
        display:grid;grid-template-columns:minmax(0,1fr) 250px;gap:26px;align-items:center;
        position:relative;overflow:hidden;margin-bottom:17px;}
    .ss-command-hero:after {content:"";pointer-events:none;position:absolute;
        width:240px;height:240px;border:1px solid rgba(147,222,255,.13);border-radius:50%;
        top:-165px;right:140px;}
    .ss-command-eyebrow {font-size:10px;font-weight:850;letter-spacing:.19em;color:#70e6f0;}
    .ss-command-hero h1 {font-size:clamp(31px,3.2vw,44px);font-weight:850;
        line-height:1.07;letter-spacing:-.055em;margin:12px 0 11px;color:#fff !important;}
    .ss-command-hero h1 span {color:#57dfec;}
    .ss-command-hero-copy p {font-size:13px;line-height:1.65;max-width:630px;
        color:#c3d7e9;margin:0;}
    .ss-command-tags {display:flex;flex-wrap:wrap;gap:7px;margin-top:17px;}
    .ss-command-tags span {font-size:10px;color:#d3e7f7;border:1px solid rgba(196,224,247,.21);
        background:rgba(255,255,255,.06);padding:6px 10px;border-radius:50px;white-space:nowrap;}
    .ss-command-hero-aside {padding:20px;border:1px solid rgba(206,232,251,.21);
        border-radius:17px;background:rgba(255,255,255,.075);position:relative;z-index:1;}
    .ss-command-aside-label {font-size:9px;letter-spacing:.12em;font-weight:750;color:#b2d5ec;}
    .ss-command-aside-number {font-size:49px;font-weight:850;line-height:1.15;
        letter-spacing:-.07em;margin-top:10px;}
    .ss-command-aside-number span {font-size:18px;letter-spacing:0;color:#bed6e6;font-weight:500;}
    .ss-command-aside-desc {font-size:12px;color:#e6f5fe;margin-top:0;}
    .ss-command-aside-track {margin:15px 0 9px;height:7px;border-radius:30px;
        background:rgba(223,244,253,.2);overflow:hidden;}
    .ss-command-aside-track > div {height:100%;border-radius:30px;
        background:linear-gradient(90deg,#60e1e6,#ffba7a);}
    .ss-command-aside-foot {font-size:10px;color:#abc5d9;line-height:1.4;}
    .ss-command-actions-label {font-size:10px;font-weight:800;letter-spacing:.17em;
        color:#657f9c;margin:4px 0 7px;}
    .ss-command-link-action {display:flex;align-items:center;justify-content:center;
        min-height:42px;padding:8px 10px;border-radius:10px;
        background:linear-gradient(95deg,#1357ca,#1182c7);color:#fff !important;
        text-decoration:none !important;font-size:13px;font-weight:740;
        box-shadow:0 5px 13px rgba(16,100,190,.12);}
    .ss-command-link-action:hover {filter:brightness(.95);text-decoration:none !important;}
    .ss-command-section-title {display:flex;align-items:center;justify-content:space-between;
        gap:12px;flex-wrap:wrap;margin:24px 0 11px;}
    .ss-command-section-title span {font-size:10px;color:#2b91aa;
        letter-spacing:.16em;font-weight:850;}
    .ss-command-section-title small {font-size:11px;color:#7e91a8;}
    .ss-command-panel {border-radius:17px;border:1px solid #e4ecf5;
        padding:20px 21px;background:#fff;min-height:345px;margin:7px 0 12px;
        box-shadow:0 7px 25px rgba(26,55,94,.035);}
    .ss-priority-summary {display:flex;align-items:center;justify-content:space-between;
        gap:10px;flex-wrap:wrap;border-radius:9px;padding:10px 12px;margin-bottom:8px;
        background:#fff7e9;color:#9c631e;font-size:11px;}
    .ss-priority-summary span {color:#aa875a;font-size:10px;}
    .ss-priority-row {display:grid;grid-template-columns:minmax(0,1fr) auto;
        column-gap:9px;align-items:center;padding:11px 2px 12px;
        border-bottom:1px solid #edf2f8;}
    .ss-priority-row:last-child {border-bottom:0;}
    .ss-priority-name {color:#1b3555;font-size:12px;font-weight:780;line-height:1.35;}
    .ss-priority-supplier {color:#8699b0;font-size:10px;margin-top:3px;}
    .ss-priority-metrics {display:flex;align-items:center;gap:10px;}
    .ss-priority-qty {color:#253b5c;font-size:12px;font-weight:850;white-space:nowrap;}
    .ss-priority-qty small {font-size:10px;color:#8c9fb3;font-weight:600;}
    .ss-priority-pill {border-radius:50px;padding:5px 8px;font-size:10px;font-weight:800;
        min-width:64px;text-align:center;white-space:nowrap;}
    .ss-priority-danger {background:#ffedf0;color:#bf4756;}
    .ss-priority-low {background:#fff1d7;color:#a67317;}
    .ss-priority-track {grid-column:1/-1;width:100%;height:4px;
        background:#eef3f8;border-radius:12px;overflow:hidden;margin-top:9px;}
    .ss-priority-fill {height:100%;border-radius:12px;background:linear-gradient(90deg,#ee9a64,#e3c364);}
    .ss-command-health {display:flex;align-items:center;gap:18px;margin:12px 0 18px;}
    .ss-command-health-text {display:flex;flex-direction:column;gap:4px;}
    .ss-command-health-text strong {color:#183350;font-size:15px;}
    .ss-command-health-text span {font-size:12px;color:#7a8da4;line-height:1.55;}
    .ss-command-subtitle {letter-spacing:.15em;font-size:10px;font-weight:850;
        color:#718aaa;border-top:1px solid #e9eff6;padding-top:14px;}
    .ss-command-ai-strip {display:flex;align-items:center;gap:16px;
        background:linear-gradient(105deg,#e7f4fd,#f1f8ff);border:1px solid #d6e8f6;
        border-radius:14px;padding:16px 19px;margin:10px 0 27px;}
    .ss-command-ai-symbol {display:grid;place-items:center;width:42px;height:42px;flex:none;
        border-radius:12px;background:#163f69;color:#70e8f1;font-size:23px;}
    .ss-command-ai-strip strong {font-size:14px;color:#193955;}
    .ss-command-ai-strip p {font-size:11px;color:#64819b;line-height:1.55;margin:4px 0 0;}
    .ss-command-ai-label {font-size:9px;font-weight:820;letter-spacing:.07em;
        color:#3c7298;white-space:nowrap;margin-left:auto;}
    .ss-command-anchor {scroll-margin-top:80px;}
    /* Only Dashboard quick-action buttons: contrast in dark Streamlit theme. */
    button[data-testid="stBaseButton-secondary"] {border:1px solid #d9e5f2;
        color:#183c66;background:#fff;border-radius:10px;min-height:42px;font-weight:720;}
    button[data-testid="stBaseButton-secondary"] p {color:#183c66 !important;}
    button[data-testid="stBaseButton-secondary"]:hover {border-color:#51accd;
        background:#f0f9ff;}
    @media (max-width:1100px) {
        .ss-command-hero {grid-template-columns:minmax(0,1fr) 205px;gap:17px;}
        .ss-command-ai-label {display:none;}
    }
    @media (max-width:760px) {
        .ss-command-hero {grid-template-columns:1fr;padding:23px;}
        .ss-command-hero-aside {padding:14px 18px;}
        .ss-command-hero h1 {font-size:34px;}
        .ss-command-panel {padding:17px;min-height:0;}
        .ss-command-ai-strip {padding:13px;align-items:flex-start;}
        .ss-command-health {gap:12px;}
    }
    
/* ================================================================
   StockSense Premium UI v4 — a real panel-grid layout, not a banner.
   Presentation only: no changes to InventoryBackend or SQLite.
   ================================================================ */
.stApp {background: #f2f5fb !important;color: #15223a;}
[data-testid="stHeader"] {background: #f2f5fb !important;}
.block-container {max-width: 1530px !important;padding: 1.4rem 2.2rem 3rem !important;}
[data-testid="stSidebar"] {background: #ffffff !important;border-right:1px solid #e2e8f2 !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#66748c !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label {padding: 11px 12px;margin: 3px 0;color:#4c5d77 !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {background:#f0f4fc !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {background:#e9efff !important;outline:none !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p {color:#2459d2 !important;font-weight:800 !important;}
[data-testid="stSidebar"] [role="radiogroup"] label p {color:#475569 !important;font-size:14px !important;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {color:#6d7d96 !important;}
[data-testid="stSidebar"] hr {border-color:#e9eef6 !important;}
[data-testid="stSidebar"] .ss-brand-name {color:#13233c !important;}
[data-testid="stSidebar"] .ss-brand-name span {color:#3068e9 !important;}
[data-testid="stSidebar"] .ss-brand-note {color:#93a1b6 !important;}
[data-testid="stSidebar"] .ss-nav-title {color:#8b9ab2 !important;}
[data-testid="stSidebar"] .ss-side-foot {background:#f4f8ff !important;border:1px solid #e1e9f7 !important;}
[data-testid="stSidebar"] .ss-side-title {color:#193b5a !important;}
[data-testid="stSidebar"] .ss-side-description {color:#70839e !important;}
[data-testid="stSidebar"] .ss-live-dot {color:#059b80 !important;}
.ss4-shell {font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}
.ss4-heading {display:flex;justify-content:space-between;gap:16px;align-items:center;margin:6px 0 18px;}
.ss4-heading h1 {color:#111d32 !important;margin:0;font-size:34px;line-height:1.1;letter-spacing:-.055em;font-weight:820;}
.ss4-heading p {margin:7px 0 0;color:#75849c;font-size:13px;}
.ss4-state {display:inline-flex;align-items:center;gap:8px;white-space:nowrap;color:#16826c;background:#e3f5ec;border:1px solid #c9ebdb;border-radius:100px;font-size:11px;font-weight:780;padding:9px 13px;}
.ss4-state i {background:#19af8a;width:7px;height:7px;border-radius:50%;}
.ss4-metrics {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:13px;margin-bottom:14px;}
.ss4-kpi {background:white;border:1px solid #e5ebf4;border-radius:15px;padding:18px 19px;min-height:132px;box-shadow:0 4px 18px rgba(18,38,73,.03);}
.ss4-kpi-feature {background:linear-gradient(130deg,#556fee 0%,#7597f8 100%);border-color:transparent;color:white;box-shadow:0 14px 26px rgba(74,107,226,.17);}
.ss4-kpi-head {display:flex;justify-content:space-between;align-items:center;gap:9px;font-size:12px;font-weight:720;color:#65748e;}
.ss4-kpi-feature .ss4-kpi-head {color:#e7edff;}
.ss4-kpi-symbol {font-size:18px;color:#4777d9;background:#edf3ff;border-radius:9px;width:29px;height:29px;display:grid;place-items:center;}
.ss4-kpi-feature .ss4-kpi-symbol {color:white;background:rgba(255,255,255,.2);}
.ss4-kpi-value {color:#10203a;font-size:31px;font-weight:820;letter-spacing:-.055em;margin:12px 0 4px;line-height:1.12;}
.ss4-kpi-feature .ss4-kpi-value {color:white;}
.ss4-kpi-foot {color:#8290a4;font-size:11px;}
.ss4-kpi-feature .ss4-kpi-foot {color:#e1e9ff;}
.ss4-alert-number {color:#bd5b28;}
.ss4-main-grid {display:grid;grid-template-columns: .89fr 1.15fr 1.03fr;gap:13px;align-items:stretch;margin-bottom:13px;}
.ss4-card {background:#fff;border:1px solid #e5ebf4;border-radius:15px;padding:19px 20px;box-shadow:0 5px 18px rgba(18,38,73,.03);min-width:0;}
.ss4-card h2 {font-size:17px;letter-spacing:-.035em;color:#17233b;margin:0 0 5px;font-weight:810;}
.ss4-card .sub {font-size:11px;color:#8591a5;margin:0 0 17px;line-height:1.5;}
.ss4-card-top {display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:3px;}
.ss4-card-top .hint {color:#456de2;font-size:11px;font-weight:750;}
.ss4-mini-row {padding:16px 0;border-bottom:1px solid #eff2f7;}
.ss4-mini-row:last-child {border:0;}
.ss4-mini-row .label {font-size:12px;color:#77869b;}
.ss4-mini-row .value {font-size:23px;font-weight:850;letter-spacing:-.03em;color:#17243b;line-height:1.25;margin-top:4px;}
.ss4-mini-row .value.blue {color:#3b6fe5;}
.ss4-mini-row .value.amber {color:#c16b30;}
.ss4-mini-row .detail {font-size:10px;color:#99a5b7;margin-top:3px;}
.ss4-columns {display:flex;justify-content:space-around;align-items:flex-end;height:188px;gap:15px;border-bottom:1px solid #e9edf6;margin-top:24px;padding:0 4px;}
.ss4-col-wrap {flex:1;display:flex;flex-direction:column;justify-content:end;align-items:center;gap:7px;height:100%;}
.ss4-col-number {font-size:14px;font-weight:850;color:#253b5a;}
.ss4-col {width:65%;max-width:75px;border-radius:14px 14px 0 0;min-height:3px;}
.ss4-col.blue {background:linear-gradient(180deg,#7591ff,#5578ea);}
.ss4-col.aqua {background:linear-gradient(180deg,#83dbe7,#58bdd3);}
.ss4-col.purple {background:linear-gradient(180deg,#cba2f3,#a97be0);}
.ss4-col-label {font-size:11px;color:#72829a;text-align:center;margin-top:10px;}
.ss4-legend {display:flex;gap:14px;flex-wrap:wrap;margin-top:24px;font-size:11px;color:#6c7e98;}
.ss4-legend b {font-weight:800;color:#243854;}
.ss4-chip {display:inline-block;padding:5px 9px;border-radius:100px;background:#fff1e0;color:#aa6a2a;font-size:10px;font-weight:800;white-space:nowrap;}
.ss4-chip-red {background:#ffe6e7;color:#c54f5a;}
.ss4-item {display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #edf1f6;}
.ss4-item:last-child {border:0;}
.ss4-product-mark {height:48px;width:48px;display:grid;place-items:center;flex:none;background:linear-gradient(135deg,#eef5ff,#dce8fc);border-radius:12px;color:#4871d3;font-size:20px;font-weight:800;}
.ss4-item-main {flex:1;min-width:0;}
.ss4-item-main strong {color:#263a57;font-size:12px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ss4-item-main small {font-size:10px;color:#94a2b5;display:block;margin-top:4px;}
.ss4-item-right {font-size:11px;color:#5b6c83;white-space:nowrap;text-align:right;}
.ss4-item-right b {display:block;color:#ad512b;font-size:13px;margin-bottom:5px;}
.ss4-bottom-grid {display:grid;grid-template-columns:1.45fr 1fr;gap:13px;margin-bottom:14px;}
.ss4-risktable {width:100%;border-collapse:collapse;font-size:12px;}
.ss4-risktable th {text-align:left;font-size:10px;letter-spacing:.05em;color:#91a0b4;font-weight:700;padding:10px 5px;border-bottom:1px solid #e6eaf2;}
.ss4-risktable td {padding:11px 5px;color:#63758e;border-bottom:1px solid #eef1f6;}
.ss4-risktable tr:last-child td {border:0;}
.ss4-risktable .pname {font-weight:750;color:#273b59;}
.ss4-risktable .right {text-align:right;white-space:nowrap;}
.ss4-progress {height:7px;background:#edf1f8;border-radius:100px;overflow:hidden;min-width:75px;}
.ss4-progress > div {background:linear-gradient(90deg,#fa9954,#f5c56b);border-radius:100px;height:100%;}
.ss4-cta {background:linear-gradient(135deg,#142e51,#0e1c33);border-radius:13px;padding:19px;display:flex;gap:13px;margin-top:11px;align-items:center;}
.ss4-cta-icon {height:44px;width:44px;border-radius:12px;background:#2568ce;display:grid;place-items:center;color:#ddfaff;font-size:23px;flex:none;}
.ss4-cta strong {color:white;font-size:14px;}
.ss4-cta p {color:#b8c7dc;line-height:1.55;font-size:11px;margin:6px 0 0;}
.ss4-workflow-row {display:flex;align-items:center;justify-content:space-between;gap:10px;margin:17px 0;padding:12px 13px;background:#f5f8fd;border-radius:10px;}
.ss4-workflow-row .name {color:#566c89;font-size:11px;}
.ss4-workflow-row .count {color:#1b2e4b;font-weight:800;font-size:18px;}
.ss4-note {font-size:11px;color:#8392a8;line-height:1.6;margin-top:11px;}
.ss4-module-title {margin:28px 0 14px;display:flex;justify-content:space-between;gap:10px;align-items:end;}
.ss4-module-title h2 {margin:0;color:#1b2b46;font-size:22px;letter-spacing:-.045em;}
.ss4-module-title p {margin:5px 0 0;color:#8392a7;font-size:12px;}
.ss4-module-title .eyebrow {color:#4c77db;font-size:10px;font-weight:800;letter-spacing:.12em;}
.ss4-action-head {display:flex;justify-content:space-between;align-items:center;gap:12px;margin:7px 0 11px;}
.ss4-action-head h3 {color:#233953;font-weight:800;font-size:13px;margin:0;}
.ss4-disclaimer {font-size:11px;color:#8694a9;margin-top:13px;}
@media (max-width:1150px){.ss4-main-grid{grid-template-columns:1fr 1fr}.ss4-main-grid .ss4-card:last-child{grid-column:1/-1}.ss4-metrics{grid-template-columns:1fr 1fr}.ss4-bottom-grid{grid-template-columns:1fr;}}
@media (max-width:760px){.block-container{padding:1.2rem 1rem 2.3rem !important;}.ss4-main-grid{grid-template-columns:1fr}.ss4-main-grid .ss4-card:last-child{grid-column:auto}.ss4-metrics{grid-template-columns:1fr 1fr}.ss4-heading{align-items:flex-start;flex-direction:column}.ss4-heading h1{font-size:27px}.ss4-kpi{padding:14px}.ss4-kpi-value{font-size:25px}}


/* ========================================================================
   StockSense AI 2.0 — MIDNIGHT OPERATIONS THEME
   CSS-only color/presentation update to the existing Premium UI.
   NO INVENTORY OR PURCHASE ORDER BUSINESS LOGIC IS MODIFIED.
   This block appears LAST so it overrides previous light-theme styles.
   ======================================================================== */
:root {
    color-scheme: dark;
    --ss-navy: #081322;
    --ss-ink: #ecf5ff;
    --ss-muted: #a7bad1;
    --ss-line: #2a4260;
    --ss-cyan: #47d5ef;
    --ss-blue: #4d86ff;
    --ss-dark-bg: #080f1e;
    --ss-dark-card: #14243b;
    --ss-dark-card-alt: #172b45;
    --ss-dark-stroke: #29425f;
    --ss-dark-copy: #eaf4ff;
    --ss-dark-muted: #a9bed5;
}
html, body {background:#080f1e !important; color:#eaf4ff !important;}
.stApp {
    background: radial-gradient(ellipse 90% 55% at 65% 0%, #15355b 0%, #0a172a 48%, #080f1e 100%) !important;
    color:#eaf4ff !important;
}
[data-testid="stHeader"] {background:rgba(8,15,29,.96) !important;}
[data-testid="stToolbar"] {color:#a5bbd8;}
[data-testid="stDecoration"] {background:#1d77b7 !important;}
.block-container {max-width:1530px !important;}
/* Sidebar: midnight instead of light gray/white. */
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#091324 0%,#0d1d34 100%) !important;
    border-right:1px solid #29415d !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#a4b8d1 !important;}
[data-testid="stSidebar"] .ss-brand-name {color:#f2f8ff !important;}
[data-testid="stSidebar"] .ss-brand-name span {color:#4eddf4 !important;}
[data-testid="stSidebar"] .ss-brand-note,
[data-testid="stSidebar"] .ss-nav-title {color:#7fa9c9 !important;}
[data-testid="stSidebar"] [role="radiogroup"] label p {color:#bdd0e6 !important;font-size:14px !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {background:#1b3450 !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
    background:linear-gradient(90deg,#194e86,#194064) !important;
    outline:1px solid #3674aa !important;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p {color:#ffffff !important;}
[data-testid="stSidebar"] hr {border-color:#273d55 !important;}
[data-testid="stSidebar"] .ss-side-foot {background:#132944 !important;border:1px solid #284968 !important;}
[data-testid="stSidebar"] .ss-side-title {color:#ebf7ff !important;}
[data-testid="stSidebar"] .ss-side-description {color:#a8c4de !important;}
[data-testid="stSidebar"] .ss-live-dot {color:#3ae0b8 !important;}
/* Page headings and section microcopy */
h1,h2,h3,[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,[data-testid="stMarkdownContainer"] h3 {color:#f0f7ff !important;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:#a6bbd3 !important;}
.ss-topline, .ss-sec-kicker {color:#64d7f4 !important;}
.ss-sec-heading {color:#f0f7ff !important;}
.ss-sec-subtitle, .ss-footnote, .ss-inventory-help {color:#a6bbd3 !important;}
/* Dashboard grid: layered glassy navy cards, not white tiles. */
.ss4-heading h1 {color:#f3f8ff !important;font-size:38px;}
.ss4-heading p {color:#abc0d8 !important;font-size:13px;}
.ss4-state {background:#133d43 !important;border:1px solid #257e75 !important;color:#78edcb !important;}
.ss4-state i {background:#38e3b5 !important;}
.ss4-kpi {
    background:linear-gradient(160deg,#1a2f4b,#112138) !important;
    border:1px solid #2a4260 !important;
    box-shadow:0 15px 30px rgba(0,0,0,.16) !important;
}
.ss4-kpi-feature {
    background:linear-gradient(135deg,#1756bb 0%,#267ce7 58%,#1596b5 100%) !important;
    border:1px solid #4b9eef !important;
    box-shadow:0 18px 30px rgba(7,69,146,.26) !important;
}
.ss4-kpi-head {color:#b2c8dd !important;}
.ss4-kpi-feature .ss4-kpi-head {color:#e4f3ff !important;}
.ss4-kpi-symbol {background:#263f60 !important;color:#80d3ff !important;}
.ss4-kpi-feature .ss4-kpi-symbol {background:rgba(255,255,255,.16) !important;color:#fff !important;}
.ss4-kpi-value {color:#fff !important;}
.ss4-kpi-foot {color:#9eb5d0 !important;}
.ss4-kpi-feature .ss4-kpi-foot {color:#e0f1ff !important;}
.ss4-alert-number {color:#ffae73 !important;}
.ss4-card {
    background:linear-gradient(160deg,#152841,#112139) !important;
    border:1px solid #2b4565 !important;
    box-shadow:0 16px 34px rgba(0,0,0,.13) !important;
}
.ss4-card h2 {color:#f0f8ff !important;}
.ss4-card .sub, .ss4-col-label, .ss4-legend,
.ss4-mini-row .label, .ss4-mini-row .detail {color:#aabed5 !important;}
.ss4-card-top .hint, .ss4-mini-row .value.blue {color:#76c8ff !important;}
.ss4-mini-row, .ss4-item {border-bottom-color:#2b4261 !important;}
.ss4-mini-row .value, .ss4-col-number, .ss4-legend b {color:#f0f8ff !important;}
.ss4-mini-row .value.amber {color:#ffbd7e !important;}
.ss4-columns {border-bottom-color:#2e4562 !important;}
.ss4-col.blue {background:linear-gradient(180deg,#5b90ff,#2e63e5) !important;}
.ss4-col.aqua {background:linear-gradient(180deg,#78f0e4,#24b8de) !important;}
.ss4-col.purple {background:linear-gradient(180deg,#d6a5ff,#9263ea) !important;}
.ss4-chip {background:#473722 !important;color:#ffd494 !important;}
.ss4-chip-red {background:#4b2534 !important;color:#ff9cae !important;}
.ss4-product-mark {background:linear-gradient(140deg,#284c72,#1d3658) !important;color:#9cddff !important;}
.ss4-item-main strong {color:#f2f8ff !important;}
.ss4-item-main small {color:#97b2cd !important;}
.ss4-item-right {color:#a9bed5 !important;}
.ss4-item-right b {color:#ffb27c !important;}
.ss4-risktable th {color:#9bb3ce !important;border-bottom-color:#2c4561 !important;}
.ss4-risktable td {color:#adbed2 !important;border-bottom-color:#253f5a !important;}
.ss4-risktable .pname {color:#ecf6ff !important;}
.ss4-progress {background:#263c57 !important;}
.ss4-workflow-row {background:#192e47 !important;border:1px solid #294563 !important;}
.ss4-workflow-row .name {color:#b2c5db !important;}
.ss4-workflow-row .count {color:#eef7ff !important;}
.ss4-cta {background:linear-gradient(125deg,#163d64,#0a243f) !important;border:1px solid #2e618b !important;}
.ss4-cta p {color:#b7d0e6 !important;}
.ss4-module-title h2, .ss4-action-head h3 {color:#eef7ff !important;}
.ss4-module-title p, .ss4-note, .ss4-disclaimer {color:#aabed5 !important;}
.ss4-module-title .eyebrow {color:#59caec !important;}
/* Original helper cards continue on Inventory, Orders, Decision Lab. */
.ss-stat,.ss-orders-panel,.ss-inventory-table-shell,.ss-orders-table-wrap {
    background:#14263e !important;
    border:1px solid #2c4966 !important;
    box-shadow:0 12px 26px rgba(0,0,0,.13) !important;
}
.ss-stat-label,.ss-stat-foot,.ss-orders-copy {color:#a9bdd5 !important;}
.ss-stat-number,.ss-orders-panel h3 {color:#f1f8ff !important;}
.ss-stat-icon {background:#253f5f !important;color:#88d8ff !important;}
.ss-stat-alert .ss-stat-icon {background:#49312e !important;color:#ffb37c !important;}
.ss-stat-alert .ss-stat-number {color:#ffb47e !important;}
.ss-inventory-hero,.ss-orders-hero {
    background:radial-gradient(ellipse at 94% 5%,rgba(21,192,216,.23),transparent 45%),
               linear-gradient(113deg,#142745,#144c69) !important;
    border:1px solid #2e6784 !important;
}
.ss-inventory-hero p,.ss-orders-hero p {color:#bad6e9 !important;}
.ss-inventory-tally,.ss-inventory-help,.ss-inventory-table .muted {color:#a9bed6 !important;}
.ss-inventory-table,.ss-inventory-table-shell,.ss-orders-table,
.ss-orders-table-wrap {background:#14253d !important;color:#dfeefc !important;}
.ss-inventory-table thead th,.ss-orders-table th {background:#1e3856 !important;color:#a8c6e4 !important;border-color:#35516f !important;}
.ss-inventory-table tbody td,.ss-orders-table td {color:#c3d5e8 !important;border-color:#29435f !important;}
.ss-inventory-table tbody tr:nth-child(even),
.ss-inventory-table tbody tr:nth-child(even) td,
.ss-orders-table tr:nth-child(even) td {background:#192d47 !important;}
.ss-inventory-table tbody tr:hover td {background:#243e5b !important;}
.ss-inventory-table .name,.ss-inventory-table .number,
.ss-orders-table .emph {color:#f1f8ff !important;}
.ss-pill-good,.ss-order-approved {background:#143e3d !important;color:#6de6c2 !important;}
.ss-pill-low,.ss-order-draft {background:#453624 !important;color:#ffd596 !important;}
.ss-pill-out {background:#512b35 !important;color:#ffabbb !important;}
.ss-inventory-empty {background:#142841 !important;border-color:#355372 !important;color:#a6c0d8 !important;}
.ss-orders-step {border-bottom-color:#304762 !important;}
.ss-orders-step-number {background:#224c73 !important;color:#b9e4ff !important;}
.ss-orders-step-title {color:#eef8ff !important;}
.ss-orders-step-desc {color:#adc3d9 !important;}
.ss-orders-empty-mark {background:#244767 !important;color:#70cbff !important;}
.ss-order-other {background:#284259 !important;color:#bfd4e9 !important;}
.ss-orders-important,.ss-note {background:#183753 !important;border-color:#306080 !important;color:#bcdbed !important;}
.ss-note-warn {background:#3a2d26 !important;border-color:#725139 !important;color:#ffd5a4 !important;}
.ss-lab-tip {background:#182c46 !important;border:1px solid #2d4868 !important;}
.ss-lab-tip-title {color:#e8f4ff !important;}
.ss-lab-tip-copy {color:#a8c2de !important;}
.ss-health-hole {background:#14263e !important;}
.ss-health-value,.ss-health-copy strong,.ss-bar-head strong {color:#f0f7ff !important;}
.ss-health-label,.ss-health-copy,.ss-bar-head {color:#adc4dc !important;}
.ss-bar-track {background:#263e57 !important;}
/* Streamlit widgets: avoid low-contrast light mode inherited from browser. */
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#29425e !important;}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stForm"] {
    background:#12253d !important;
    border-color:#2e4969 !important;
}
[data-testid="stForm"] [data-testid="stWidgetLabel"],
[data-testid="stForm"] [data-testid="stWidgetLabel"] *,
[data-testid="stForm"] [data-testid="stMarkdownContainer"] p,
[data-testid="stForm"] label,
[data-testid="stForm"] label *,
[data-testid="stNumberInput"] [data-testid="stWidgetLabel"] p,
[data-testid="stSlider"] [data-testid="stWidgetLabel"] p,
[data-testid="stTextInput"] [data-testid="stWidgetLabel"] p,
[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p,
[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {
    color:#e9f4ff !important;opacity:1 !important;
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stForm"] [data-testid="stNumberInput"] input,
[data-testid="stForm"] [data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stForm"] [data-testid="stNumberInput"] [data-baseweb="input"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background:#1b304b !important;
    color:#f1f8ff !important;
    -webkit-text-fill-color:#f1f8ff !important;
    border-color:#385b7b !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] * {color:#f1f8ff !important;}
[data-testid="stForm"] [data-testid="stNumberInput"] button {background:#253f5d !important;color:#f1f8ff !important;border-color:#416382 !important;}
[data-testid="stForm"] [data-testid="stNumberInput"] button svg {fill:#f1f8ff !important;}
[data-testid="stForm"] [data-testid="stSlider"] span,
[data-testid="stForm"] [data-testid="stSlider"] [data-testid="stTickBar"],
[data-testid="stForm"] [data-testid="stSlider"] [data-testid="stTickBar"] * {color:#b1c9de !important;}
[data-testid="stForm"] [data-testid="stThumbValue"],
[data-testid="stForm"] [data-testid="stThumbValue"] * {color:#76dcff !important;}
[data-testid="stForm"] [data-testid="stSlider"] [role="slider"] {background:#30c0e9 !important;border-color:#30c0e9 !important;}
[data-testid="stExpander"] {background:#14263e !important;border:1px solid #2b4763 !important;border-radius:12px !important;}
[data-testid="stExpander"] * {color:#e7f2ff;}
[data-testid="stAlert"] {border-radius:12px !important;}
[data-testid="stAlert"] p {color:inherit;}
[data-testid="stDataFrame"] {border-color:#30506f !important;background:#101d30 !important;}
[data-testid="stDownloadButton"] button,
[data-testid="stButton"] button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]),
button[data-testid="stBaseButton-secondary"] {
    background:#1b3452 !important;border:1px solid #386184 !important;color:#e9f4ff !important;
    border-radius:11px !important;
}
[data-testid="stDownloadButton"] button *,
button[data-testid="stBaseButton-secondary"] * {color:#f1f8ff !important;-webkit-text-fill-color:#f1f8ff !important;}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button,
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-formSubmit"] {
    background:linear-gradient(100deg,#1b66e5,#119fca) !important;
    color:#fff !important;border:1px solid #4099e7 !important;
    box-shadow:0 7px 19px rgba(9,111,197,.24) !important;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover {filter:brightness(1.13);}
/* Make native data frames follow the midnight scheme as far as theme permits. */
[data-testid="stDataFrame"] canvas {color-scheme:dark;}
@media(max-width:1000px){.ss4-heading h1{font-size:32px;}}


    /* Business-owner workflows: dark theme, clear totals and form contrast. */
    .ss-owner-head {margin:20px 0 14px; padding:20px 24px; border-radius:16px;
        border:1px solid #315b7a; background:linear-gradient(110deg,#143657,#13263e);}
    .ss-owner-head strong {color:#eef9ff; font-size:20px; font-weight:800;}
    .ss-owner-head p {color:#b1cee3; margin:7px 0 0; font-size:13px;}
    .ss-owner-cue {border:1px solid #345a77; background:#18354e;
        padding:13px 17px; border-radius:12px; color:#d8ecfd; font-size:12px;}
    .ss-owner-cue strong {color:#75e3e8;}
    .ss-owner-amount {background:#16304a; border:1px solid #355979;
        border-radius:12px; padding:15px; color:#c0d8eb; margin:10px 0;}
    .ss-owner-amount strong {color:#fff; font-size:27px;}
    /* Make the new form's entire field labels visible on dark cards. */
    [data-testid="stMultiSelect"] [data-testid="stWidgetLabel"] p,
    [data-testid="stMultiSelect"] label p,
    [data-testid="stNumberInput"] label p,
    [data-testid="stTextInput"] label p,
    [data-testid="stCheckbox"] label p {color:#ecf5ff !important;}
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [data-baseweb="select"] input {
        background:#1b304b !important; color:#f4faff !important;
        -webkit-text-fill-color:#f4faff !important;
        border-color:#426989 !important;
    }
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {background:#225485 !important;}
    [data-testid="stForm"] [data-testid="stNumberInput"] button * {color:#fff !important;}

    /* VISUAL BUYING EXPERIENCE — shared StockSense midnight design */
    .stApp {background:#091421 !important;color:#eaf3ff !important;}
    .block-container {max-width:1510px;padding-top:1.3rem;}
    [data-testid="stSidebar"]{background:#0b192a !important;border-right:1px solid #22405e !important;}
    .ss4-heading h1{font-size:36px !important;}
    .ss4-card,.ss4-kpi,.ss-orders-panel,.ss-stat{border-radius:17px !important;}
    .v-eyebrow{font-size:10px;letter-spacing:.14em;color:#66d8ff;font-weight:850;}
    .v-section-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:20px 0 15px;}
    .v-section-head h2,.v-section-head h3{color:#eef7ff !important;margin:5px 0;font-size:21px;font-weight:800;}
    .v-section-head p{color:#a6c1dd;margin:4px 0;font-size:12px;}
    .v-mini-chip{color:#8edfff;background:#173854;border:1px solid #315a79;border-radius:99px;padding:6px 10px;font-size:10px;white-space:nowrap;}
    .v-builder-hero{margin:19px 0 19px;padding:22px 25px;border-radius:17px;background:linear-gradient(110deg,#102642,#16496b);border:1px solid #28577d;}
    .v-builder-hero h2{color:#fff !important;font-size:27px;letter-spacing:-.045em;margin:7px 0;}
    .v-builder-hero p{color:#bdd6e8;font-size:13px;line-height:1.5;max-width:690px;margin:0;}
    .v-product{min-width:0;padding:3px 1px 0;}
    .v-product-art{height:112px;border-radius:12px;display:grid;place-items:center;margin-bottom:13px;position:relative;overflow:hidden;border:1px solid rgba(155,213,255,.11);}
    .v-product-art::after{content:"";width:115px;height:115px;position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.11);top:-50px;right:-40px;}
    .v-product-art>span[role="img"]{font-size:55px;line-height:1;filter:drop-shadow(0 10px 6px rgba(0,0,0,.20));}
    .v-art-aqua{background:radial-gradient(circle at 30% 25%,#225b86,#14324e 70%);}
    .v-art-green{background:radial-gradient(circle at 30% 25%,#255e56,#142f41 70%);}
    .v-art-amber{background:radial-gradient(circle at 30% 25%,#715036,#253348 75%);}
    .v-art-pink{background:radial-gradient(circle at 30% 25%,#713e57,#253149 75%);}
    .v-art-lavender{background:radial-gradient(circle at 30% 25%,#514d83,#27314c 75%);}
    .v-stock-pill{position:absolute;z-index:1;right:7px;bottom:7px;border-radius:25px;padding:4px 7px;font-size:10px;font-weight:800;border:1px solid rgba(255,255,255,.14);}
    .v-healthy{color:#8ef1cb;background:#163e36;}.v-warning{color:#ffd396;background:#553d24;}.v-danger{color:#ffb0bf;background:#632f39;}
    .v-product-name{color:#eef7ff;font-size:14px;min-height:36px;font-weight:800;line-height:1.25;}
    .v-product-supplier{font-size:11px;color:#98b1cb;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;margin:4px 0 13px;}
    .v-product-meta{border-top:1px solid #2b4865;padding:9px 0;display:flex;justify-content:space-between;gap:9px;color:#9eb6cc;font-size:10px;}
    .v-product-meta b{color:#e8f5ff;}
    .v-product-price{font-size:22px;color:#fff;font-weight:900;margin:6px 0 13px;letter-spacing:-.035em;}
    .v-product-price small{font-size:11px;color:#9fb6d0;font-weight:500;}
    .v-compact .v-product-art{height:105px;}
    .v-compact .v-product-name{font-size:12px;}
    .v-compact .v-product-price{font-size:19px;margin-bottom:10px;}
    .v-cart-header{display:flex;justify-content:space-between;gap:10px;align-items:center;background:#152f4d;border:1px solid #2d5679;border-radius:13px;padding:14px 17px;margin:18px 0 13px;}
    .v-cart-header h3{font-size:21px;color:#fff !important;margin:4px 0 0;}
    .v-cart-count{background:#1b70d1;color:white;border-radius:99px;font-size:11px;font-weight:800;padding:6px 10px;white-space:nowrap;}
    .v-cart-empty{min-height:175px;text-align:center;background:#122842;border:1px dashed #335775;color:#83bfff;border-radius:13px;padding:38px 16px;font-size:31px;}
    .v-cart-empty strong{display:block;font-size:15px;color:white;margin-top:10px;}
    .v-cart-empty p{font-size:12px;color:#a6bdd5;margin:9px 0;}
    .v-cart-product{display:flex;gap:10px;align-items:center;border-bottom:1px solid #2b4863;padding:11px 0 3px;}
    .v-cart-emoji{font-size:29px;background:#193752;display:inline-grid;place-items:center;height:46px;width:46px;border-radius:11px;}
    .v-cart-product b{display:block;color:#ecf6ff;font-size:13px;}
    .v-cart-product small{display:block;color:#9ab3cc;font-size:11px;margin-top:3px;}
    .v-remove-spacer{height:30px;}
    .v-cart-total{margin:17px 0 10px;padding:17px 18px;border-radius:13px;background:linear-gradient(110deg,#183f6c,#154d83);border:1px solid #357fc2;display:flex;align-items:center;justify-content:space-between;gap:15px;}
    .v-cart-total span{color:#c4dcf2;font-weight:700;font-size:13px;}.v-cart-total strong{font-size:27px;color:#fff;}
    .v-budget-top{display:flex;justify-content:space-between;gap:9px;font-size:11px;color:#b7cde2;margin:13px 0 7px;}
    .v-budget-track{height:9px;background:#27405c;border-radius:100px;overflow:hidden;}.v-budget-fill{height:100%;border-radius:100px;transition:width .2s ease;}
    .v-space-top{margin-top:19px;}
    .v-supplier-row{display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid #2b4661;padding:10px 0;color:#dceafb;font-size:12px;}
    .v-supplier-row small{color:#9fcae5;font-size:11px;}
    [data-testid="stVerticalBlockBorderWrapper"] {border-color:#304f6e !important;}
    [data-testid="stVerticalBlockBorderWrapper"] > div {background:#11253c !important;}
    [data-testid="stButton"] button{font-weight:700 !important;}
    @media(max-width:850px){.v-product-art{height:90px}.v-product-art>span[role="img"]{font-size:43px}.v-section-head{flex-wrap:wrap}.v-builder-hero{padding:20px}.v-cart-total strong{font-size:22px;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# SMALL DISPLAY HELPERS (PRESENTATION ONLY — NO BUSINESS LOGIC CHANGES)
# -----------------------------------------------------------------------------
def go_to_page(destination: str) -> None:
    """Change the sidebar radio through a callback; no backend operations."""
    st.session_state["stocksense_navigation_v3"] = destination


def priority_inventory_rows(products: list[dict], limit: int = 6) -> str:
    """Escaped, presentation-only stock alert rows derived from SQLite."""
    prioritized = sorted(
        products,
        key=lambda p: (
            float(p.get("stock_quantity", 0)) / max(float(p.get("reorder_level", 0)), 1),
            -float(p.get("sales_last_7_days", 0)),
            str(p.get("name", "")),
        ),
    )[:limit]
    blocks = []
    for p in prioritized:
        stock = max(0, int(p.get("stock_quantity", 0)))
        threshold = max(0, int(p.get("reorder_level", 0)))
        percent = round(100 * stock / threshold) if threshold else 0
        percent = min(100, max(0, percent))
        level = "Out of stock" if stock == 0 else "Critical" if threshold and stock * 2 <= threshold else "Low stock"
        status_class = "ss-priority-danger" if level in ("Out of stock", "Critical") else "ss-priority-low"
        name = escape(str(p.get("name", "Unknown product")))
        supplier = escape(str(p.get("supplier", "Unknown supplier")))
        blocks.append(
            '<div class="ss-priority-row">'
            '<div class="ss-priority-info">'
            f'<div class="ss-priority-name">{name}</div>'
            f'<div class="ss-priority-supplier">{supplier}</div>'
            '</div>'
            f'<div class="ss-priority-metrics"><span class="ss-priority-qty">{stock}<small> / {threshold}</small></span>'
            f'<span class="ss-priority-pill {status_class}">{level}</span></div>'
            f'<div class="ss-priority-track"><div class="ss-priority-fill" style="width:{percent}%"></div></div>'
            '</div>'
        )
    return ''.join(blocks)


def section_heading(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        '<div class="ss-sec-kicker">' + escape(kicker) + "</div>"
        '<div class="ss-sec-heading">' + escape(title) + "</div>"
        '<div class="ss-sec-subtitle">' + escape(subtitle) + "</div>",
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, foot: str, symbol: str,
              alert: bool = False) -> None:
    alert_class = " ss-stat-alert" if alert else ""
    st.markdown(
        f'<div class="ss-stat{alert_class}">'
        f'<div class="ss-stat-top"><span class="ss-stat-label">{escape(label)}</span>'
        f'<span class="ss-stat-icon">{escape(symbol)}</span></div>'
        f'<div class="ss-stat-number">{escape(value)}</div>'
        f'<div class="ss-stat-foot">{escape(foot)}</div></div>',
        unsafe_allow_html=True,
    )


def product_title(product: dict, fallback: str) -> str:
    # "name" is used by the existing restock plan; use fallback defensively.
    return str(product.get("name") or product.get("product_name") or fallback)


def inventory_bars(products: list) -> None:
    """Quantity ranking, calculated directly from the existing inventory rows."""
    ranked = sorted(products, key=lambda p: int(p["stock_quantity"]), reverse=True)[:5]
    if not ranked:
        st.caption("Inventory is empty.")
        return
    maximum = max(int(row["stock_quantity"]) for row in ranked) or 1
    bars = []
    for i, product in enumerate(ranked, 1):
        quantity = int(product["stock_quantity"])
        label = escape(product_title(product, f"Product {i}"))
        # HTML escape data from SQLite; percentages are calculated numbers.
        width = max(0, min(100, round(quantity / maximum * 100)))
        bars.append(
            '<div class="ss-bar-row">'
            f'<div class="ss-bar-head"><span>{label}</span><strong>{quantity:,} units</strong></div>'
            f'<div class="ss-bar-track"><div class="ss-bar-fill" '
            f'style="width:{width}%"></div></div></div>'
        )
    st.markdown("".join(bars), unsafe_allow_html=True)


def _safe_number(value, default=None):
    """Parse a database numeric field without changing data in SQLite."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return default


def _stock_label(product, low_ids, low_names):
    """Use backend.get_low_stock() as source of truth for warning membership."""
    qty = _safe_number(product.get("stock_quantity"), 0)
    if qty <= 0:
        return "Out of stock"
    product_id = product.get("product_id", product.get("id"))
    product_name = str(product.get("name") or product.get("product_name") or "")
    if product_id is not None:
        is_low = str(product_id) in low_ids
    else:
        is_low = product_name in low_names
    return "Low stock" if is_low else "Healthy"


def _inventory_display_data(products, low_products):
    """Return display-only copies. No inventory writes or backend logic changes."""
    low_ids = {
        str(p.get("product_id", p.get("id"))) for p in low_products
        if p.get("product_id", p.get("id")) is not None
    }
    low_names = {
        str(p.get("name") or p.get("product_name") or "") for p in low_products
    }
    output = []
    for row in products:
        product = dict(row)
        qty = _safe_number(product.get("stock_quantity"), 0)
        cost = _safe_number(product.get("unit_cost"))
        product["_display_name"] = product_title(product, "Unnamed product")
        product["_display_supplier"] = str(product.get("supplier") or "Unspecified")
        product["_display_status"] = _stock_label(product, low_ids, low_names)
        product["_display_stock"] = qty
        product["_display_value"] = qty * cost if cost is not None else None
        output.append(product)
    return output


def _csv_from_products(products):
    """Export actual unmodified SQLite fields from currently filtered rows."""
    if not products:
        return ""
    columns = list(dict.fromkeys(
        field for product in products for field in product if not field.startswith("_display_")
    ))
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for product in products:
        writer.writerow(product)
    return buffer.getvalue()


def _inventory_table(products):
    """Contrast-safe, horizontally scrollable HTML table for the SQLite catalog."""
    if not products:
        st.markdown(
            '<div class="ss-inventory-empty">No products match the selected filters. '
            'Try another search or stock status.</div>',
            unsafe_allow_html=True,
        )
        return
    have_sales = any("sales_last_7_days" in p for p in products)
    have_price = any("selling_price" in p for p in products)
    headers = ["ID", "Product", "Supplier", "Status", "On hand", "Reorder at"]
    if have_sales:
        headers.append("Sales (7d)")
    headers.extend(["Unit cost", "Inventory value"])
    if have_price:
        headers.append("Sell price")
    html = [
        '<div class="ss-inventory-table-shell"><div class="ss-inventory-table-scroll">',
        '<table class="ss-inventory-table"><thead><tr>',
        "".join(f"<th>{escape(h)}</th>" for h in headers),
        '</tr></thead><tbody>',
    ]
    for p in products:
        status = p["_display_status"]
        status_css = {
            "Healthy": "ss-pill-good",
            "Low stock": "ss-pill-low",
            "Out of stock": "ss-pill-out",
        }[status]
        qty = p["_display_stock"]
        quantity = str(int(qty)) if qty.is_integer() else f"{qty:g}"
        reorder = _safe_number(p.get("reorder_level"))
        reorder_display = "—" if reorder is None else f"{reorder:g}"
        sales = _safe_number(p.get("sales_last_7_days"))
        unit_cost = _safe_number(p.get("unit_cost"))
        cost_value = p["_display_value"]
        price = _safe_number(p.get("selling_price"))
        id_display = p.get("product_id", p.get("id", "—"))
        cells = [
            f'<td class="muted">{escape(str(id_display))}</td>',
            f'<td class="name">{escape(p["_display_name"])}</td>',
            f'<td>{escape(p["_display_supplier"])}</td>',
            f'<td><span class="ss-inventory-pill {status_css}">{escape(status)}</span></td>',
            f'<td class="number right">{escape(quantity)}</td>',
            f'<td class="right">{escape(reorder_display)}</td>',
        ]
        if have_sales:
            cells.append(f'<td class="right">{"—" if sales is None else f"{sales:g}"}</td>')
        cells.extend([
            f'<td class="right">{"—" if unit_cost is None else f"${unit_cost:,.2f}"}</td>',
            f'<td class="number right">{"—" if cost_value is None else f"${cost_value:,.2f}"}</td>',
        ])
        if have_price:
            cells.append(f'<td class="right">{"—" if price is None else f"${price:,.2f}"}</td>')
        html.append("<tr>" + "".join(cells) + "</tr>")
    html.extend(['</tbody></table></div></div>'])
    st.markdown("".join(html), unsafe_allow_html=True)


def _order_status_label(value):
    """Return the display label and CSS class for a stored order status."""
    status = str(value or "unknown").strip().lower()
    if status == "draft":
        return "Draft", "ss-order-draft"
    if status == "approved":
        return "Approved locally", "ss-order-approved"
    return status.replace("_", " ").title(), "ss-order-other"


def _order_items_count(order):
    """The backend exposes individual order items as a list of rows."""
    items = order.get("items", [])
    return len(items) if isinstance(items, (list, tuple)) else 0


def _order_history_table(orders):
    """Show read-only persisted order metadata in a contrast-safe HTML table."""
    rows = [
        '<div class="ss-orders-table-wrap"><table class="ss-orders-table">',
        '<thead><tr><th>Order</th><th>Date created</th><th>Status</th>'
        '<th>Products</th><th>Estimated cost</th></tr></thead><tbody>',
    ]
    for order in orders:
        label, css_class = _order_status_label(order.get("status"))
        amount = _safe_number(order.get("total_cost"), 0.0)
        rows.append(
            '<tr>'
            f'<td class="emph">#{escape(str(order.get("order_id", "—")))}</td>'
            f'<td>{escape(str(order.get("created_at") or "—"))}</td>'
            f'<td><span class="ss-order-status {css_class}">{escape(label)}</span></td>'
            f'<td>{_order_items_count(order)}</td>'
            f'<td class="emph">${amount:,.2f}</td>'
            '</tr>'
        )
    rows.append('</tbody></table></div>')
    st.markdown(''.join(rows), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# BACKEND: KEEP THE SAME IMPLEMENTATION AND PUBLIC FUNCTION CALLS
# -----------------------------------------------------------------------------
backend = InventoryBackend()
backend.initialize()

# Keep all four navigation values identical to the original app.py.
st.sidebar.markdown(
    '<div class="ss-brand">'
    '<div class="ss-brand-icon">◆</div>'
    '<div><div class="ss-brand-name">StockSense <span>AI</span></div>'
    '<div class="ss-brand-note">OPERATIONS CONSOLE · 2.0</div></div></div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown('<div class="ss-nav-title">WORKSPACE</div>', unsafe_allow_html=True)
page = st.sidebar.radio(
    "Explore", ["Dashboard", "Inventory", "AI Assistant", "Purchase Orders"],
    label_visibility="collapsed", key="stocksense_navigation_v3",
)
st.sidebar.divider()
st.sidebar.markdown(
    '<div class="ss-side-foot">'
    '<div class="ss-side-title"><span class="ss-live-dot">●</span> Local simulation active</div>'
    '<div class="ss-side-description">SQLite-backed inventory · Sample product data<br>'
    'No supplier purchases · AI connection optional</div></div>',
    unsafe_allow_html=True,
)
st.sidebar.caption("BUILT FOR AMAZON BUILD, SHIP, SHAPE 2026")


# -----------------------------------------------------------------------------
# 1. DASHBOARD — PREMIUM THREE-COLUMN GRID (LIVE SQLITE DATA)
# -----------------------------------------------------------------------------
if page == "Dashboard":
    inv = backend.get_inventory()
    low = backend.get_low_stock()
    orders = backend.get_orders()
    product_count = len(inv)
    low_stock_count = len(low)
    units_in_stock = sum(int(p["stock_quantity"]) for p in inv)
    inventory_cost = sum(int(p["stock_quantity"]) * float(p["unit_cost"]) for p in inv)
    out_count = sum(int(p["stock_quantity"]) == 0 for p in inv)
    healthy_count = max(0, product_count - low_stock_count)
    low_only_count = max(0, low_stock_count - out_count)
    healthy_percent = round(100 * healthy_count / product_count) if product_count else 0
    seven_day_sales = sum(int(p.get("sales_last_7_days", 0)) for p in inv)
    supplier_count = len({str(p.get("supplier", "")) for p in inv})
    draft_count = sum(o.get("status") == "draft" for o in orders)
    approved_count = sum(o.get("status") == "approved" for o in orders)

    # No guessed revenue, fabricated trend, or fictitious 'AI accuracy' figures.
    st.markdown(
        '<div class="ss4-shell"><div class="ss4-heading">'
        '<div><h1>Dashboard</h1><p>Good decisions begin with a clear picture of your inventory.</p></div>'
        '<span class="ss4-state"><i></i> SQLite database connected</span>'
        '</div></div>', unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="ss4-shell"><div class="ss4-metrics">'
        f'<div class="ss4-kpi ss4-kpi-feature"><div class="ss4-kpi-head">Inventory at cost'
        f'<span class="ss4-kpi-symbol">$</span></div><div class="ss4-kpi-value">${inventory_cost:,.2f}</div>'
        '<div class="ss4-kpi-foot">Current stock value · not revenue</div></div>'
        f'<div class="ss4-kpi"><div class="ss4-kpi-head">Products tracked<span class="ss4-kpi-symbol">▦</span></div>'
        f'<div class="ss4-kpi-value">{product_count:,}</div><div class="ss4-kpi-foot">SQLite catalog items</div></div>'
        f'<div class="ss4-kpi"><div class="ss4-kpi-head">Units on hand<span class="ss4-kpi-symbol">◫</span></div>'
        f'<div class="ss4-kpi-value">{units_in_stock:,}</div><div class="ss4-kpi-foot">Across all products</div></div>'
        f'<div class="ss4-kpi"><div class="ss4-kpi-head">Need restocking<span class="ss4-kpi-symbol">!</span></div>'
        f'<div class="ss4-kpi-value ss4-alert-number">{low_stock_count:,}</div>'
        '<div class="ss4-kpi-foot">At or below reorder threshold</div></div>'
        '</div></div>', unsafe_allow_html=True,
    )

    st.markdown('<div class="ss4-shell"><div class="ss4-action-head"><h3>QUICK ACTIONS</h3></div></div>', unsafe_allow_html=True)
    nav_lab, nav_inv, nav_orders, nav_ai = st.columns(4, gap="small")
    with nav_lab:
        st.markdown('<a class="ss-command-link-action" href="#smart-restock-decision-lab">↗ Run restock lab</a>', unsafe_allow_html=True)
    with nav_inv:
        st.button("▦ Inventory catalog", key="premium_inv", on_click=go_to_page,
                  args=("Inventory",), width="stretch")
    with nav_orders:
        st.button("🛒 Visual Purchase Builder", key="premium_orders", on_click=go_to_page,
                  args=("Purchase Orders",), width="stretch")
    with nav_ai:
        st.button("✦ AI Assistant", key="premium_ai", on_click=go_to_page,
                  args=("AI Assistant",), width="stretch")

    # Render a complete 3-column analytics grid; each figure is directly derived
    # from the local SQLite records loaded above.
    peak = max(1, healthy_count, low_only_count, out_count)
    chart_entries = [
        ("Healthy", healthy_count, "blue"),
        ("Low stock", low_only_count, "aqua"),
        ("Out of stock", out_count, "purple"),
    ]
    chart_html = "".join(
        f'<div class="ss4-col-wrap"><div class="ss4-col-number">{num}</div>'
        f'<div class="ss4-col {css}" style="height:{round(100*num/peak) if num else 2}%"></div>'
        f'</div>' for label, num, css in chart_entries
    )
    labels_html = ''.join(f'<div style="flex:1;text-align:center">{escape(label)}</div>'
                          for label, num, css in chart_entries)
    critical = sorted(low, key=lambda p:(int(p["stock_quantity"]) / max(1,int(p["reorder_level"])),
                                             -int(p.get("sales_last_7_days",0))))[:4]
    critical_html = "".join(
        '<div class="ss4-item">'
        f'<span class="ss4-product-mark">{product_symbol(str(p["name"]))[0]}</span>'
        f'<div class="ss4-item-main"><strong>{escape(str(p["name"]))}</strong>'
        f'<small>{escape(str(p.get("supplier", "Supplier unavailable")))}</small></div>'
        f'<div class="ss4-item-right"><b>{int(p["stock_quantity"])} / {int(p["reorder_level"])}</b>'
        '<span class="ss4-chip">Low stock</span></div></div>'
        for p in critical
    ) if critical else '<div class="ss4-note">No products currently need restocking.</div>'
    st.markdown(
        '<div class="ss4-shell"><div class="ss4-main-grid">'
        '<section class="ss4-card"><div class="ss4-card-top"><h2>Overview</h2>'
        '<span class="hint">Live snapshot</span></div>'
        '<p class="sub">A snapshot from the sample inventory</p>'
        f'<div class="ss4-mini-row"><div class="label">Products above reorder level</div>'
        f'<div class="value blue">{healthy_count} <span style="font-size:12px;color:#8d9caf">of {product_count}</span></div>'
        '<div class="detail">Products not currently flagged</div></div>'
        f'<div class="ss4-mini-row"><div class="label">Units sold · last 7 days</div>'
        f'<div class="value">{seven_day_sales:,}</div>'
        '<div class="detail">Sample sales quantities, not revenue</div></div>'
        f'<div class="ss4-mini-row"><div class="label">Supplier partners</div>'
        f'<div class="value">{supplier_count:,}</div><div class="detail">Distinct suppliers in SQLite</div></div>'
        '</section>'
        '<section class="ss4-card"><div class="ss4-card-top"><h2>Stock distribution</h2>'
        '<span class="hint">Product counts</span></div>'
        '<p class="sub">Inventory health by reorder status</p>'
        f'<div class="ss4-columns">{chart_html}</div>'
        f'<div style="display:flex;gap:15px">{labels_html}</div>'
        '<div class="ss4-legend">'
        f'<span><b>{healthy_percent}%</b> of products healthy</span>'
        f'<span><b>{low_stock_count}</b> need attention</span></div>'
        '</section>'
        '<section class="ss4-card"><div class="ss4-card-top"><h2>Priority insights</h2>'
        '<span class="hint">By urgency</span></div>'
        '<p class="sub">Most urgent products based on reorder thresholds</p>'
        f'{critical_html}'
        '</section>'
        '</div></div>', unsafe_allow_html=True,
    )

    critical_rows = sorted(low,key=lambda p:(int(p["stock_quantity"])/max(1,int(p["reorder_level"])),
                                           str(p["name"])))[:5]
    table_rows = "".join(
        f'<tr><td class="pname">{escape(str(p["name"]))}</td>'
        f'<td>{escape(str(p["supplier"]))}</td>'
        f'<td class="right">{int(p["stock_quantity"])} / {int(p["reorder_level"])}</td>'
        f'<td><div class="ss4-progress"><div style="width:{max(0, min(100, round(100 * int(p["stock_quantity"]) / max(1, int(p["reorder_level"])))))}%"></div></div></td></tr>'
        for p in critical_rows
    ) if critical_rows else '<tr><td colspan="4">No active stock alerts.</td></tr>'
    st.markdown(
        '<div class="ss4-shell"><div class="ss4-bottom-grid">'
        '<section class="ss4-card"><div class="ss4-card-top"><h2>Products requiring action</h2>'
        '<span class="hint">Live SQLite</span></div>'
        '<p class="sub">Focus on the most understocked items before restocking</p>'
        '<table class="ss4-risktable"><thead><tr><th>Product</th><th>Supplier</th>'
        '<th class="right">Stock / goal</th><th>Coverage</th></tr></thead><tbody>'
        f'{table_rows}</tbody></table></section>'
        '<section class="ss4-card"><div class="ss4-card-top"><h2>Purchase workflow</h2>'
        '<span class="hint">Saved to SQLite</span></div>'
        '<p class="sub">Real order history, with explicit human confirmation</p>'
        f'<div class="ss4-workflow-row"><span class="name">Awaiting review</span><span class="count">{draft_count}</span></div>'
        f'<div class="ss4-workflow-row"><span class="name">Approved locally</span><span class="count">{approved_count}</span></div>'
        '<div class="ss4-cta"><div class="ss4-cta-icon">✦</div><div>'
        '<strong>Your StockSense assistant</strong><p>Ask inventory questions and prepare a draft after AI setup. '
        'For now, the Decision Lab and manual orders work without an API key.</p>'
        '</div></div></section>'
        '</div></div>', unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ss-owner-head"><strong>Morning Operations Brief</strong>'
        '<p>One click replaces manual stock checks, budget allocation, '
        'supplier sorting, and pending-draft cross-checks. It is a transparent '
        'local calculation, not a measured time-saving claim.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("Generate today's procurement action brief · $150 baseline",
                 key="ss_ops_brief_run_v1", type="primary", width="stretch"):
        try:
            st.session_state["ss_ops_brief_v1"] = backend.recommend_smart_restock(
                150.0, delay_days=0, planning_days=7,
            )
        except (ValueError, TypeError) as exc:
            st.session_state.pop("ss_ops_brief_v1", None)
            st.error(f"Unable to generate operations brief: {exc}")
    brief = st.session_state.get("ss_ops_brief_v1")
    if brief:
        proposed = brief["items"]
        proposed_ids = {line["product_id"] for line in proposed}
        overlap_ids = set()
        for order in orders:
            if order.get("status") == "draft":
                overlap_ids.update(line["product_id"] for line in order.get("items", [])
                                   if line["product_id"] in proposed_ids)
        details = [{
            "Product": item["name"], "Supplier": item["supplier"],
            "Risk": item["risk"], "Buy qty": item["quantity"],
            "Line cost": item["line_cost"],
            "Already in a pending draft": "Yes" if item["product_id"] in overlap_ids else "No",
        } for item in proposed]
        brief_cols = st.columns(3)
        with brief_cols[0]:
            stat_card("Low-stock products", str(low_stock_count), "SQLite reorder alerts", "!")
        with brief_cols[1]:
            stat_card("Baseline plan", f"${brief['total_cost']:.2f}", "$150 proposed budget", "$")
        with brief_cols[2]:
            stat_card("Draft overlap", str(len(overlap_ids)), "Products in pending drafts", "▤", alert=bool(overlap_ids))
        if overlap_ids:
            st.warning("Some recommendations already appear in saved drafts. "
                       "Review Purchase Orders before preparing another order. "
                       "Drafts are not confirmed deliveries.")
        if details:
            st.dataframe(details, hide_index=True, width="stretch")
            buf = StringIO()
            writer = csv.DictWriter(buf, fieldnames=list(details[0]))
            writer.writeheader()
            writer.writerows(details)
            st.download_button("Download action brief (CSV)", data=buf.getvalue(),
                               file_name="stocksense_operations_brief.csv", mime="text/csv",
                               key="ss_ops_brief_export_v1", width="stretch")
        else:
            st.info("There are no recommended purchase lines at this baseline budget.")
        st.caption(brief["caveat"])

    st.markdown('<div id="smart-restock-decision-lab"></div>',unsafe_allow_html=True)
    st.markdown('<div class="ss4-module-title"><div><div class="eyebrow">DECISION INTELLIGENCE</div>'
                '<h2>Smart Restock Decision Lab</h2><p>Compare budgets, supplier delays and planning horizons.</p>'
                '</div></div>', unsafe_allow_html=True)

    # Preserve the original form keys, bounds and backend function call.
    lab_left, lab_right = st.columns([1.5, 1], gap="medium")
    with lab_left:
        with st.form("decision_lab_form"):
            st.markdown("**Configure your scenario**")
            budget = st.number_input(
                "Available cash (USD)", min_value=0.0,
                max_value=1000000.0, value=150.0, step=10.0,
            )
            delay = st.slider(
                "Extra supplier delivery delay (days)",
                min_value=0, max_value=7, value=0,
            )
            horizon = st.slider(
                "Planning horizon after delivery (days)",
                min_value=1, max_value=14, value=7,
            )
            run_plan = st.form_submit_button(
                "Analyze restocking plan", type="primary", width="stretch",
            )
            st.caption("This is an analysis only; it does not save, approve or send an order.")
    with lab_right:
        st.markdown(
            '<div class="ss-lab-tip"><div class="ss-lab-tip-title">01 · Try a $150 budget</div>'
            '<div class="ss-lab-tip-copy">See how the existing decision engine distributes available cash.</div></div>'
            '<div class="ss-lab-tip"><div class="ss-lab-tip-title">02 · Stress-test $50</div>'
            '<div class="ss-lab-tip-copy">Compare the changes when your budget becomes tighter.</div></div>'
            '<div class="ss-lab-tip"><div class="ss-lab-tip-title">03 · Add a supplier delay</div>'
            '<div class="ss-lab-tip-copy">Simulate 0–7 extra delivery days to expose shortage risks.</div></div>',
            unsafe_allow_html=True,
        )
        st.info("Lead times and shelf lives are simulated assumptions, not live supplier information.")

    if run_plan:
        try:
            plan = backend.recommend_smart_restock(
                budget, delay_days=delay, planning_days=horizon,
            )
            st.session_state["smart_restock_preview"] = plan
        except (ValueError, TypeError) as exc:
            st.session_state.pop("smart_restock_preview", None)
            st.error(str(exc))

    if "smart_restock_preview" in st.session_state:
        plan = st.session_state["smart_restock_preview"]
        st.write("")
        with st.container(border=True):
            section_heading(
                "SCENARIO RESULT", "Recommended restock plan",
                "Calculated by your existing Smart Restock algorithm. No order has been saved.",
            )
            result_cols = st.columns(3, gap="medium")
            with result_cols[0]:
                stat_card("Suggested spending", f"${plan['total_cost']:,.2f}",
                          "Estimated purchasing cost", "$")
            with result_cols[1]:
                stat_card("Budget remaining", f"${plan['remaining_budget']:,.2f}",
                          "Not committed", "◈")
            with result_cols[2]:
                stat_card("At risk before delivery", f"{plan['at_risk_before_delivery']:,}",
                          "Estimated shortage-risk count", "!",
                          alert=plan["at_risk_before_delivery"] > 0)

            if plan["items"]:
                # All backend recommendation fields and explanatory reasons remain available.
                st.dataframe(
                    [{
                        "Product": p["name"], "Risk": p["risk"],
                        "Days of cover": p["days_of_cover"],
                        "Lead time (days)": p["supplier_lead_days"],
                        "Suggested quantity": p["quantity"],
                        "Line cost": p["line_cost"],
                        "Shelf-life cap": "Applied" if p["perishable_cap_applied"] else "No",
                        "Why": p["reason"],
                    } for p in plan["items"]],
                    hide_index=True, width="stretch",
                )
                st.info("To save a LOCAL draft without an API key, open Purchase Orders → "
                        "Preview restocking recommendation → Create draft order in SQLite. "
                        "Approval remains a separate confirmation step.")
            else:
                st.warning("Nothing fits this budget and planning scenario.")
            if plan["not_fully_funded"]:
                st.caption("Not fully funded: " + ", ".join(plan["not_fully_funded"]))
            st.caption(plan["caveat"])

    st.markdown(
        '<div class="ss-footnote">STOCKSENSE AI 2.0 · Data are simulated sample '
        'inventory. Lead times and shelf lives are assumptions. No supplier '
        'purchases occur, and no savings have been measured.</div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 2. INVENTORY — POLISHED CATALOG; SAME EXISTING READ-ONLY BACKEND CALLS
# -----------------------------------------------------------------------------
elif page == "Inventory":
    # Keep backend calls authoritative; filters and badges only change presentation.
    inventory = backend.get_inventory()
    low_inventory = backend.get_low_stock()
    catalog = _inventory_display_data(inventory, low_inventory)
    product_count = len(catalog)
    low_count = len(low_inventory)
    out_count = sum(p["_display_status"] == "Out of stock" for p in catalog)
    total_units = sum(p["_display_stock"] for p in catalog)
    suppliers = sorted({p["_display_supplier"] for p in catalog}, key=str.casefold)

    st.markdown('<div class="ss-topline">Workspace / Inventory</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="ss-inventory-hero">'
        '<div class="eyebrow">YOUR STOCK, CLEARLY ORGANIZED</div>'
        '<h1>Inventory workspace</h1>'
        '<p>Search products, review reorder alerts, and see stock values '
        'calculated from your existing SQLite inventory. All records shown are '
        'local sample data; this screen does not change quantities.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    new_product_notice = st.session_state.pop("ss_product_added_notice", None)
    if new_product_notice:
        st.success(new_product_notice)

    with st.expander("＋ Add a new product to the catalog", expanded=False):
        st.caption("Business owner control · Saves a product to SQLite. Does not create an order or contact a supplier.")
        with st.form("ss_add_product_form", clear_on_submit=True):
            prod_left, prod_right = st.columns(2, gap="medium")
            with prod_left:
                new_name = st.text_input("Product name *", placeholder="e.g. Coca-Cola 500ml")
                new_supplier = st.text_input("Supplier *", placeholder="e.g. Local Beverages")
                new_stock = st.number_input("Current units on hand *", min_value=0, max_value=1000000, value=0, step=1)
                new_reorder = st.number_input("Reorder level *", min_value=0, max_value=1000000, value=10, step=1)
                new_sales = st.number_input("Sales in the last 7 days *", min_value=0, max_value=1000000, value=0, step=1)
            with prod_right:
                new_cost = st.number_input("Purchase cost per unit (USD) *", min_value=0.01, max_value=1000000.0, value=1.00, step=0.25, format="%.2f")
                new_price = st.number_input("Selling price per unit (USD) *", min_value=0.0, max_value=1000000.0, value=2.00, step=0.25, format="%.2f")
                new_lead = st.number_input("Assumed supplier lead time (days)", min_value=0, max_value=365, value=3, step=1)
                new_shelf = st.number_input("Assumed shelf life (days, 0 = unspecified)", min_value=0, max_value=3650, value=0, step=1)
            st.caption("Lead time, shelf life and manually entered sales are estimates. Smart Restock skips products with zero recent sales.")
            add_clicked = st.form_submit_button("＋ Save product to SQLite", type="primary", width="stretch")
        if add_clicked:
            try:
                created = backend.add_product(
                    name=new_name, supplier=new_supplier,
                    stock_quantity=int(new_stock), reorder_level=int(new_reorder),
                    sales_last_7_days=int(new_sales), unit_cost=float(new_cost),
                    selling_price=float(new_price), supplier_lead_days=int(new_lead),
                    shelf_life_days=int(new_shelf) if new_shelf else None,
                )
                st.session_state["ss_product_added_notice"] = (
                    f"Added product #{created['product_id']}: {created['name']}. "
                    "It's now available for manual purchasing and inventory review."
                )
                st.rerun()
            except (ValueError, TypeError) as exc:
                st.error(f"Product not saved: {exc}")
            except Exception:
                st.error("Product could not be saved. Review the local database connection.")

    cards = st.columns(4, gap="medium")
    with cards[0]:
        stat_card("Catalog products", f"{product_count:,}", "Stored in SQLite", "▦")
    with cards[1]:
        stat_card("Units on hand", f"{total_units:,.0f}", "Across all products", "◫")
    with cards[2]:
        stat_card("Low-stock alerts", f"{low_count:,}", "From get_low_stock()", "!", alert=low_count > 0)
    with cards[3]:
        stat_card("Active suppliers", f"{len(suppliers):,}", "From supplier field", "♧")

    st.write("")
    section_heading(
        "PRODUCT DIRECTORY", "Browse inventory",
        "Search by product, supplier or ID. Refine by stock status and supplier.",
    )
    with st.container(border=True):
        col_search, col_status, col_supplier, col_sort = st.columns(
            [1.75, 1, 1.1, 1.2], gap="small"
        )
        with col_search:
            query = st.text_input(
                "Search products", placeholder="e.g. milk, olive oil, FreshFields",
                key="inventory_search_v2",
            ).strip().casefold()
        with col_status:
            status_filter = st.selectbox(
                "Stock status", ["All", "Low stock", "Out of stock", "Healthy"],
                key="inventory_status_v2",
            )
        with col_supplier:
            supplier_filter = st.selectbox(
                "Supplier", ["All suppliers", *suppliers],
                key="inventory_supplier_v2",
            )
        with col_sort:
            sort_by = st.selectbox(
                "Sort by", ["Needs attention", "Product A–Z", "Lowest stock", "Highest stock value"],
                key="inventory_sort_v2",
            )

    filtered = []
    for p in catalog:
        identity = str(p.get("product_id", p.get("id", "")))
        haystack = " ".join([p["_display_name"], p["_display_supplier"], identity]).casefold()
        if query and query not in haystack:
            continue
        # Low stock includes out-of-stock products, matching backend alert semantics.
        if status_filter == "Low stock" and p["_display_status"] not in ("Low stock", "Out of stock"):
            continue
        if status_filter in ("Out of stock", "Healthy") and p["_display_status"] != status_filter:
            continue
        if supplier_filter != "All suppliers" and p["_display_supplier"] != supplier_filter:
            continue
        filtered.append(p)

    if sort_by == "Needs attention":
        order = {"Out of stock": 0, "Low stock": 1, "Healthy": 2}
        filtered.sort(key=lambda p: (order[p["_display_status"]], p["_display_stock"], p["_display_name"].casefold()))
    elif sort_by == "Product A–Z":
        filtered.sort(key=lambda p: p["_display_name"].casefold())
    elif sort_by == "Lowest stock":
        filtered.sort(key=lambda p: (p["_display_stock"], p["_display_name"].casefold()))
    else:
        filtered.sort(key=lambda p: (p["_display_value"] is None, -(p["_display_value"] or 0)))

    render_inventory_gallery(st, filtered, go_to_page)
    st.write("")

    tally, exporter = st.columns([3.2, 1], gap="small")
    with tally:
        st.markdown(
            '<div class="ss-inventory-tally">'
            f'<strong>{len(filtered):,}</strong> of <strong>{product_count:,}</strong> '
            'products shown &nbsp;·&nbsp; '
            f'<strong>{low_count:,}</strong> low-stock alerts overall &nbsp;·&nbsp; '
            f'<strong>{out_count:,}</strong> currently out of stock'
            '</div>',
            unsafe_allow_html=True,
        )
    with exporter:
        st.download_button(
            "Download filtered CSV", data=_csv_from_products(filtered),
            file_name="stocksense_inventory_filtered.csv", mime="text/csv",
            disabled=not filtered, width="stretch", key="inventory_export_v2",
        )

    _inventory_table(filtered)
    st.markdown(
        '<div class="ss-inventory-help">'
        '<strong>How alerts work:</strong> Low stock comes from your existing '
        'SQLite backend; “Out of stock” means a recorded quantity of zero or less. '
        'The table and downloaded CSV are read-only views. Use the Dashboard’s '
        'Smart Restock Decision Lab to explore purchasing scenarios.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.expander("View all original SQLite fields"):
        st.caption("Unmodified inventory records from backend.get_inventory().")
        st.dataframe(inventory, hide_index=True, width="stretch")


# -----------------------------------------------------------------------------
# 3. AI ASSISTANT — EXISTING PAGE AND FUNCTIONALITY PRESERVED
# -----------------------------------------------------------------------------
elif page == "AI Assistant":
    render_assistant_page()


# -----------------------------------------------------------------------------
# 4. PURCHASE ORDERS — LIVE SQLITE HISTORY; EXPLICIT LOCAL APPROVAL ONLY
# -----------------------------------------------------------------------------
else:
    # Orders are read from the ORIGINAL backend. No tables or schemas are changed.
    orders = list(backend.get_orders())
    drafts = [o for o in orders if str(o.get("status", "")).lower() == "draft"]
    approved = [o for o in orders if str(o.get("status", "")).lower() == "approved"]
    draft_value = sum(_safe_number(o.get("total_cost"), 0.0) for o in drafts)

    st.markdown('<div class="ss-topline">Workspace / Purchase Orders</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="ss-orders-hero">'
        '<div class="eyebrow">PURCHASING, WITH HUMAN OVERSIGHT</div>'
        '<h1>Purchase Orders</h1>'
        '<p>Track locally saved restock drafts, review proposed purchases, '
        'and explicitly approve each order. Nothing is sent to suppliers; '
        'approvals do not automatically increase stock.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    cards = st.columns(4, gap="medium")
    with cards[0]:
        stat_card("Saved orders", f"{len(orders):,}", "From local SQLite history", "▤")
    with cards[1]:
        stat_card("Awaiting approval", f"{len(drafts):,}", "Saved drafts requiring review", "!", alert=bool(drafts))
    with cards[2]:
        stat_card("Approved locally", f"{len(approved):,}", "No supplier action performed", "✓")
    with cards[3]:
        stat_card("Draft order value", f"${draft_value:,.2f}", "Total proposed, not spent", "$")

    st.write("")
    # New visual product gallery and reactive cart. The old backend contract is unchanged.
    render_visual_purchase_builder(st, backend, orders)

    st.divider()
    section_heading("SMART AUTOMATION", "AI-assisted restock recommendation",
                    "Or let the existing decision engine choose priorities under a budget.")

    with st.form("po_draft_scenario_form"):
        config_a, config_b, config_c = st.columns([1.2, 1, 1], gap="medium")
        with config_a:
            po_budget = st.number_input(
                "Maximum budget (USD)", min_value=0.0, max_value=1000000.0,
                value=150.0, step=10.0, format="%.2f", key="po_draft_budget_v2",
            )
        with config_b:
            po_delay = st.slider(
                "Extra supplier delay (days)", 0, 7, 0,
                key="po_draft_delay_v2",
            )
        with config_c:
            po_horizon = st.slider(
                "Planning horizon (days)", 1, 14, 7,
                key="po_draft_horizon_v2",
            )
        submit_preview = st.form_submit_button(
            "Preview restocking recommendation", type="primary", width="stretch",
        )

    if submit_preview:
        # Preview is read-only: it never writes an order to SQLite.
        st.session_state.pop("po_draft_checked_v2", None)
        st.session_state.pop("po_draft_preview_v2", None)
        try:
            preview = backend.recommend_smart_restock(
                float(po_budget), delay_days=int(po_delay),
                planning_days=int(po_horizon),
            )
            if float(preview["total_cost"]) > float(po_budget) + 0.01:
                st.error("The backend recommendation exceeds the selected budget. "
                         "No draft was created.")
            else:
                st.session_state["po_draft_preview_v2"] = {
                    "plan": preview,
                    "budget": float(po_budget),
                    "delay": int(po_delay),
                    "horizon": int(po_horizon),
                }
        except (ValueError, TypeError, KeyError) as exc:
            st.error(f"Unable to calculate a restock preview: {exc}")

    saved_notice = st.session_state.pop("po_saved_notice_v2", None)
    if saved_notice:
        st.success(saved_notice)

    preview_state = st.session_state.get("po_draft_preview_v2")
    if preview_state:
        preview = preview_state["plan"]
        preview_budget = preview_state["budget"]
        st.write("")
        with st.container(border=True):
            section_heading(
                "REVIEW BEFORE SAVING", "Recommendation preview",
                f"Budget: ${preview_budget:,.2f} | "
                f"Extra delay: {preview_state['delay']} days | "
                f"Planning horizon: {preview_state['horizon']} days. "
                "This preview has NOT been saved.",
            )
            cols = st.columns(3, gap="medium")
            with cols[0]:
                stat_card("Suggested spending", f"${preview['total_cost']:,.2f}",
                          "Estimated draft cost", "$")
            with cols[1]:
                stat_card("Budget remaining", f"${preview['remaining_budget']:,.2f}",
                          "Budget not allocated", "◈")
            with cols[2]:
                stat_card("At risk before delivery",
                          str(preview["at_risk_before_delivery"]),
                          "Simulation estimate", "!",
                          alert=preview["at_risk_before_delivery"] > 0)
            if preview.get("items"):
                st.dataframe(
                    [{"Product": item["name"],
                      "Suggested quantity": item["quantity"],
                      "Line cost": item["line_cost"],
                      "Risk": item["risk"],
                      "Why": item["reason"]}
                     for item in preview["items"]],
                    hide_index=True, width="stretch",
                )
                st.info("Saving a draft creates a local SQLite record. "
                        "It does not approve the order, place a purchase, "
                        "or increase stock quantities.")
                smart_ids = {p["product_id"] for p in preview["items"]}
                matching_drafts = []
                for open_order in backend.get_orders():
                    if open_order.get("status") != "draft":
                        continue
                    shared = [line for line in open_order.get("items", [])
                              if line.get("product_id") in smart_ids]
                    if shared:
                        matching_drafts.append(open_order["order_id"])
                if matching_drafts:
                    st.warning("These products also appear in pending drafts "
                               + ", ".join(f"#{oid}" for oid in matching_drafts[:10])
                               + ". Review them to prevent double purchasing. "
                               "The backend blocks identical automated drafts.")
                    checked_overlaps = st.checkbox(
                        "I checked the existing drafts and still want this new plan.",
                        key="ss_smart_draft_overlap_checked_v1",
                    )
                else:
                    checked_overlaps = True
                reviewed = st.checkbox(
                    "I reviewed this recommendation and want to save a LOCAL "
                    "draft for later approval.",
                    key="po_draft_checked_v2",
                )
                if st.button(
                    "Create draft order in SQLite", type="primary",
                    disabled=not (reviewed and checked_overlaps), key="po_create_draft_btn_v2",
                    width="stretch",
                ):
                    try:
                        # The adapter already provides this higher-level method.
                        # Avoid passing plan['items'] to create_draft(): the low-level
                        # schema cannot be validated without backend.py.
                        existing_ids = {str(o.get("order_id"))
                                        for o in backend.get_orders()}
                        backend.prepare_smart_order(
                            preview_budget,
                            delay_days=preview_state["delay"],
                            planning_days=preview_state["horizon"],
                        )
                        latest_orders = list(backend.get_orders())
                        new_orders = [o for o in latest_orders
                                      if str(o.get("order_id")) not in existing_ids]
                        if len(new_orders) != 1:
                            st.error(
                                "Could not confirm exactly one new saved order. "
                                "Please check Purchase Orders history before "
                                "trying again; do not click repeatedly. "
                                "The backend may use a different return format."
                            )
                        else:
                            saved = new_orders[0]
                            saved_status = str(saved.get("status", "")).lower()
                            saved_cost = float(saved.get("total_cost", 0))
                            if saved_status != "draft":
                                st.error(
                                    f"Order #{saved.get('order_id')} was saved "
                                    f"with unexpected status '{saved_status}'. "
                                    "Do not proceed with approval until the "
                                    "backend has been inspected."
                                )
                            elif saved_cost > preview_budget + 0.01:
                                st.error(
                                    f"Order #{saved.get('order_id')} was saved "
                                    "but exceeds the budget. Do not approve it."
                                )
                            else:
                                st.session_state.pop("po_draft_preview_v2", None)
                                st.session_state["po_saved_notice_v2"] = (
                                    f"Saved order #{saved.get('order_id')} as a "
                                    f"LOCAL draft (${saved_cost:,.2f}). "
                                    "Review it below before approving."
                                )
                                st.rerun()
                    except Exception as exc:
                        st.error(
                            f"Draft preparation could not be confirmed: {exc}. "
                            "Check Purchase Orders history before retrying."
                        )
            else:
                st.warning("This scenario has no recommended items; "
                           "there is nothing to save as a draft.")
            if preview.get("caveat"):
                st.caption(str(preview["caveat"]))

    st.write("")
    if not orders:
        section_heading(
            "ORDER WORKFLOW", "Ready for your first order",
            "No purchase-order drafts have been saved yet.",
        )
        left, right = st.columns([1.3, 1], gap="medium")
        with left:
            st.markdown(
                '<div class="ss-orders-panel">'
                '<div class="ss-orders-empty-mark">▤</div>'
                '<h3>No purchase orders saved yet</h3>'
                '<div class="ss-orders-copy">Analyze a restock scenario above, '
                'review the suggested items, then explicitly save a local draft. '
                'Only saved orders will appear in your SQLite history.</div>'
                '</div>', unsafe_allow_html=True,
            )
        with right:
            st.markdown(
                '<div class="ss-orders-panel"><h3>How local approval works</h3>'
                '<div class="ss-orders-step"><span class="ss-orders-step-number">1</span>'
                '<div><div class="ss-orders-step-title">Analyze inventory</div>'
                '<div class="ss-orders-step-desc">Calculate quantities using sample '
                'inventory, simulated lead times and a budget.</div></div></div>'
                '<div class="ss-orders-step"><span class="ss-orders-step-number">2</span>'
                '<div><div class="ss-orders-step-title">Save a draft</div>'
                '<div class="ss-orders-step-desc">Explicitly save the recommendation '
                'as a local SQLite draft. No approval occurs.</div></div></div>'
                '<div class="ss-orders-step"><span class="ss-orders-step-number">3</span>'
                '<div><div class="ss-orders-step-title">Review and approve</div>'
                '<div class="ss-orders-step-desc">Open the saved order and check '
                'the confirmation box before approval.</div></div></div>'
                '</div>', unsafe_allow_html=True,
            )
    else:
        section_heading(
            "ORDER HISTORY", "Saved purchasing activity",
            "Only records from backend.get_orders() are shown below.",
        )
        view = st.selectbox(
            "Filter orders", ["All orders", "Drafts", "Approved", "Other statuses"],
            key="orders_status_filter_v2",
        )
        if view == "Drafts":
            displayed = drafts
        elif view == "Approved":
            displayed = approved
        elif view == "Other statuses":
            displayed = [o for o in orders if o not in drafts and o not in approved]
        else:
            displayed = orders

        st.markdown(
            f'<div class="ss-inventory-tally"><strong>{len(displayed):,}</strong> '
            f'of <strong>{len(orders):,}</strong> saved orders shown</div>',
            unsafe_allow_html=True,
        )
        if displayed:
            _order_history_table(displayed)
            st.write("")
            section_heading(
                "ORDER DETAILS", "Review and approve",
                "Open a saved order to inspect its items. Drafts require explicit confirmation.",
            )
        else:
            st.info("There are no saved orders with this status.")

        for order in displayed:
            amount = _safe_number(order.get("total_cost"), 0.0)
            status = str(order.get("status", "unknown"))
            oid = order["order_id"]
            with st.expander(f"Order #{oid} · {status.upper()} · ${amount:,.2f}"):
                st.caption(f"Created: {order.get('created_at') or '—'}")
                items = order.get("items", [])
                if items:
                    st.dataframe(items, hide_index=True, width="stretch")
                else:
                    st.info("There are no line items recorded for this order.")
                if status.lower() == "draft":
                    st.warning(
                        "This action approves the saved draft in SQLite only. "
                        "It does not send a supplier purchase or receive stock."
                    )
                    check_key = f"confirm_order_checkbox_{oid}"
                    checked = st.checkbox(
                        f"I confirm approval of LOCAL draft #{oid} "
                        "(no real purchase will be sent).",
                        key=check_key,
                    )
                    if st.button(
                        f"Approve local draft #{oid}",
                        disabled=not checked, type="primary",
                        key=f"approve_local_{oid}",
                    ):
                        try:
                            # This is the ORIGINAL backend safety contract.
                            backend.approve_order(oid, confirmed=True)
                            st.success(f"Order #{oid} approved locally.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Couldn't approve this draft: {exc}")
                else:
                    st.caption("Read-only saved order; there is no approval action here.")

    st.write("")
    st.markdown(
        '<div class="ss-orders-important"><strong>Simulation safety:</strong> '
        'Purchase orders are stored locally. A recommendation preview is NOT '
        'a draft. Even an approved local order is not sent to a supplier and '
        'does not automatically alter recorded inventory.</div>',
        unsafe_allow_html=True,
    )
