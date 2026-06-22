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

# ── 全局通用 CSS ──
COMMON_CSS = """
<style>
/* 全局页面背景与字体 */
html, body, .stApp {
    background-color: #fafbfc !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* 隐藏 Streamlit 默认头部和底部元素 */
#MainMenu, header, footer, .stDeployButton {
    visibility: hidden;
    display: none !important;
}
.stApp > header {
    display: none !important;
}

.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    
    /* 全局替换为适配图2的浅冷灰色（浅蓝灰） */
    background-image: url("data:image/svg+xml,%3Csvg width='1396' height='2074' viewBox='0 0 1396 2074' fill='none' xmlns='http://www.w3.org/2000/svg' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9.12701 775.222L105.627 810.222L85.127 825.222L202.627 1144.22L266.627 1220.22V968.222L389.627 1662.22L477.627 1711.72V1562.72L609.127 2066.22L852.127 1287.72L828.627 1536.22L893.127 1515.72L1080.63 968.222L1133.13 1073.72L1314.63 810.222H1288.63L1390.63 775.222M1332.63 759.722L1109.13 382.722L1050.13 483.722L836.627 125.722L777.627 155.222L676.127 3.72198L550.627 211.222H475.127L309.627 578.222L230.627 469.722L75.627 759.722' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M10.1269 773.621C-42.6003 753.209 170.627 768.171 378.627 766.121C613.078 763.81 831.322 765.092 822.627 759.722L953.627 656.722L924.127 522.222L788.127 361.722L861.127 296.722L836.627 127.722L753.127 211.222H735.627L574.627 487.222L655.127 228.722L620.127 211.222L679.627 3.72198L543.627 228.722L477.127 211.222L307.627 623.722L239.627 532.722L119.627 766.222M822.627 759.722C1033.46 757.389 1441.83 756.922 1388.63 773.722' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M1305.97 761.852C1306.74 760.765 1307.51 759.679 1308.29 758.592C1301.81 754.027 1295.34 749.461 1288.86 744.895C1254.21 720.467 1219.57 696.038 1184.92 671.61L1185.22 671.905C1140.3 612.26 1095.38 552.615 1050.47 492.969L1050.4 492.879L1050.29 492.834C1044.45 490.358 1038.61 487.883 1032.76 485.407L1032.9 485.516C1021.27 470.225 1009.64 454.933 998.015 439.642C993.219 433.335 988.423 427.029 983.627 420.722C988.37 427.069 993.113 433.416 997.855 439.763C1009.35 455.151 1020.85 470.54 1032.35 485.928L1032.41 486.002L1032.49 486.037C1038.31 488.561 1044.14 491.086 1049.96 493.61L1049.79 493.475C1094.2 553.496 1138.62 613.517 1183.03 673.539L1183.34 673.834C1217.78 698.553 1252.22 723.273 1286.66 747.992C1293.09 752.612 1299.53 757.232 1305.97 761.852Z' fill='%23E4EAF2'/%3E%3Cpath d='M207.676 759.845C208.643 760.763 209.611 761.681 210.578 762.599C212.544 760.479 214.509 758.359 216.475 756.239C229.821 741.847 243.167 727.455 256.513 713.063L256.669 712.859C263.864 700.774 271.059 688.69 278.254 676.605L278.008 676.85C293.592 667.167 309.176 657.483 324.76 647.8C327.216 646.274 329.671 644.748 332.127 643.222C329.637 644.691 327.147 646.16 324.657 647.629C308.853 656.95 293.05 666.272 277.247 675.594L277 675.839C269.528 687.754 262.057 699.67 254.585 711.585L254.741 711.381C241.067 725.462 227.393 739.543 213.719 753.623C211.705 755.697 209.69 757.771 207.676 759.845Z' fill='%23E4EAF2'/%3E%3Cpath d='M242.702 762.399C243.319 763.948 243.935 765.496 244.552 767.045C250.779 764.529 257.537 761.845 263.933 759.322C310.048 742.145 359.177 719.465 404.308 712.881C404.788 713.904 405.894 714.525 406.822 714.608C407.753 714.705 408.41 714.558 409.123 714.371C409.708 714.21 410.373 713.956 410.96 713.693C411.488 713.457 412.039 713.181 412.613 712.869C414.685 711.734 416.724 710.33 418.583 708.968C422.378 706.171 425.959 703.157 429.484 700.066C436.469 693.912 443.186 687.43 449.751 680.826C462.661 667.446 476.038 654.399 486.355 638.572C501.837 621.147 526.021 612.068 547.278 601.565L547.405 601.473C556.675 591.086 565.945 580.698 575.216 570.31C579.853 565.114 584.49 559.918 589.127 554.722C584.428 559.862 579.729 565.003 575.03 570.143C565.636 580.419 556.243 590.695 546.849 600.971L546.976 600.879C525.42 611.323 501.69 619.343 484.899 637.872C463.279 665.883 434.637 697.585 406.946 711.563C354.323 714.377 309.719 738.771 262.217 754.893C255.779 757.342 248.991 759.949 242.702 762.399Z' fill='%23E4EAF2'/%3E%3Cpath d='M8.62701 774.722C72.627 773.922 462.294 778.389 649.127 780.722C649.127 780.722 678.127 774.722 696.127 774.722C714.127 774.722 747.627 780.722 747.627 780.722H1385.63' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M105.627 812.722L250.627 785.722L643.127 778.222' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M1293.63 811.722L1146.13 783.222' stroke='%23E4EAF2' stroke-width='4'/%3E%3C/svg%3E");
    
    /* 调整长宽比：使用宽 x 高的形式，强制压扁成“矮胖”比例，您可以微调 900px 和 450px 的数值 */
    background-size: 500px auto; 
    background-position: center 55%; 
    background-repeat: no-repeat;
    opacity: 0.8;
}
"""

