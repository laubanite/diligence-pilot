"""
VestMind - UI 组件模块
已重构：支持 Markdown 锚点标题与极简排版
"""
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import re

from config import THRESHOLD_MAP


def render_financial_radar(ratios):
    """基于最新一期 ratios 绘制财务雷达图。"""
    if not isinstance(ratios, dict) or not ratios.get("years"):
        st.warning("暂无足够数据生成雷达图。")
        return

    latest_index = len(ratios["years"]) - 1
    latest_year = ratios["years"][latest_index]

    def get_ratio_value(key):
        values = ratios.get(key, [])
        if not isinstance(values, list) or latest_index >= len(values):
            return None
        return values[latest_index]

    metrics = [
        ("毛利率", get_ratio_value("gross_margin"), lambda v: max(0.0, min(v if v is not None else 0.0, 0.8)) / 0.8),
        ("研发费用率", get_ratio_value("rd_expense_ratio"), lambda v: max(0.0, 1 - min(v if v is not None else 0.0, 0.4) / 0.4)),
        ("EBITDA利润率", get_ratio_value("ebitda_margin"), lambda v: max(0.0, min(v if v is not None else 0.0, 0.5)) / 0.5),
        ("利润含金量", get_ratio_value("profit_quality"), lambda v: max(0.0, min(v if v is not None else 0.0, 1.5)) / 1.5),
        ("应收账款周转天数", get_ratio_value("ar_turnover_days"), lambda v: 1.0 - min(max(v if v is not None else 999.0, 0.0), 180.0) / 180.0),
        ("现金跑道", get_ratio_value("cash_runway_months"), lambda v: min(max(v if v is not None else 0.0, 0.0), 24.0) / 24.0),
    ]

    radar_labels = [m[0] for m in metrics]
    company_scores = [round(m[2](m[1]), 4) if m[1] is not None else 0 for m in metrics]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=company_scores + [company_scores[0]],
        theta=radar_labels + [radar_labels[0]],
        fill='toself', name=f'{latest_year}公司表现',
        line=dict(color='#1a1d23', width=2),
        fillcolor='rgba(26, 29, 35, 0.1)',
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False, margin=dict(l=40, r=40, t=20, b=20),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


def render_alert_table(title, rows, alert_rules):
    """按红黄阈值展示财务比率表格。"""
    st.markdown(f"### {title}") # 使用 H3 方便目录层级
    if not rows: return

    df = pd.DataFrame(rows)
    
    def classify_value(metric, value):
        if pd.isna(value): return ""
        rule = alert_rules.get(metric, {})
        if "min" in rule and value < rule["min"]: return "background-color: #fee2e2"
        if "max" in rule and value > rule["max"]: return "background-color: #fee2e2"
        return ""

    def highlight_row(row):
        styles = [""] * len(row)
        metric = row.get("指标名称")
        for i, col in enumerate(row.index):
            if col not in ["指标名称", "健康阈值"]:
                styles[i] = classify_value(metric, row[col])
        return styles

    st.dataframe(df.style.apply(highlight_row, axis=1), use_container_width=True)


def _normalize_fin_dict(data, expected_years=None):
    """将 dict 中所有值统一为等长列表，缺失年份用 None 补齐，确保安全传入 DataFrame。

    如果 expected_years 未提供，则从 data['years'] 推断。
    如果 data 中没有 'years' 键或为空，返回 None。
    标量值（非列表）会被包装成单元素列表后再补齐。
    """
    if not isinstance(data, dict) or not data:
        return None

    # 提取年份列表，如果不存在或为空则无法标准化
    years = data.get("years", None)
    if not isinstance(years, list) or len(years) == 0:
        if expected_years and isinstance(expected_years, list) and len(expected_years) > 0:
            years = expected_years
        else:
            return None

    n = len(years)
    normalized = {"years": list(years)}

    for key, value in data.items():
        if key == "years":
            continue
        # 统一为列表
        if not isinstance(value, list):
            value = [value]
        # 补齐或截断到与 years 等长
        if len(value) < n:
            value = list(value) + [None] * (n - len(value))
        elif len(value) > n:
            value = value[:n]
        normalized[key] = value

    return normalized


