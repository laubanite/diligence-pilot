"""
VestMind - 硬科技AI投研助手
主入口模块
"""
import time
import re
import streamlit as st
from dotenv import load_dotenv

from config import PAGE_TITLE, SPINNER_TEXT
from pdf_utils import extract_text
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
st.set_page_config(page_title="VestMind", layout="wide")

# ── Tab 选中态颜色修正：红色 → 黑色 ──
st.markdown("""
<style>
/* 选中的 Tab 底部下划线颜色变为黑色 */
.stTabs [data-baseweb="tab"] {
    color: #000000;
}
.stTabs [aria-selected="true"] {
    color: #000000 !important;
    border-bottom-color: #000000 !important;
}
/* 鼠标悬停时的底部线也变为黑色（可选） */
.stTabs [data-baseweb="tab"]:hover {
    border-bottom-color: #666666 !important;
}
</style>
""", unsafe_allow_html=True)

# ── 状态初始化 ──
if "page" not in st.session_state:
    st.session_state.page = "home"
if "tab_index" not in st.session_state:
    st.session_state.tab_index = 0

# ── 全局通用 CSS (包含背景图) ──
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
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background-image: url("data:image/svg+xml,%3Csvg width='1396' height='2074' viewBox='0 0 1396 2074' fill='none' xmlns='http://www.w3.org/2000/svg' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9.12701 775.222L105.627 810.222L85.127 825.222L202.627 1144.22L266.627 1220.22V968.222L389.627 1662.22L477.627 1711.72V1562.72L609.127 2066.22L852.127 1287.72L828.627 1536.22L893.127 1515.72L1080.63 968.222L1133.13 1073.72L1314.63 810.222H1288.63L1390.63 775.222M1332.63 759.722L1109.13 382.722L1050.13 483.722L836.627 125.722L777.627 155.222L676.127 3.72198L550.627 211.222H475.127L309.627 578.222L230.627 469.722L75.627 759.722' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M10.1269 773.621C-42.6003 753.209 170.627 768.171 378.627 766.121C613.078 763.81 831.322 765.092 822.627 759.722L953.627 656.722L924.127 522.222L788.127 361.722L861.127 296.722L836.627 127.722L753.127 211.222H735.627L574.627 487.222L655.127 228.722L620.127 211.222L679.627 3.72198L543.627 228.722L477.127 211.222L307.627 623.722L239.627 532.722L119.627 766.222M822.627 759.722C1033.46 757.389 1441.83 756.922 1388.63 773.722' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M1305.97 761.852C1306.74 760.765 1307.51 759.679 1308.29 758.592C1301.81 754.027 1295.34 749.461 1288.86 744.895C1254.21 720.467 1219.57 696.038 1184.92 671.61L1185.22 671.905C1140.3 612.26 1095.38 552.615 1050.47 492.969L1050.4 492.879L1050.29 492.834C1044.45 490.358 1038.61 487.883 1032.76 485.407L1032.9 485.516C1021.27 470.225 1009.64 454.933 998.015 439.642C993.219 433.335 988.423 427.029 983.627 420.722C988.37 427.069 993.113 433.416 997.855 439.763C1009.35 455.151 1020.85 470.54 1032.35 485.928L1032.41 486.002L1032.49 486.037C1038.31 488.561 1044.14 491.086 1049.96 493.61L1049.79 493.475C1094.2 553.496 1138.62 613.517 1183.03 673.539L1183.34 673.834C1217.78 698.553 1252.22 723.273 1286.66 747.992C1293.09 752.612 1299.53 757.232 1305.97 761.852Z' fill='%23E4EAF2'/%3E%3Cpath d='M207.676 759.845C208.643 760.763 209.611 761.681 210.578 762.599C212.544 760.479 214.509 758.359 216.475 756.239C229.821 741.847 243.167 727.455 256.513 713.063L256.669 712.859C263.864 700.774 271.059 688.69 278.254 676.605L278.008 676.85C293.592 667.167 309.176 657.483 324.76 647.8C327.216 646.274 329.671 644.748 332.127 643.222C329.637 644.691 327.147 646.16 324.657 647.629C308.853 656.95 293.05 666.272 277.247 675.594L277 675.839C269.528 687.754 262.057 699.67 254.585 711.585L254.741 711.381C241.067 725.462 227.393 739.543 213.719 753.623C211.705 755.697 209.69 757.771 207.676 759.845Z' fill='%23E4EAF2'/%3E%3Cpath d='M242.702 762.399C243.319 763.948 243.935 765.496 244.552 767.045C250.779 764.529 257.537 761.845 263.933 759.322C310.048 742.145 359.177 719.465 404.308 712.881C404.788 713.904 405.894 714.525 406.822 714.608C407.753 714.705 408.41 714.558 409.123 714.371C409.708 714.21 410.373 713.956 410.96 713.693C411.488 713.457 412.039 713.181 412.613 712.869C414.685 711.734 416.724 710.33 418.583 708.968C422.378 706.171 425.959 703.157 429.484 700.066C436.469 693.912 443.186 687.43 449.751 680.826C462.661 667.446 476.038 654.399 486.355 638.572C501.837 621.147 526.021 612.068 547.278 601.565L547.405 601.473C556.675 591.086 565.945 580.698 575.216 570.31C579.853 565.114 584.49 559.918 589.127 554.722C584.428 559.862 579.729 565.003 575.03 570.143C565.636 580.419 556.243 590.695 546.849 600.971L546.976 600.879C525.42 611.323 501.69 619.343 484.899 637.872C463.279 665.883 434.637 697.585 406.946 711.563C354.323 714.377 309.719 738.771 262.217 754.893C255.779 757.342 248.991 759.949 242.702 762.399Z' fill='%23E4EAF2'/%3E%3Cpath d='M8.62701 774.722C72.627 773.922 462.294 778.389 649.127 780.722C649.127 780.722 678.127 774.722 696.127 774.722C714.127 774.722 747.627 780.722 747.627 780.722H1385.63' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M105.627 812.722L250.627 785.722L643.127 778.222' stroke='%23E4EAF2' stroke-width='4'/%3E%3Cpath d='M1293.63 811.722L1146.13 783.222' stroke='%23E4EAF2' stroke-width='4'/%3E%3C/svg%3E");
    background-size: 500px auto; 
    background-position: center 65%; 
    background-repeat: no-repeat;
    opacity: 0.8;
}
</style>
"""

# ── 首页独占 CSS ──
HOME_CSS = """
<style>
.block-container {
    display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
    min-height: 100vh !important; padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important;
}
.block-container > div[data-testid="stVerticalBlock"] {
    width: 100%; max-width: 800px; display: flex; flex-direction: column; justify-content: center; position: relative; z-index: 1;
}
.hero-text-container { width: 100%; max-width: 680px; margin: 0 auto; text-align: left; }
.logo-placeholder { font-size: 1.25rem; font-weight: 600; letter-spacing: 0.05em; color: #4b5563; margin-bottom: 1.5rem; }
.slogan { font-size: clamp(2.5rem, 4.5vw, 4.2rem); font-weight: 400; color: #1a1d23; margin-bottom: 3.5rem; line-height: 1.15; letter-spacing: -0.02em; }
.investment-italic { font-family: 'Georgia', 'Times New Roman', serif; font-style: italic; font-weight: 400; color: #1a1d23; }

/* ====== 上传区域胶囊容器 ====== */
div[data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) {
    background: #ffffff; border-radius: 60px; box-shadow: 0 10px 40px rgba(0,0,0,0.04), 0 2px 10px rgba(0,0,0,0.02);
    padding: 8px 10px 8px 25px; align-items: center; max-width: 780px; width: 100%;
    margin: 0 auto; border: 1px solid rgba(0,0,0,0.06);
    flex-shrink: 0; overflow: hidden; display: flex !important;
    justify-content: space-between !important; gap: 0 !important;
}

/* 隐藏 Streamlit 原生上传组件 UI */
[data-testid="stFileUploader"] { margin: 0 !important; padding: 0 !important; }
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] { padding: 0 !important; background: transparent !important; border: none !important; min-height: 0 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > div,
[data-testid="stFileUploaderDropzoneInstructions"] > small,
[data-testid="stFileUploaderDropzoneIcon"] { display: none !important; }
[data-testid="stUploadedFile"], .stFileUploaderFile, .stFileUploaderFileData { display: none !important; }

/* 默认态占位文字样式 */
[data-testid="stFileUploaderDropzoneInstructions"]::after {
    content: "Upload a report to start your research...";
    color: #9ca3af; font-size: 1rem; cursor: pointer; display: block; line-height: 44px;
}

/* 文件卡片样式 (阶段2 & 3) */
.file-card {
    display: flex; align-items: center; background: #f4f5f7; border-radius: 40px; 
    padding: 0 16px; height: 44px; gap: 10px; width: 100%;
}
.file-icon { font-size: 1.1rem; }
.file-name { font-size: 0.9rem; font-weight: 500; color: #1a1d23; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px; }
.file-size { font-size: 0.8rem; color: #9ca3af; }

/* 右侧 Analyze / Thinking 按钮 (阶段3 带转圈) */
@keyframes spin { 100% { transform: rotate(360deg); } }
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button {
    background: #1a1d23 !important; color: #ffffff !important;
    border: none !important; border-radius: 40px !important;
    height: 48px !important; padding: 0 2rem !important;
    font-size: 0.95rem !important; font-weight: 500 !important;
    width: 135px !important; cursor: pointer !important;
    display: inline-flex !important; align-items: center !important;
    justify-content: center !important; gap: 8px !important;
    transition: all 0.2s !important;
}

/* 思考态样式锁定 */
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button:disabled {
    cursor: not-allowed !important; opacity: 1 !important;
    background: #1a1d23 !important;
}
/* 动态注入旋转圆圈 */
div[data-testid="stHorizontalBlock"] [data-testid="stButton"] button:disabled div[data-testid="stMarkdownContainer"] p:contains("Thinking")::before {
    content: ""; display: inline-block; width: 14px; height: 14px;
    border: 2px solid rgba(255,255,255,0.3); border-top-color: #ffffff;
    border-radius: 50%; animation: spin 0.8s linear infinite;
    vertical-align: middle; margin-right: 8px;
}

/* 底部图标 */
.features-container { display: flex; gap: 70px; justify-content: center; margin-top: 4.5rem; opacity: 0.7; }
.feature-item { display: flex; flex-direction: column; align-items: center; gap: 12px; color: #6b7280; font-size: 0.85rem; font-weight: 500; }
.feature-icon { width: 24px; height: 24px; stroke: currentColor; stroke-width: 1.5; fill: none; }
</style>
"""

# ── 结果页独占 CSS ──
RESULT_CSS = """
<style>
.block-container { padding-top: 2.5rem !important; max-width: 1300px !important; display: block !important; }
button[key^="rtab_"] { border-radius: 50px !important; border: none !important; transition: all 0.2s ease !important; }
button[key^="rtab_"][kind="secondary"] { background-color: #f1f3f5 !important; color: #6b7280 !important; }
button[key^="rtab_"][kind="primary"] { background-color: #1a1d23 !important; color: #ffffff !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }
.result-card { background: transparent !important; box-shadow: none !important; border: none !important; margin-top: 2rem; padding: 0 !important; }
.toc-container { position: sticky; top: 50px; border-left: 1px solid #e5e7eb; padding-left: 20px; margin-left: 10px; }
.toc-item { font-size: 0.85rem; color: #9ca3af; margin-bottom: 15px; cursor: pointer; text-decoration: none; display: block; }
.toc-item:hover { color: #1a1d23; }
</style>
"""

def generate_toc_html(text):
    """提取 H2 (##) 和 H3 (###) 标题生成目录"""
    if not text:
        return ""
    titles = re.findall(r'^(#{2,3})\s+(.*)', text, re.MULTILINE)
    if not titles: return ""
    html = '<div class="toc-container">'
    for level_mark, title in titles:
        clean_title = title.replace("**", "").strip()
        indent = 15 if level_mark == "###" else 0
        html += f'<div class="toc-item" style="margin-left:{indent}px">{clean_title}</div>'
    html += '</div>'
    return html

def render_home_page():
    """首页布局"""
    st.markdown(COMMON_CSS, unsafe_allow_html=True)
    st.markdown(HOME_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-text-container">
        <div class="logo-placeholder">VestMind</div>
        <div class="slogan">Smart Mind for Sound<br><span class="investment-italic">Investment</span></div>
    </div>
    """, unsafe_allow_html=True)

    # 状态初始化
    if "analyzing" not in st.session_state: st.session_state.analyzing = False
    if "upload_key" not in st.session_state: st.session_state.upload_key = 0
    if "file_info" not in st.session_state: st.session_state.file_info = None

    if st.session_state.get("clear_file", False):
        st.session_state.upload_key += 1
        st.session_state.file_info = None
        st.session_state.file_bytes = None
        st.session_state.clear_file = False
        st.rerun()

    # 胶囊容器布局
    cap_cols = st.columns([4, 1])

    with cap_cols[0]:
        # 阶段 1：默认态
        if st.session_state.file_info is None:
            upload_key = f"home_uploader_{st.session_state.upload_key}"
            uploaded = st.file_uploader("Upload", type=["pdf", "docx"],
                                        label_visibility="collapsed", key=upload_key)
            if uploaded is not None:
                size = uploaded.size
                size_str = f"{size/(1024*1024):.1f} MB" if size >= 1024*1024 else f"{size/1024:.1f} KB"
                st.session_state.file_info = {"name": uploaded.name, "size": size_str}
                st.session_state.file_bytes = uploaded.read()
                st.rerun()
        # 阶段 2 & 3：显示文件卡片
        else:
            file = st.session_state.file_info
            l2, r2 = st.columns([12, 1])
            with l2:
                # 替换为 SVG 图标并调整了卡片颜色与透明度
                st.markdown(f"""
                <div class="file-card" style="background: rgba(248, 249, 250, 0.7) !important; border: 1px solid rgba(0,0,0,0.03);">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                        <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M14 2V8H20" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M16 13H8" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M16 17H8" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M10 9H8" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span class="file-name" style="color: #4b5563;">{file["name"]}</span>
                    <span class="file-size" style="color: #9ca3af; margin-left: 8px;">{file["size"]}</span>
                </div>
                """, unsafe_allow_html=True)
            with r2:
                # 只有在非分析状态下才允许删除文件
                if not st.session_state.analyzing:
                    if st.button("✕", key="remove_file", help="移除文件"):
                        st.session_state.clear_file = True
                        st.rerun()

    with cap_cols[1]:
        # 阶段 3：点击后按钮变为 Thinking... 样式由 CSS 控制自动添加圆圈
        is_analyzing = st.session_state.analyzing
        btn_label = "Thinking..." if is_analyzing else "Analyze"
        btn_disabled = (st.session_state.file_info is None) or is_analyzing
        
        if st.button(btn_label, disabled=btn_disabled, key="analyze_btn", use_container_width=True):
            st.session_state.analyzing = True
            st.rerun()

    # 分析逻辑
    if st.session_state.analyzing and st.session_state.get("file_bytes"):
        from io import BytesIO
        fname = st.session_state.file_info["name"]
        fbytes = st.session_state.file_bytes
        class FakeUpload:
            name = fname
            def read(self): return fbytes
            size = len(fbytes)
        uploaded_obj = FakeUpload()

        # 分析过程
        start_time = time.time()
        full_text = extract_text(uploaded_obj)
        if full_text.startswith("PDF解析失败") or full_text.startswith("DOCX解析失败"):
            st.error(full_text)
            st.session_state.analyzing = False
            st.rerun()
        else:
            st.session_state['industry_text'] = industry_analysis(full_text)
            fin_data, fin_json_str = extract_financials(full_text)
            st.session_state['fin_data'] = fin_data
            st.session_state['ratios'] = calculate_ratios(fin_data)
            st.session_state['highlights_text'] = extract_highlights(full_text, fin_json_str)
            st.session_state['anomalies_text'] = detect_anomalies(full_text, fin_json_str)
            st.session_state['logic_text'] = investment_logic(full_text, fin_json_str, st.session_state['anomalies_text'])
            st.session_state['communication_text'] = generate_communication_points(full_text, st.session_state['anomalies_text'], st.session_state['logic_text'])
            st.session_state['elapsed'] = time.time() - start_time
            st.session_state.analyzing = False
            st.session_state.page = "result"
            st.rerun()

    # 底部图标
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
    """结果页布局 (内容+右侧目录)"""
    st.markdown(RESULT_CSS, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;">
        <span style="font-size:1.5rem;font-weight:700;color:#1a1d23;">VestMind</span>
        <span style="font-size:0.75rem;color:#9ca3af;background:#e8ecf1;padding:2px 10px;border-radius:20px;">{st.session_state.get('elapsed', 0):.0f}s</span>
    </div>
    """, unsafe_allow_html=True)

    tab_labels = ["行业研究", "财务透视", "异常标记", "投资亮点", "投资逻辑", "沟通清单"]
    active_idx = st.session_state.tab_index

    cols = st.columns(len(tab_labels))
    for i, label in enumerate(tab_labels):
        with cols[i]:
            is_active = i == active_idx
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"rtab_{i}", use_container_width=True, type=btn_type):
                st.session_state.tab_index = i
                st.rerun()

    main_col, toc_col = st.columns([4, 1])
    content_text = ""
    tab_idx = st.session_state.tab_index
    
    with main_col:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        if tab_idx == 0:
            content_text = render_industry_tab(st.session_state.get('industry_text', ''))
        elif tab_idx == 1:
            render_financial_tab(st.session_state.get('fin_data'), st.session_state.get('ratios'))
        elif tab_idx == 2:
            content_text = render_anomalies_tab(st.session_state.get('anomalies_text', ''))
        elif tab_idx == 3:
            content_text = render_highlights_tab(st.session_state.get('highlights_text', ''))
        elif tab_idx == 4:
            content_text = render_logic_tab(st.session_state.get('logic_text', ''))
        elif tab_idx == 5:
            content_text = render_communication_tab(st.session_state.get('communication_text', ''))
        st.markdown('</div>', unsafe_allow_html=True)

    with toc_col:
        if content_text:
            st.markdown(generate_toc_html(content_text), unsafe_allow_html=True)

# ── 页面路由 ──
if st.session_state.page == "home":
    render_home_page()
else:
    render_result_page()