# ── 首页独占 CSS (解决居中和内嵌框) ──
HOME_CSS = """
<style>
/* 1. 彻底消灭滚动条，强制垂直居中 */
.block-container {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 100vh !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}
.block-container > div[data-testid="stVerticalBlock"] {
    width: 100%;
    max-width: 800px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    z-index: 1;
}

/* 文本与 Logo 样式：使用统一宽度容器，整体居中，但内部文字全部左对齐 */
.hero-text-container {
    width: 100%;
    max-width: 680px; /* 和下方长条胶囊保持一致，以实现完美的左边缘对齐 */
    margin: 0 auto;
    text-align: left; 
}
.logo-placeholder {
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: #4b5563;
    margin-bottom: 1.5rem;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    user-select: none;
}
.slogan {
    font-size: clamp(2.5rem, 4.5vw, 4.2rem);
    font-weight: 400;
    color: #1a1d23;
    margin-bottom: 3.5rem;
    line-height: 1.15;
    letter-spacing: -0.02em;
}
.investment-italic {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-style: italic;
    font-weight: 400;
    color: #1a1d23;
}

/* ========================================================================= */
/* 2. 黑魔法：劫持 Streamlit 原生布局容器，变成完整的内嵌式胶囊框 */
/* ========================================================================= */
div[data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) {
    background: #ffffff;
    border-radius: 60px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.04), 0 2px 10px rgba(0,0,0,0.02);
    padding: 8px 8px 8px 26px; 
    align-items: center;
    max-width: 680px;
    margin: 0 auto;
    border: 1px solid rgba(0,0,0,0.04);
}

[data-testid="stFileUploader"] { margin-bottom: 0 !important; }
[data-testid="stFileUploader"] > div { padding: 0 !important; }

[data-testid="stFileUploader"] section { 
    padding: 0 !important; 
    background: transparent !important; 
    border: none !important;
    min-height: 48px !important;
    display: flex;
    align-items: center;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div,
[data-testid="stFileUploaderDropzoneIcon"] { display: none !important; }

[data-testid="stFileUploaderDropzoneInstructions"] { 
    display: flex !important; 
    margin: 0 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"]::before {
    content: "Upload a PDF report or give any task...";
    color: #9ca3af;
    font-size: 1.05rem;
    font-weight: 400;
}

[data-testid="stUploadedFile"] {
    background: #f4f5f7 !important;
    border-radius: 40px !important;
    padding: 4px 16px !important;
    margin-top: 0 !important;
    border: none !important;
}

div[data-testid="stHorizontalBlock"] [data-testid="column"]:last-child {
    display: flex;
    justify-content: flex-end;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button {
    background: #1a1d23 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 40px !important;
    height: 48px !important; 
    padding: 0 2.2rem !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    width: 100%;
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button:hover {
    background: #000000 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button:disabled {
    background: #f0f2f5 !important;
    color: #a0a5b0 !important;
    transform: none !important;
    cursor: not-allowed !important;
}

/* 底部极简线条图标 */
.features-container {
    display: flex;
    gap: 70px;
    justify-content: center;
    margin-top: 4.5rem;
    opacity: 0.7;
}
.feature-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    color: #6b7280;
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.3s ease;
    cursor: default;
}
.feature-item:hover {
    opacity: 1;
    color: #1a1d23;
    transform: translateY(-2px);
}
.feature-icon {
    width: 24px;
    height: 24px;
    stroke: currentColor;
    stroke-width: 1.5;
    fill: none;
    stroke-linecap: round;
    stroke-linejoin: round;
}
</style>
"""

# ── 结果页独占 CSS (恢复正常顶部间距) ──
RESULT_CSS = """
<style>
.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
    display: block !important;
}

/* 结果页 Tab 导航栏 */
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

/* 结果内容卡片 */
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
</style>
"""

def render_home_page():
    """首页布局"""
    st.markdown(HOME_CSS, unsafe_allow_html=True)
    
    # 将文本包裹在指定的对齐容器内，完美实现图2的左边缘对齐且支持换行
    st.markdown("""
    <div class="hero-text-container">
        <div class="logo-placeholder">VestMind</div>
        <div class="slogan">Smart Mind for Sound<br><span class="investment-italic">Investment</span></div>
    </div>
    """, unsafe_allow_html=True)

    # 用原生 st.columns 构建布局，CSS 会自动把这一行变成"一个胶囊"
    cap_cols = st.columns([3, 1])
    
    with cap_cols[0]:
        uploaded = st.file_uploader(
            "Placeholder", # CSS 已劫持并替换了这里的文案，所以这里写什么不重要
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

    # 极简线框图标特征区
    st.markdown("""
    <div class="features-container">
        <div class="feature-item">
            <svg class="feature-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
                <polyline points="16 7 22 7 22 13"></polyline>
            </svg>
            Financials
        </div>
        <div class="feature-item">
            <svg class="feature-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 17 12 22 22 17"></polyline>
                <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
            Industry
        </div>
        <div class="feature-item">
            <svg class="feature-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <circle cx="18" cy="5" r="3"></circle>
                <circle cx="6" cy="12" r="3"></circle>
                <circle cx="18" cy="19" r="3"></circle>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
            Logic
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_result_page():
    """结果页布局：自定义 Tab 导航 + 内容区"""
    st.markdown(RESULT_CSS, unsafe_allow_html=True)
    
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
st.markdown(COMMON_CSS, unsafe_allow_html=True)

if st.session_state.page == "home":
    render_home_page()
else:
    render_result_page()