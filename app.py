"""
DiligencePilot - 硬科技AI投研助手
主入口模块（UI 重构版）
"""
import time

import streamlit as st
from dotenv import load_dotenv

from config import PAGE_TITLE, SPINNER_TEXT
from pdf_utils import extract_text_from_pdf
from analysis_nodes import (
    extract_financials,
    detect_anomalies,
    extract_highlights,
    industry_analysis,
    investment_logic,
    generate_communication_points,
)
from financial_ratios import calculate_ratios
from ui_components import (
    render_financial_tab,
    render_highlights_tab,
    render_anomalies_tab,
    render_industry_tab,
    render_logic_tab,
    render_communication_tab,
)

load_dotenv()

# ── 页面配置 ──
st.set_page_config(page_title=PAGE_TITLE, layout="wide")

# ── 状态初始化 ──
if "page" not in st.session_state:
    st.session_state.page = "home"
if "tab_index" not in st.session_state:
    st.session_state.tab_index = 0

# ── Custom CSS 注入 ──
CSS = """
<style>
/* ===== 全局 ===== */
html, body, .stApp {
    background-color: #f5f6f8 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* ===== 背景山形线 ===== */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 800'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='0' y2='1'%3E%3Cstop offset='0' stop-color='%23e8ecf1'/%3E%3Cstop offset='1' stop-color='%23f5f6f8'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M0,600 C200,550 400,650 600,580 S900,500 1200,560 S1400,620 1440,600 L1440,800 L0,800 Z' fill='url(%23g)'/%3E%3Cpath d='M0,650 C300,580 500,700 800,630 S1100,550 1440,640 L1440,800 L0,800 Z' fill='%23dce1e8' opacity='0.4'/%3E%3Cpath d='M0,700 C400,640 700,760 1000,680 S1300,600 1440,670 L1440,800 L0,800 Z' fill='%23caced6' opacity='0.25'/%3E%3C/svg%3E");
    background-size: cover;
    background-position: center bottom;
    background-repeat: no-repeat;
}

/* ===== 首页内容容器 ===== */
.home-container {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 90vh;
    text-align: center;
    padding: 2rem 1rem;
}

/* ===== Logo 占位 ===== */
.logo-placeholder {
    font-size: 3rem;
    font-weight: 300;
    letter-spacing: 0.3em;
    color: #b0b7c3;
    margin-bottom: 1.2rem;
    text-transform: uppercase;
    user-select: none;
}

/* ===== 大号标语 ===== */
.slogan {
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 700;
    color: #1a1d23;
    margin-bottom: 2.5rem;
    line-height: 1.2;
    letter-spacing: -0.02em;
}

/* ===== 一体化胶囊卡片 ===== */
.capsule-card {
    display: flex;
    align-items: center;
    background: #ffffff;
    border-radius: 60px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04);
    padding: 4px 4px 4px 24px;
    margin: 0 auto;
    width: 100%;
    max-width: 560px;
    transition: box-shadow 0.3s ease;
}
.capsule-card:hover {
    box-shadow: 0 12px 40px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.06);
}
.capsule-left {
    flex: 1;
    min-width: 0;
}
.capsule-left [data-testid="stFileUploader"] {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}
.capsule-left [data-testid="stFileUploader"] > div {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}
.capsule-left [data-testid="stFileUploader"] button {
    display: none !important;
}
.capsule-left [data-testid="stFileUploader"] section {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}
.capsule-left .uploadedFileName {
    display: none !important;
}
.capsule-left label {
    font-size: 0.95rem !important;
    color: #888fa0 !important;
    font-weight: 400 !important;
    padding: 0 !important;
    margin: 0 !important;
    cursor: pointer !important;
    display: block !important;
}
.capsule-right {
    flex-shrink: 0;
    margin-left: 8px;
}
.capsule-right button {
    background: #1a1d23 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 40px !important;
    padding: 0.65rem 2rem !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: background 0.2s ease, transform 0.15s ease !important;
    min-width: 120px;
    height: 44px;
}
.capsule-right button:hover {
    background: #2d3139 !important;
    transform: scale(1.02) !important;
}
.capsule-right button:disabled,
.capsule-right button[disabled] {
    background: #c0c4cc !important;
    cursor: not-allowed !important;
}

/* ===== 3D 悬浮卡片 ===== */
.floating-cards {
    display: flex;
    gap: 20px;
    justify-content: center;
    margin-top: 3rem;
    perspective: 1200px;
    flex-wrap: wrap;
}
.floating-card {
    width: 140px;
    padding: 1.2rem 0.8rem;
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(6px);
    border-radius: 16px;
    text-align: center;
    font-size: 0.85rem;
    font-weight: 500;
    color: #6b7280;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    transform: rotateX(8deg) rotateY(-6deg) translateY(0);
    transition: transform 0.45s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.4s ease;
    cursor: default;
    border: 1px solid rgba(255,255,255,0.5);
}
.floating-card:nth-child(2) {
    transform: rotateX(8deg) rotateY(0deg) translateY(6px);
}
.floating-card:nth-child(3) {
    transform: rotateX(8deg) rotateY(6deg) translateY(0);
}
.floating-card:hover {
    transform: rotateX(0deg) rotateY(0deg) translateY(-12px) !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.12);
    background: rgba(255,255,255,0.95);
}
.floating-card-icon {
    font-size: 1.6rem;
    margin-bottom: 6px;
    display: block;
}

/* ===== 结果页 Tab 导航栏 ===== */
.tab-nav {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #e0e4ea;
    padding: 0;
    margin: 1rem 0 0 0;
    background: transparent;
    position: relative;
    z-index: 1;
}
.tab-item {
    position: relative;
    padding: 0.75rem 1.4rem;
    font-size: 0.9rem;
    font-weight: 500;
    color: #9ca3af;
    cursor: pointer;
    transition: color 0.25s ease;
    border: none;
    background: transparent;
    white-space: nowrap;
    user-select: none;
}
.tab-item::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    width: 0;
    height: 3px;
    background: #1a1d23;
    border-radius: 3px 3px 0 0;
    transition: width 0.3s ease, left 0.3s ease;
}
.tab-item.active {
    color: #1a1d23;
    font-weight: 600;
}
.tab-item.active::after {
    width: 70%;
    left: 15%;
}
.tab-item:hover {
    color: #4b5563;
}

/* ===== 结果内容卡片 ===== */
.result-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-top: 1.2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05), 0 1px 4px rgba(0,0,0,0.03);
    position: relative;
    z-index: 1;
    min-height: 300px;
}

/* ===== 隐藏 Streamlit 默认元素 ===== */
#MainMenu, header, footer, .stDeployButton {
    visibility: hidden;
    display: none !important;
}
.stApp > header {
    display: none !important;
}
.stFileUploaderFile {
    display: none !important;
}
</style>
"""

