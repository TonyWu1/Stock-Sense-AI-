"""StockSense AI Assistant — dark premium UI, same StockSenseAgent behavior.

This is a simulated Alexa+-inspired web experience, not an Amazon Alexa service.
The real LLM chat is available only when OPENAI_API_KEY is configured.
All business actions remain delegated to StockSenseAgent and InventoryBackend.
"""
from __future__ import annotations

import os
from html import escape

import streamlit as st
from dotenv import load_dotenv
from agent import StockSenseAgent
from backend_adapter import InventoryBackend

load_dotenv()


def get_session_agent() -> StockSenseAgent | None:
    """One agent per browser session; local SQLite remains shared."""
    token = os.getenv("OPENAI_API_KEY", "").strip()
    if not token or token == "your_api_key_here":
        return None
    if "stocksense_agent" not in st.session_state:
        st.session_state.stocksense_agent = StockSenseAgent()
    return st.session_state.stocksense_agent


ASSISTANT_CSS = """
<style>
body:has(.ss-ai-page-marker) .stApp,
body:has(.ss-ai-page-marker) [data-testid="stHeader"] {background:#0b1423 !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] {background:#0c1828 !important;border-right:1px solid #1a3047 !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] .ss-brand-name {color:white !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] .ss-brand-name span {color:#4addff !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] [role="radiogroup"] label p {color:#c0cee1 !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {background:#1562bd !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p {color:white !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] .ss-side-foot {background:#122b43 !important;border-color:#264760 !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] .ss-side-title {color:#e7f2ff !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] .ss-side-description {color:#a1b6ce !important;}
body:has(.ss-ai-page-marker) [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#b6c8df !important;}
body:has(.ss-ai-page-marker) .block-container {max-width:1500px !important;}
body:has(.ss-ai-page-marker) [data-testid="stChatMessage"] {background:#12243a !important;border:1px solid #244057 !important;border-radius:14px;padding:16px;margin-bottom:11px;}
body:has(.ss-ai-page-marker) [data-testid="stChatMessage"] p,
body:has(.ss-ai-page-marker) [data-testid="stChatMessage"] li {color:#e2eaf4 !important;}
body:has(.ss-ai-page-marker) [data-testid="stChatInput"] {background:#152a41 !important;border:1px solid #2a4d67 !important;}
body:has(.ss-ai-page-marker) [data-testid="stChatInput"] textarea {color:#e9f2ff !important;}
body:has(.ss-ai-page-marker) [data-testid="stWidgetLabel"] p {color:#d8e7f8 !important;}
body:has(.ss-ai-page-marker) [data-testid="stCheckbox"] p {color:#e7f1ff !important;}
body:has(.ss-ai-page-marker) [data-testid="stVerticalBlockBorderWrapper"] {border-color:#213d56 !important;}
.ss-ai-header {display:flex;align-items:center;justify-content:space-between;gap:20px;margin:8px 0 18px;}
.ss-ai-header h1 {color:#f5f8ff !important;margin:0;font-size:33px;font-weight:830;letter-spacing:-.045em;}
.ss-ai-header p {color:#8fabc6;margin:6px 0 0;font-size:12px;}
.ss-ai-status {font-size:11px;color:#b4ccdf;background:#173149;border:1px solid #2b4c64;border-radius:100px;padding:9px 13px;white-space:nowrap;}
.ss-ai-status i {display:inline-block;margin-right:7px;width:7px;height:7px;border-radius:50%;background:#23d2a9;}
.ss-ai-headpanel {background:#101e31;border:1px solid #23425c;border-radius:15px;padding:22px;margin-bottom:15px;}
.ss-ai-headpanel h2 {color:#f3f8ff !important;font-size:20px;font-weight:810;margin:0 0 6px;letter-spacing:-.03em;}
.ss-ai-headpanel p {font-size:12px;color:#9db6ce;line-height:1.6;margin:0;}
.ss-ai-empty {min-height:250px;background:linear-gradient(135deg,#101e31,#122e4c);border:1px solid #264763;border-radius:16px;display:flex;align-items:center;justify-content:center;text-align:center;padding:35px;margin:12px 0 16px;}
.ss-ai-empty strong {color:white;font-size:22px;display:block;margin:9px 0;}
.ss-ai-empty p {color:#9ebcd5;font-size:13px;line-height:1.65;max-width:440px;margin:auto;}
.ss-ai-emblem {height:56px;width:56px;background:linear-gradient(135deg,#1475da,#21b5ed);border-radius:18px;display:grid;place-items:center;color:white;font-size:26px;margin:0 auto;}
.ss-ai-chat-tip {color:#9bb6d0;font-size:11px;margin-bottom:17px;line-height:1.5;}
.ss-ai-prompt {color:#bfdbf4;border:1px solid #2b4b63;background:#122c43;border-radius:9px;padding:10px 13px;font-size:12px;margin-top:8px;}
.ss-ai-aside {background:#101e31;border:1px solid #244059;border-radius:15px;padding:20px;margin-bottom:13px;}
.ss-ai-aside h3 {color:#eaf4ff !important;font-size:18px;margin:0 0 5px;}
.ss-ai-aside p {color:#8cabc6;font-size:11px;margin:0 0 15px;}
.ss-ai-aside-row {display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid #203d56;gap:12px;}
.ss-ai-aside-row:last-child {border:0;}
.ss-ai-aside-row span {color:#acc4db;font-size:12px;}
.ss-ai-aside-row strong {color:#f3faff;font-weight:800;font-size:23px;}
.ss-ai-sidebar-risk {margin-bottom:17px;}
.ss-ai-sidebar-risk .label {display:flex;justify-content:space-between;color:#bed5e9;font-size:11px;margin-bottom:8px;gap:10px;}
.ss-ai-sidebar-risk .bar {height:7px;background:#1c3751;border-radius:90px;overflow:hidden;}
.ss-ai-sidebar-risk .bar div {height:100%;border-radius:90px;background:linear-gradient(90deg,#2cbdeb,#1971e0);}
.ss-ai-caution {background:#14283d;border:1px solid #27516a;border-radius:12px;padding:13px 15px;color:#a9c3d9;font-size:11px;line-height:1.65;}
.ss-ai-offline {background:#142d43;border:1px solid #27627d;border-radius:12px;padding:13px 17px;color:#b7d4e8;font-size:12px;line-height:1.65;}
.ss-ai-offline strong {color:#ffffff;}
@media (max-width:760px){.ss-ai-header{align-items:flex-start;flex-direction:column}.ss-ai-header h1{font-size:27px}}
</style>
<div class="ss-ai-page-marker"></div>
"""