def render_financial_tab(fin_data, ratios):
    """Tab 1：财务透视"""
    st.markdown("## 核心经营趋势")
    if fin_data:
        norm_fin = _normalize_fin_dict(fin_data)
        if norm_fin and norm_fin.get("years"):
            df = pd.DataFrame.from_dict(norm_fin, orient='columns')
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=df['years'], y=df['revenue'], name="收入", marker_color="#1a1d23"), secondary_y=False)
            fig.add_trace(go.Scatter(x=df['years'], y=df['operating_cash_flow'], name="经营现金流", line=dict(color="#9ca3af")), secondary_y=False)
            fig.update_layout(height=400, margin=dict(t=20, b=20), barmode='group')
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("## 财务健康雷达")
    if ratios:
        render_financial_radar(ratios)

    st.markdown("## 详细指标分析")
    if isinstance(ratios, dict) and ratios:
        norm_ratios = _normalize_fin_dict(ratios)
        if norm_ratios and norm_ratios.get("years"):
            ratios_df = pd.DataFrame.from_dict(norm_ratios, orient='columns')
            years_list = norm_ratios["years"]
            display_groups = {
                "生存与现金流": ["cash_runway_months", "profit_quality", "cash_to_revenue_ratio"],
                "盈利质量": ["gross_margin", "deducted_np_ratio", "rd_expense_ratio"],
                "运营效率": ["ar_turnover_days", "inventory_turnover_days", "asset_turnover"],
            }
            for group_name, metrics in display_groups.items():
                rows = []
                for metric in metrics:
                    if metric in ratios_df.columns:
                        row = {"指标名称": metric, "健康阈值": str(THRESHOLD_MAP.get(metric, {}))}
                        for year in years_list:
                            year_idx = years_list.index(year)
                            row[str(year)] = ratios_df.loc[year_idx, metric]
                        rows.append(row)
                render_alert_table(group_name, rows, THRESHOLD_MAP)


def render_highlights_tab(highlights_text):
    """Tab 2：投资亮点 (返回 Markdown 供 TOC 使用)"""
    if not highlights_text or "LLM调用出错" in highlights_text:
        st.warning("暂无高亮分析")
        return ""

    md_for_toc = ""
    blocks = highlights_text.split("### ")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not body:
            continue
        heading = f"## {title}"
        md_for_toc += heading + "\n"
        st.markdown(heading)
        st.markdown(body)
        st.markdown("---")
    return md_for_toc


def render_anomalies_tab(anomalies_text):
    """Tab 3：异常标记 (返回 Markdown 供 TOC 使用)"""
    if not anomalies_text or "LLM调用出错" in anomalies_text:
        st.warning("暂无异常标记")
        return ""

    md_for_toc = ""
    blocks = anomalies_text.split("### ")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not body:
            continue
        heading = f"## {title}"
        md_for_toc += heading + "\n"
        st.markdown(heading)
        st.markdown(body)
        st.markdown("---")
    return md_for_toc


def render_industry_tab(industry_text):
    """Tab 4：行业研究 (返回原始 Markdown 供 TOC 使用)"""
    st.markdown('<div style="background:#f8fafc; padding:15px; border-radius:10px; border-left:4px solid #1a1d23; margin-bottom:25px; font-size:0.95rem; color:#64748b;">本章节分析基于尽调报告与 VestMind AI 产业知识库。</div>', unsafe_allow_html=True)
    if not industry_text:
        st.warning("内容生成中...")
        return ""
    st.markdown(industry_text)
    return industry_text


def render_logic_tab(logic_text):
    """Tab 5：投资逻辑 (返回原始 Markdown 供 TOC 使用)"""
    if not logic_text:
        st.warning("内容生成中...")
        return ""
    st.markdown(logic_text)
    return logic_text


def render_communication_tab(communication_text):
    """Tab 6：重点沟通清单 (返回 Markdown 供 TOC 使用)"""
    if not communication_text:
        st.warning("内容生成中...")
        return ""

    md_for_toc = ""
    blocks = communication_text.split("### ")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not body:
            continue
        # ○ 前缀条目用空行隔开形成独立段落
        formatted_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("- 沟通要点：") or stripped.startswith("- 产生原因：") or stripped.startswith("- 我们的初步理解："):
                formatted_lines.append(stripped)
            elif stripped.startswith("可能原因"):
                formatted_lines.append(stripped)
            else:
                formatted_lines.append(stripped)
        formatted_body = "\n".join(formatted_lines)

        heading = f"## {title}"
        md_for_toc += heading + "\n"
        st.markdown(heading)
        st.markdown(formatted_body)
        st.markdown("---")
    return md_for_toc