def render_home_page():
    """首页布局"""
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown('<div class="home-container">', unsafe_allow_html=True)

        # Logo 占位
        st.markdown('<div class="logo-placeholder">◆ LOGO ◆</div>', unsafe_allow_html=True)

        # 主标语
        st.markdown('<div class="slogan">Smart mind for sound investment</div>', unsafe_allow_html=True)

        # 胶囊卡片：上传 + 按钮
        cap_cols = st.columns([3, 1])
        with cap_cols[0]:
            uploaded = st.file_uploader(
                "📄 上传尽调报告 PDF",
                type=["pdf"],
                label_visibility="collapsed",
                key="home_uploader",
            )
        with cap_cols[1]:
            btn_disabled = uploaded is None
            if st.button("开始分析", disabled=btn_disabled, use_container_width=True):
                with st.spinner(SPINNER_TEXT):
                    start_time = time.time()
                    full_text = extract_text_from_pdf(uploaded)
                    if full_text.startswith("PDF解析失败"):
                        st.error(full_text)
                    else:
                        industry_text = industry_analysis(full_text)
                        fin_data, fin_json_str = extract_financials(full_text)
                        ratios = calculate_ratios(fin_data)
                        highlights_text = extract_highlights(full_text, fin_json_str)
                        anomalies_text = detect_anomalies(full_text, fin_json_str)
                        logic_text = investment_logic(full_text, fin_json_str, anomalies_text)
                        communication_text = generate_communication_points(full_text, anomalies_text, logic_text)

                        elapsed = time.time() - start_time

                        st.session_state['full_text'] = full_text
                        st.session_state['industry_text'] = industry_text
                        st.session_state['fin_data'] = fin_data
                        st.session_state['fin_json_str'] = fin_json_str
                        st.session_state['ratios'] = ratios
                        st.session_state['highlights_text'] = highlights_text
                        st.session_state['anomalies_text'] = anomalies_text
                        st.session_state['logic_text'] = logic_text
                        st.session_state['communication_text'] = communication_text
                        st.session_state['elapsed'] = elapsed

                        st.session_state.page = "result"
                        st.rerun()

        # 3D 悬浮卡片
        st.markdown("""
        <div class="floating-cards">
            <div class="floating-card">
                <span class="floating-card-icon">📊</span>
                Financials
            </div>
            <div class="floating-card">
                <span class="floating-card-icon">🔬</span>
                Industry
            </div>
            <div class="floating-card">
                <span class="floating-card-icon">🧠</span>
                Logic
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def render_result_page():
    """结果页布局：自定义 Tab 导航 + 内容区"""
    # Tab 导航栏
    tab_labels = ["行业研究", "财务透视", "异常标记", "投资亮点", "投资逻辑", "沟通清单"]

    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0;position:relative;z-index:1;">
        <span style="font-size:1.5rem;font-weight:700;color:#1a1d23;letter-spacing:-0.03em;">DiligencePilot</span>
        <span style="font-size:0.75rem;color:#9ca3af;font-weight:400;background:#e8ecf1;padding:2px 10px;border-radius:20px;">
            {:.0f}s
        </span>
    </div>
    """.format(st.session_state.get('elapsed', 0)), unsafe_allow_html=True)

    # 用列模拟 Tab 切换
    cols = st.columns(len(tab_labels))
    for i, label in enumerate(tab_labels):
        with cols[i]:
            active_cls = "active" if st.session_state.tab_index == i else ""
            btn_type = "primary" if st.session_state.tab_index == i else "secondary"
            if st.button(label, key=f"tab_btn_{i}", use_container_width=True, type=btn_type):
                st.session_state.tab_index = i
                st.rerun()

    # 内容卡片
    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    tab_idx = st.session_state.tab_index

    if tab_idx == 0:  # 行业研究
        render_industry_tab(st.session_state.get('industry_text', ''))
    elif tab_idx == 1:  # 财务透视
        render_financial_tab(
            st.session_state.get('fin_data'),
            st.session_state.get('ratios'),
        )
    elif tab_idx == 2:  # 异常标记
        render_anomalies_tab(st.session_state.get('anomalies_text', ''))
    elif tab_idx == 3:  # 投资亮点
        render_highlights_tab(st.session_state.get('highlights_text', ''))
    elif tab_idx == 4:  # 投资逻辑
        render_logic_tab(st.session_state.get('logic_text', ''))
    elif tab_idx == 5:  # 沟通清单
        render_communication_tab(st.session_state.get('communication_text', ''))

    st.markdown('</div>', unsafe_allow_html=True)


# ── 页面路由 ──
st.markdown(CSS, unsafe_allow_html=True)

if st.session_state.page == "home":
    render_home_page()
else:
    render_result_page()