def render_assistant_page() -> None:
    st.markdown(ASSISTANT_CSS, unsafe_allow_html=True)
    backend = InventoryBackend()
    backend.initialize()
    inventory = backend.get_inventory()
    low = backend.get_low_stock()
    orders = backend.get_orders()
    drafts = sum(o.get("status") == "draft" for o in orders)
    healthy = max(0, len(inventory) - len(low))

    agent = get_session_agent()
    connection = "AI connected" if agent is not None else "AI awaiting API key"
    st.markdown(
        '<div class="ss-ai-header"><div><h1>StockSense Assistant</h1>'
        '<p>Alexa+-inspired text simulation · real SQLite tools · no Alexa service connection</p>'
        f'</div><span class="ss-ai-status"><i></i>{escape(connection)}</span></div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.8, 0.95], gap="medium")
    with left:
        st.markdown(
            '<div class="ss-ai-headpanel"><h2>Inventory conversations</h2>'
            '<p>Ask a business question. When the model is enabled, the agent calls your existing '
            'inventory tools and saves only the drafts you explicitly request.</p></div>',
            unsafe_allow_html=True,
        )
        if agent is None:
            st.markdown(
                '<div class="ss-ai-empty"><div>'
                '<div class="ss-ai-emblem">✦</div>'
                '<strong>Your business assistant, one connection away.</strong>'
                '<p>The rest of StockSense AI works offline. Add an OpenAI API key in '
                '<code>.env</code> when ready to enable conversational tool calling.</p>'
                '</div></div>'
                '<div class="ss-ai-offline"><strong>Offline mode</strong> · '
                'Dashboard, Decision Lab, inventory and manual draft approvals work without an API key. '
                'No AI responses are simulated as if they came from a real model.</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("＋ New conversation", key="ai_new_chat_premium"):
                agent.reset()
                st.rerun()
            if not agent.ui_messages:
                st.markdown(
                    '<div class="ss-ai-empty"><div><div class="ss-ai-emblem">✦</div>'
                    '<strong>Ask StockSense anything about inventory.</strong>'
                    '<p>Start with a low-stock question or run a cash-aware restocking scenario.</p>'
                    '</div></div>', unsafe_allow_html=True,
                )
            for message in agent.ui_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if agent.pending_order_id is not None:
                order = agent.backend.get_order(agent.pending_order_id)
                if order and order["status"] == "draft":
                    with st.container(border=True):
                        st.markdown(f"### Review local draft #{order['order_id']}")
                        st.markdown(f"**Total: ${order['total_cost']:.2f}**")
                        st.dataframe(order["items"], hide_index=True, width="stretch")
                        st.caption("This approval only changes local SQLite status; no supplier order is sent.")
                        approved = st.checkbox(
                            f"I explicitly approve LOCAL draft #{order['order_id']}.",
                            key=f"premium_agent_approval_{order['order_id']}",
                        )
                        yes, no = st.columns(2)
                        with yes:
                            if st.button("Approve local draft", key="premium_confirm_ai", type="primary",
                                         disabled=not approved, width="stretch"):
                                answer = agent.confirm_order(order["order_id"])
                                agent.ui_messages.append({"role": "assistant", "content": answer})
                                st.rerun()
                        with no:
                            if st.button("Not now", key="premium_decline_ai", width="stretch"):
                                agent.pending_order_id = None
                                agent.awaiting_confirmation = False
                                agent.ui_messages.append({"role": "assistant", "content":
                                    "The draft remains saved and was NOT approved."})
                                st.rerun()
            prompt = st.chat_input("Ask about inventory, sales, or a restock budget…")
            if prompt:
                agent.chat(prompt)
                st.rerun()

        st.markdown(
            '<div class="ss-ai-chat-tip" style="margin-top:19px">SUGGESTED QUESTIONS</div>'
            '<div class="ss-ai-prompt">Which products are low on stock?</div>'
            '<div class="ss-ai-prompt">What should I restock with a $50 budget?</div>'
            '<div class="ss-ai-prompt">Prepare a smart restock order under $150.</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div class="ss-ai-aside"><h3>Live business signals</h3>'
            '<p>Read directly from your local SQLite inventory</p>'
            f'<div class="ss-ai-aside-row"><span>Catalog products</span><strong>{len(inventory):,}</strong></div>'
            f'<div class="ss-ai-aside-row"><span>Low-stock alerts</span><strong>{len(low):,}</strong></div>'
            f'<div class="ss-ai-aside-row"><span>Products above target</span><strong>{healthy:,}</strong></div>'
            f'<div class="ss-ai-aside-row"><span>Drafts awaiting approval</span><strong>{drafts:,}</strong></div>'
            '</div>', unsafe_allow_html=True,
        )
        # No made-up chart history. Bars represent actual stock/reorder ratios.
        risk_rows = sorted(low, key=lambda p: int(p["stock_quantity"]) / max(1, int(p["reorder_level"])))[:4]
        bar_html = "".join(
            '<div class="ss-ai-sidebar-risk"><div class="label">'
            f'<span>{escape(str(p["name"]))}</span>'
            f'<span>{int(p["stock_quantity"])} / {int(p["reorder_level"])}</span></div>'
            '<div class="bar"><div style="width:'
            f'{max(0, min(100, round(100 * int(p["stock_quantity"]) / max(1, int(p["reorder_level"])))))}%'
            '"></div></div></div>' for p in risk_rows
        )
        st.markdown(
            '<div class="ss-ai-aside"><h3>Items at risk</h3><p>Stock relative to reorder threshold</p>'
            + (bar_html or '<p>No current low-stock products.</p>') + '</div>'
            '<div class="ss-ai-caution">All sample lead times and shelf lives are assumptions. '
            'This is a simulated Alexa+-inspired experience, not a connection to Amazon Alexa. '
            'Local approvals do not send real supplier orders.</div>',
            unsafe_allow_html=True,
        )
