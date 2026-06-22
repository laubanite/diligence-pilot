"""
UI 组件模块——所有 Tab 的渲染函数
"""
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

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

    gross_margin = get_ratio_value("gross_margin")
    rd_expense_ratio = get_ratio_value("rd_expense_ratio")
    ebitda_margin = get_ratio_value("ebitda_margin")
    profit_quality = get_ratio_value("profit_quality")
    ar_days = get_ratio_value("ar_turnover_days")
    cash_runway = get_ratio_value("cash_runway_months")

    metrics = [
        ("毛利率", gross_margin, lambda v: max(0.0, min(v if v is not None else 0.0, 0.8)) / 0.8),
        ("研发费用率", rd_expense_ratio, lambda v: max(0.0, 1 - min(v if v is not None else 0.0, 0.4) / 0.4)),
        ("EBITDA利润率", ebitda_margin, lambda v: max(0.0, min(v if v is not None else 0.0, 0.5)) / 0.5),
        ("利润含金量", profit_quality, lambda v: max(0.0, min(v if v is not None else 0.0, 1.5)) / 1.5),
        ("应收账款周转天数", ar_days, lambda v: 1.0 - min(max(v if v is not None else 999.0, 0.0), 180.0) / 180.0),
        ("现金跑道（月）", cash_runway, lambda v: min(max(v if v is not None else 0.0, 0.0), 24.0) / 24.0),
    ]

    radar_labels = []
    company_scores = []
    baseline_scores = []
    for label, raw_value, transform in metrics:
        radar_labels.append(label)
        if raw_value is None:
            company_scores.append(None)
        else:
            company_scores.append(round(transform(raw_value), 4))
        baseline_scores.append(1.0)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=baseline_scores + [baseline_scores[0]],
        theta=radar_labels + [radar_labels[0]],
        fill='toself', name='健康基准',
        line=dict(color='rgba(160,160,160,0.65)'),
        fillcolor='rgba(160,160,160,0.18)',
    ))

    company_trace_r = []
    company_trace_theta = []
    for label, score, (_, raw_value, _) in zip(radar_labels, company_scores, metrics):
        if score is None:
            company_trace_r.append(0)
            company_trace_theta.append(f"{label}<br>N/A")
        else:
            company_trace_r.append(score)
            company_trace_theta.append(label)

    fig.add_trace(go.Scatterpolar(
        r=company_trace_r + [company_trace_r[0]],
        theta=company_trace_theta + [company_trace_theta[0]],
        fill='toself', name=f'{latest_year}公司表现',
        line=dict(color='#2f855a', width=3),
        fillcolor='rgba(47,133,90,0.25)',
        hovertemplate='%{theta}: %{r}<extra></extra>',
    ))

    fig.update_layout(
        title=f"{latest_year} 财务健康雷达图",
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True, margin=dict(l=40, r=40, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_alert_table(title, rows, alert_rules):
    """按红黄阈值展示财务比率表格。"""
    st.subheader(title)
    if not rows:
        st.warning("当前分类没有可展示的数据。")
        return

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("当前分类没有可展示的数据。")
        return

    def classify_value(metric, value):
        if pd.isna(value):
            return ""
        rule = alert_rules.get(metric, {})
        if not rule:
            return ""
        if "min" in rule and rule["min"] is not None and value < rule["min"]:
            return "red"
        if "max" in rule and rule["max"] is not None and value > rule["max"]:
            return "red"
        if "warn_min" in rule and rule["warn_min"] is not None and value < rule["warn_min"]:
            return "yellow"
        if "warn_max" in rule and rule["warn_max"] is not None and value > rule["warn_max"]:
            return "yellow"
        return ""

    def highlight_row(row):
        styles = []
        metric = row.get("指标名称")
        for col in row.index:
            if col in ["指标名称", "健康阈值"]:
                styles.append("")
                continue
            flag = classify_value(metric, row[col])
            if flag == "red":
                styles.append("background-color: #ffe5e5")
            elif flag == "yellow":
                styles.append("background-color: #fff2cc")
            else:
                styles.append("")
        return styles

    st.dataframe(df.style.format(na_rep="N/A").apply(highlight_row, axis=1))


def render_financial_tab(fin_data, ratios):
    """Tab 1：财务透视"""
    if not fin_data:
        st.warning("财务数据解析失败或未提取到有效数据。")
        return

    try:
        df = pd.DataFrame(fin_data)

        if {'revenue', 'gross_profit', 'operating_cash_flow', 'rd_expense'}.issubset(df.columns):
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=df['years'], y=df['revenue'], name="收入"), secondary_y=False)
            gross_margin_series = [
                (g / r * 100) if g is not None and r not in (None, 0) else None
                for g, r in zip(df['gross_profit'], df['revenue'])
            ]
            fig.add_trace(go.Scatter(x=df['years'], y=gross_margin_series, name="毛利率(%)", mode="lines+markers"), secondary_y=True)
            fig.add_trace(go.Scatter(x=df['years'], y=df['rd_expense'], name="研发费用", mode="lines+markers"), secondary_y=True)
            fig.add_trace(go.Bar(x=df['years'], y=df['operating_cash_flow'], name="经营现金流"), secondary_y=False)
            fig.update_layout(title_text="核心经营趋势", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("图表字段不完整，已跳过核心趋势图。")

        if isinstance(ratios, dict) and ratios:
            render_financial_radar(ratios)

        if isinstance(ratios, dict) and ratios:
            ratios_df = pd.DataFrame(ratios)
            display_groups = {
                "生存与现金流": ["cash_runway_months", "profit_quality", "cash_to_revenue_ratio"],
                "盈利质量": ["gross_margin", "gross_margin_trend", "deducted_np_ratio", "rd_expense_ratio", "ebitda_margin"],
                "运营效率": ["ar_turnover_days", "inventory_turnover_days", "nwc_change_ratio", "asset_turnover"],
                "资本结构": ["interest_bearing_debt_ratio", "equity_dilution_rate", "current_ratio"],
            }
            for group_name, metrics in display_groups.items():
                rows = []
                for metric in metrics:
                    if metric not in ratios_df.columns:
                        continue
                    row = {"指标名称": metric, "健康阈值": str(THRESHOLD_MAP.get(metric, {}))}
                    for year in ratios_df["years"]:
                        year_index = ratios_df["years"].tolist().index(year)
                        row[str(year)] = ratios_df.loc[year_index, metric]
                    rows.append(row)
                render_alert_table(group_name, rows, THRESHOLD_MAP)

        st.dataframe(df)
    except Exception as e:
        st.warning(f"图表渲染出错：{str(e)}")


def render_highlights_tab(highlights_text):
    """Tab 2：投资亮点"""
    if not highlights_text:
        st.info("尚未生成投资亮点。请先点击开始分析。")
    elif highlights_text.startswith("LLM调用出错"):
        st.error(highlights_text)
    else:
        cards = [chunk.strip() for chunk in highlights_text.split("**亮点") if chunk.strip()]
        for card in cards:
            content = "**亮点" + card
            title_line = content.split("\n", 1)[0].strip()
            body = content.split("\n", 1)[1] if "\n" in content else ""
            desc_text = data_text = source_text = strength_text = ""
            for line in body.splitlines():
                if line.startswith("- 亮点描述："):
                    desc_text = line.replace("- 亮点描述：", "", 1).strip()
                elif line.startswith("- 数据支撑："):
                    data_text = line.replace("- 数据支撑：", "", 1).strip()
                elif line.startswith("- 原文依据："):
                    source_text = line.replace("- 原文依据：", "", 1).strip()
                elif line.startswith("- 亮点强度："):
                    strength_text = line.replace("- 亮点强度：", "", 1).strip()
            with st.container(border=True):
                st.markdown(f"**{title_line.replace('**', '').strip()}**")
                st.markdown(f"**亮点描述：** {desc_text}")
                st.markdown(f"**数据支撑：** {data_text}")
                st.markdown(f"**原文依据：** {source_text}")
                st.markdown(f"**亮点强度：** {strength_text}")


def render_anomalies_tab(anomalies_text):
    """Tab 3：异常标记"""
    if not anomalies_text:
        st.info("尚未生成异常分析。请先点击开始分析。")
    elif anomalies_text.startswith("LLM调用出错"):
        st.error(anomalies_text)
    else:
        cards = anomalies_text.split("**异常点")
        for card in cards:
            if not card.strip():
                continue
            content = "**异常点" + card
            lines = content.splitlines()
            title_line = lines[0].replace("**", "").strip()
            desc_text = data_text = source_text = risk_text = ""
            for line in lines[1:]:
                if line.startswith("- 异常描述："):
                    desc_text = line.replace("- 异常描述：", "", 1).strip()
                elif line.startswith("- 数据对比："):
                    data_text = line.replace("- 数据对比：", "", 1).strip()
                elif line.startswith("- 原文依据："):
                    source_text = line.replace("- 原文依据：", "", 1).strip()
                elif line.startswith("- 风险等级："):
                    risk_text = line.replace("- 风险等级：", "", 1).strip()
            with st.container(border=True):
                st.markdown(f"**{title_line}**")
                st.markdown(f"**异常描述：** {desc_text}")
                st.markdown(f"**数据对比：** {data_text}")
                st.markdown(f"> {source_text}")
                st.markdown(f"**风险等级：** {risk_text}")


def render_industry_tab(industry_text):
    """Tab 4：行业研究"""
    st.info("以下分析结合了尽调报告和AI产业知识库，推测部分已标注。")
    if not industry_text:
        st.warning("尚未生成行业分析。")
    elif industry_text.startswith("LLM调用出错"):
        st.error(industry_text)
    else:
        st.markdown(industry_text)


def render_logic_tab(logic_text):
    """Tab 5：投资逻辑"""
    st.info("以下分析由AI基于尽调报告信息生成，推测部分已标注，仅供投资团队参考。")
    if not logic_text:
        st.warning("尚未生成投资逻辑。")
    elif logic_text.startswith("LLM调用出错"):
        st.error(logic_text)
    else:
        st.markdown(logic_text)


def render_communication_tab(communication_text):
    """Tab 6：重点沟通清单"""
    st.caption("以下沟通要点仅供内部参考，实际沟通时请结合现场语境调整措辞。")
    if not communication_text:
        st.warning("尚未生成沟通清单。")
    elif communication_text.startswith("LLM调用出错"):
        st.error(communication_text)
    else:
        points = [chunk.strip() for chunk in communication_text.split("**沟通点") if chunk.strip()]
        if not points:
            st.warning("未生成可展示的沟通点。")
        else:
            for point in points:
                card_text = "**沟通点" + point
                title_line = card_text.split("\n", 1)[0].strip()
                body = card_text.split("\n", 1)[1] if "\n" in card_text else ""
                reason_text = understanding_text = points_text = ""
                for line in body.splitlines():
                    if line.startswith("- 沟通要点："):
                        points_text = line.replace("- 沟通要点：", "", 1).strip()
                    elif line.startswith("- 产生原因："):
                        reason_text = line.replace("- 产生原因：", "", 1).strip()
                    elif line.startswith("- 我们的初步理解："):
                        understanding_text = line.replace("- 我们的初步理解：", "", 1).strip()
                with st.container(border=True):
                    st.markdown(f"**{title_line.replace('**', '').strip()}**")
                    st.markdown(f"**沟通要点：** {points_text}")
                    st.markdown(f"**产生原因：** {reason_text}")
                    st.markdown(f"**我们的初步理解：** {understanding_text}")
