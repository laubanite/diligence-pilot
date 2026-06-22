"""
LLM 分析节点模块（6 个分析函数）
"""
import json
import re

import streamlit as st

from llm_utils import call_llm


def extract_financials(full_text):
    """
    分析节点一：从报告全文中提取三年核心财务基础科目数据。
    返回 (fin_data_dict, fin_json_str)。
    """
    system_prompt = """你是一位硬科技赛道财务分析师。从以下尽调报告中提取近三个完整财年的基础科目数据。返回严格的JSON，不要任何解释。
JSON格式：
{
  "years": ["2023","2024","2025"],
  "revenue": [数字,数字,数字],
  "cost_of_sales": [数字,数字,数字],
  "gross_profit": [数字,数字,数字],
  "rd_expense": [数字,数字,数字],
  "ebitda": [数字,数字,数字],
  "net_profit": [数字,数字,数字],
  "non_recurring_items": [数字,数字,数字],
  "operating_cash_flow": [数字,数字,数字],
  "investing_cash_flow": [数字,数字,数字],
  "cash_equivalents": [数字,数字,数字],
  "cash_from_sales": [数字,数字,数字],
  "accounts_receivable": [数字,数字,数字],
  "inventory": [数字,数字,数字],
  "accounts_payable": [数字,数字,数字],
  "advance_from_customers": [数字,数字,数字],
  "total_assets": [数字,数字,数字],
  "current_assets": [数字,数字,数字],
  "current_liabilities": [数字,数字,数字],
  "short_term_borrowings": [数字,数字,数字],
  "long_term_borrowings": [数字,数字,数字],
  "non_current_liabilities_due_in_1yr": [数字,数字,数字],
  "equity_before_round": [数字,数字,数字],
  "new_equity_issued": [数字,数字,数字],
  "government_subsidy": [数字,数字,数字],
  "revenue_top5_customer_share": [百分比数字,数字,数字]
}
提示要求：所有数字必须直接从报告提取，单位统一为万元。毛利率、研发费用率等比率不要计算，只提取原始数值。未找到的字段必须填 null，严禁省略键名。只返回 JSON 对象，首字符必须是 {，尾字符必须是 }。不要输出任何解释、注释或 Markdown 标记。所有数字必须来自报告，计算逻辑需明确，不要使用外部知识。"""

    user_prompt = full_text
    response_text = call_llm(system_prompt, user_prompt, json_mode=True)

    try:
        if response_text.startswith("LLM调用出错"):
            raise ValueError(response_text)

        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        if not clean_text.startswith("{"):
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                clean_text = match.group()

        return json.loads(clean_text), response_text
    except Exception as e:
        print(f"JSON解析失败: {e}\n原始返回内容: \n{response_text}")
        st.error(f"财务数据解析失败。原始返回（前500字符）：{response_text[:500]}")
        return {}, response_text


def detect_anomalies(full_text, financial_json_str):
    """
    分析节点二：财务与经营异常检测。
    """
    system_prompt = """你是PE硬科技尽调专家。基于财务数据和报告全文，找出最多3个最显著的财务或经营异常信号。优先关注：
- 现金跑道 < 12 个月。
- 利润含金量连续两年 < 0.5。
- 收现比连续两年 < 0.8。
- 毛利率边际趋势连续两年下降且幅度 > 10%。
- 扣非净利润占比 < 50%。
- 研发费用率 < 5% 或 > 30%。
- EBITDA利润率连续下滑。
- 应收账款周转天数 > 120 天。
- 存货周转天数 > 180 天（无合理说明）。
- 净营运资本变动率 > 1.0。
- 有息资产负债率 > 30%。
- 股权稀释率单轮 > 30%。
- 前五大客户依赖度 > 50%。
- 在建工程占比 > 150%（可以从报告文字中判断，若无数据可忽略）。
- 实际税率远低于 15% 且无亏损抵免解释。
- 研发资本化率 > 50%。

对每个异常严格按以下格式输出，不要输出任何其他内容：
**异常点1**
- 异常描述：（一句话）
- 数据对比：（具体年份和数字）
- 原文依据：（引用报告原文1-2句，标明页码如[page_8]）
- 风险等级：高/中

**异常点2**
...

只返回上述格式内容，不要任何其他文字。

**所有事实判断必须引用报告原文或页码。外部知识仅在报告缺失时使用，且必须标注（推测）。**"""

    user_prompt = f"报告全文：{full_text}\n\n提取的财务数据：{financial_json_str}"
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text


