import streamlit as st
import os
import pymupdf
import pandas as pd
import plotly.express as px
import requests
import json
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

st.set_page_config(page_title="DiligencePilot Demo | 硬科技AI投研助手", layout="wide")

st.title("DiligencePilot Demo | 硬科技AI投研助手")
st.subheader("聚焦半导体、新能源、高端制造 · 7维投资逻辑框架")

def extract_text_from_pdf(uploaded_file):
    """
    从前端上传的 PDF 文件读取纯文本。
    """
    try:
        # Pymupdf 接受二进制流并解析
        doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for i, page in enumerate(doc):
            text = page.get_text()
            full_text += f"\n\n[page_{i+1}]\n{text}"
        return full_text.strip()
    except Exception as e:
        return f"PDF解析失败: {str(e)}"

def call_llm(system_prompt, user_prompt, json_mode=False):
    """
    通用大模型请求函数。直接通过 requests 发送 HTTP POST。
    """
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    
    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if json_mode:
        system_prompt += "\n只返回合法JSON，不要任何其他文字。"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        print("===== API DEBUG =====")
        print("Status Code:", response.status_code)
        print("Response Body:", response.text[:500])
        print("=====================")
        
        response.raise_for_status() # 检测非200状态码
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"LLM调用出错: {str(e)}"

def extract_financials(full_text):
    """
    分析节点一：从报告全文中提取3年核心财务数据。
    """
    system_prompt = """你是一位硬科技赛道财务分析师。从以下尽调报告中提取近三个完整财年的核心财务数据。返回严格的JSON，不要任何解释。
JSON格式：
{
  "years": ["2023","2024","2025"],
  "revenue": [数字,数字,数字],
  "gross_margin": [百分比数字,数字,数字],
  "rd_expense": [数字,数字,数字],
  "rd_capitalization_rate": [百分比数字,数字,数字],
  "net_profit": [数字,数字,数字],
  "operating_cash_flow": [数字,数字,数字],
  "capex": [数字,数字,数字],
  "accounts_receivable": [数字,数字,数字],
  "inventory": [数字,数字,数字],
  "government_subsidy": [数字,数字,数字],
  "revenue_top5_customer_share": [百分比数字,数字,数字]
}
特殊说明：关于"rd_capitalization_rate"（研发资本化率）：请先尝试从报告中提取“研发费用资本化金额”和“总研发投入”（或“研发费用合计”）。如果两项都提取到，且总研发投入不为零，请计算 资本化金额 / 总研发投入 * 100 作为百分比填入；如果只提取到费用化研发支出，没有资本化金额，或者完全没有研发数据，该字段必须填 null，严禁编造。

未找到的字段填null。只返回JSON。所有数字必须来自报告，计算逻辑需明确，不要使用外部知识。"""
    
    user_prompt = full_text
    
    # 强制开启 json_mode
    response_text = call_llm(system_prompt, user_prompt, json_mode=True)
    
    # 防呆解析 JSON
    try:
        if response_text.startswith("LLM调用出错"):
            raise ValueError(response_text)
            
        # 尝试清洗返回的文本（有时候大模型可能会带上 markdown 也就是 ```json...```）
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        return json.loads(clean_text.strip()), response_text
    except Exception as e:
        print(f"JSON解析失败: {e}\n原始返回内容: \n{response_text}")
        return {}, response_text

def detect_anomalies(full_text, financial_json_str):
    """
    分析节点二：财务与经营异常检测。
    """
    system_prompt = """你是PE硬科技尽调专家。基于财务数据和报告全文，找出最多3个最显著的财务或经营异常信号。优先关注：
- 收入质量：应收增速远超收入增速；大客户依赖度过高（>50%）。
- 毛利率异常：剧烈波动，与行业技术成熟度不符。
- 研发资本化：资本化率过高（>50%），或研发投入与核心技术产出不匹配。
- 产能与资产：新增产能资本开支异常，固定资产周转率下降但无合理解释。
- 补贴依赖：政府补助占净利润比例过高（>50%），或补贴政策即将到期。
- 现金流：净利润为正但经营现金流持续为负。

对每个异常严格按以下格式输出，不要输出任何其他内容：
**异常点1**
- 异常描述：（一句话）
- 数据对比：（具体年份和数字）
- 原文依据：（引用报告原文1-2句，标明页码如[page_8]）
- 风险等级：高/中

**异常点2**
..."""

    user_prompt = f"报告全文：{full_text}\n\n提取的财务数据：{financial_json_str}"
    
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text