def extract_highlights(full_text, financial_json_str):
    """
    分析节点：投资亮点。
    """
    system_prompt = """你是一位硬科技赛道PE投资分析师。基于尽调报告全文和财务数据，找出这家公司最值得关注的3个投资亮点。每个亮点必须有具体数据或事实支撑。
对每个亮点，严格按以下格式输出：
**亮点1**
- 亮点描述：（一句话概括）
- 数据支撑：（具体数字、时间、客户、专利等）
- 原文依据：（引用报告原文1-2句，标明页码如[page_x]）
- 亮点强度：强/中

**亮点2**
...

只返回上述格式内容，不要任何其他文字。

**所有事实判断必须引用报告原文或页码。外部知识仅在报告缺失时使用，且必须标注（推测）。**"""

    user_prompt = f"报告全文：{full_text}\n\n提取的财务数据：{financial_json_str}"
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text


def industry_analysis(full_text):
    """
    分析节点：行业研究。
    """
    system_prompt = """**核心原则：你的分析必须严格基于尽调报告中的信息。报告中明确陈述的事实（如产业链位置、市场份额、技术路线）必须原文采纳，不得用你的内部知识覆盖或修改。只有在报告信息缺失时，才可以用行业常识补充，并必须在句末标注（推测）。如果报告与你的常识冲突，以报告为准。**

你是一位硬科技产业研究专家。请基于尽调报告中对行业的描述，结合你对相关产业的知识储备，输出一份简明的行业分析报告。
必须覆盖以下四个模块：
1. 产业链结构：该行业的上游/中游/下游分别是什么？标的公司处于哪个环节？必须引用报告中明确提及产业链位置的原文（标注页码）。如果报告未明确说明，才基于行业知识推断并标注（推测）。
2. 市场规模与增速：全球及中国市场空间（TAM/SAM）、近年增速、驱动因素。
3. 竞争格局：国内外主要玩家、技术路线差异、标的公司的竞争位势。
4. 关键卡点：该行业当前面临的核心瓶颈或痛点是什么？标的公司是否正解决这些卡点？

输出格式（严格Markdown）：
## 行业分析
### 产业链定位
...
### 市场规模与增速
...
### 竞争格局
...
### 行业关键卡点与公司价值
...
**总结**：（一句话总结标的公司在该行业中的位置和结构性机会）

信息不足时基于行业常识合理推断，并在句末标注（推测）。

**所有事实判断必须引用报告原文或页码。外部知识仅在报告缺失时使用，且必须标注（推测）。**"""

    user_prompt = full_text
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text


def investment_logic(full_text, financial_json_str, anomalies_text):
    """
    分析节点三：投资逻辑梳理（7维框架）
    """
    system_prompt = """**核心原则：你的分析必须严格基于尽调报告中的信息。报告中明确陈述的事实必须原文采纳，不得用你的内部知识覆盖或修改。信息不足时才可推测并标注。如果报告与你的常识冲突，以报告为准。**

你是一位顶级硬科技VC合伙人，正在为投委会撰写投资逻辑摘要。请基于尽调报告全文、财务数据和已发现的异常，从以下7个维度梳理投资逻辑，每个维度2-3句分析，信息不足时基于行业常识推测，并在句末标注（推测）。最后给出综合判断。

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
**综合判断**：（一句话总结投资逻辑是否成立，关键支撑点和最大风险）

**所有事实判断必须引用报告原文或页码。外部知识仅在报告缺失时使用，且必须标注（推测）。**"""

    user_prompt = f"报告全文：{full_text}\n\n财务数据：{financial_json_str}\n\n已发现异常：{anomalies_text}"
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text


def generate_communication_points(full_text, anomalies_text, logic_text):
    """
    分析节点四：重点沟通清单
    """
    system_prompt = """你是PE投资分析系统。你的任务是根据报告、财务数据和异常，直接输出5个沟通点。不要输出任何前言、后语、解释。严格按以下格式输出：

**沟通点1：[标题]**
- 沟通要点：...
- 产生原因：...
- 我们的初步理解：可能原因一：...；可能原因二：...

...（重复5次）

覆盖维度应包括：
- 技术与产品（研发进展、技术壁垒、产品成熟度、专利归属等）
- 市场与客户（市场空间、客户集中度、竞争格局、增长驱动等）
- 财务与现金流（收入质量、回款、补贴依赖、现金流持续性等）
- 团队与治理（核心团队稳定性、激励机制、控制权等）
- 运营与产能（产能利用率、扩产计划、供应链等）
- 融资与退出（估值逻辑、资金用途、退出预期等）

生成5个沟通点，按重要性排序。保持专业、客观，体现投资团队的审慎与尊重。

**重要：直接输出第一个沟通点，不要任何开头语、总结语、问候语。严格遵循上述三段式格式，不要输出任何与格式无关的文字。**

**所有事实判断必须引用报告原文或页码。外部知识仅在报告缺失时使用，且必须标注（推测）。**"""

    user_prompt = f"报告全文：{full_text}\n\n异常点：{anomalies_text}\n\n投资逻辑：{logic_text}"
    response_text = call_llm(system_prompt, user_prompt, json_mode=False)
    return response_text