def investment_logic(full_text, financial_json_str, anomalies_text):
    """
    分析节点三：投资逻辑梳理（7维框架）
    """
    system_prompt = """你是一位顶级硬科技VC合伙人，正在为投委会撰写投资逻辑摘要。请基于尽调报告全文、财务数据和已发现的异常，从以下7个维度梳理投资逻辑，每个维度2-3句分析，信息不足时基于行业常识推测，并在句末标注（推测）。最后给出综合判断。

维度：
1. 产业周期：公司是否处在正确的时间窗口？产业处于导入期/加速期/成熟期？政策或技术换代驱动力？
2. 技术壁垒：技术方案的护城河？专利、工艺know-how、团队背景、研发投入强度？被快速复制的风险？
3. 客户价值：产品解决产业链多痛的问题？付费意愿、转换成本、标杆客户验证？
4. 团队执行力：团队能否将技术转化为商业成功？产业化经验、供应链管理能力、商务拓展记录？
5. 市场TAM：市场空间是否足够大以容纳高估值？可服务市场规模、渗透率趋势、行业增速？
6. 财务模型：商业模式是否清晰？毛利率、研发效率、资本效率能否支撑到盈亏平衡点？现金流断裂风险？
7. 退出路径：为资本提供的退出通道？上市路径（科创板/创业板/海外）或被并购价值？当前估值回报空间？

输出格式（严格Markdown）：
## 投资逻辑框架
### 1. 产业周期
...
### 2. 技术壁垒
...
### 3. 客户价值
...
### 4. 团队执行力
...
### 5. 市场TAM
...
### 6. 财务模型
...
### 7. 退出路径
...
**综合判断**：（一句话总结投资逻辑是否成立，关键支撑点和最大风险）"""

    user_prompt = f"报告全文：{full_text}\n\n财务数据：{financial_json_str}\n\n已发现异常：{anomalies_text}"
    
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text

def generate_questions(full_text, anomalies_text, logic_text):
    """
    分析节点四：投委必问
    """
    system_prompt = """你是一位顶级硬科技VC合伙人，正要面试被投企业的创始人与CEO。基于尽调报告、已发现的异常和投资逻辑梳理，生成5个最尖锐、最直击要害的必问问题。语气老练、直接，覆盖技术、产能、收入质量、补贴依赖、财务模型、退出等关键点。
输出格式：
1. 问题一
2. 问题二
..."""

    user_prompt = f"报告全文：{full_text}\n\n异常点：{anomalies_text}\n\n投资逻辑：{logic_text}"
    
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text

if __name__ == "__main__":
    uploaded_file = st.file_uploader("支持文字型PDF，分析时长约60秒", type=["pdf"])
    
    if not uploaded_file:
        st.info("👈 请上传一份硬科技公司的尽调报告PDF，然后点击“开始分析”。")
    else:
        if st.button("开始分析"):
            with st.spinner("正在解析报告并调用AI分析，预计1分钟..."):
                start_time = time.time()
                
                full_text = extract_text_from_pdf(uploaded_file)
                if full_text.startswith("PDF解析失败"):
                    st.error(full_text)
                else:
                    fin_data, fin_json_str = extract_financials(full_text)
                    anomalies_text = detect_anomalies(full_text, fin_json_str)
                    logic_text = investment_logic(full_text, fin_json_str, anomalies_text)
                    questions_text = generate_questions(full_text, anomalies_text, logic_text)
                    
                    elapsed = time.time() - start_time
                    
                    st.session_state['fin_data'] = fin_data
                    st.session_state['fin_json_str'] = fin_json_str
                    st.session_state['anomalies_text'] = anomalies_text
                    st.session_state['logic_text'] = logic_text
                    st.session_state['questions_text'] = questions_text
                    st.session_state['elapsed'] = elapsed
                    
                    st.success(f"分析完成，耗时 {elapsed:.0f} 秒")

    if 'fin_data' in st.session_state:
        tab1, tab2, tab3, tab4 = st.tabs(["财务透视", "异常标记", "投资逻辑", "投委必问"])
        
        with tab1:
            fin_data = st.session_state['fin_data']
            if not fin_data:
                st.warning("财务数据解析失败或未提取到有效数据。")
            else:
                try:
                    df = pd.DataFrame(fin_data)
                    from plotly.subplots import make_subplots
                    import plotly.graph_objects as go
                    
                    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
                    fig1.add_trace(go.Bar(x=df['years'], y=df['revenue'], name="收入"), secondary_y=False)
                    fig1.add_trace(go.Scatter(x=df['years'], y=df['gross_margin'], name="毛利率(%)", mode="lines+markers"), secondary_y=True)
                    fig1.add_trace(go.Scatter(x=df['years'], y=df['rd_expense'], name="研发费用", fill='tozeroy', mode="lines"), secondary_y=True)
                    fig1.update_layout(title_text="收入、毛利率与研发费用趋势")
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
                    fig2.add_trace(go.Bar(x=df['years'], y=df['operating_cash_flow'], name="经营现金流"), secondary_y=False)
                    fig2.add_trace(go.Bar(x=df['years'], y=df['capex'], name="资本开支"), secondary_y=False)
                    fig2.add_trace(go.Scatter(x=df['years'], y=df['accounts_receivable'], name="应收账款", mode="lines+markers"), secondary_y=True)
                    fig2.add_trace(go.Scatter(x=df['years'], y=df['inventory'], name="存货", mode="lines+markers"), secondary_y=True)
                    fig2.update_layout(title_text="现金流与营运资产趋势", barmode='group')
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    st.dataframe(df)
                except Exception as e:
                    st.warning(f"图表渲染出错：{str(e)}")

        with tab2:
            anomalies = st.session_state['anomalies_text']
            if anomalies.startswith("LLM调用出错"):
                st.error(anomalies)
            else:
                cards = anomalies.split("**异常点")
                for card in cards:
                    if card.strip():
                        content = "**异常点" + card
                        border_color = "#ccc"
                        if "风险等级：高" in content:
                            border_color = "red"
                        elif "风险等级：中" in content:
                            border_color = "orange"
                            
                        # 用灰色背景和不同颜色的左边框来渲染风险等级
                        st.markdown(
                            f'''<div style="border-left: 5px solid {border_color}; padding: 15px; margin-bottom: 15px; background-color: #2b2b2b; color: #ddd; border-radius: 5px;">'''
                            f'''<div style="white-space: pre-wrap;">{content}</div></div>''', 
                            unsafe_allow_html=True
                        )

        with tab3:
            st.info("以下分析由AI基于尽调报告信息生成，推测部分已标注，仅供投资团队参考。")
            logic_text = st.session_state['logic_text']
            if logic_text.startswith("LLM调用出错"):
                st.error(logic_text)
            else:
                st.markdown(logic_text)
                
        with tab4:
            questions = st.session_state['questions_text']
            if questions.startswith("LLM调用出错"):
                st.error(questions)
            else:
                st.markdown(
                    f'''<div style="background-color: #1a1a2e; padding: 20px; border-radius: 8px; color: #f5f5f5; font-size: 18px; line-height: 1.8;">'''
                    f'''<strong>{questions}</strong></div>''', 
                    unsafe_allow_html=True
                )
