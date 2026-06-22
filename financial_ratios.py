"""
财务比率计算模块（纯 Python，不依赖 Streamlit）
"""


def calculate_ratios(fin_data):
    """
    基于财务基础科目数据计算展示级和监控级指标。
    返回比率字典，所有除法都有除零保护。
    """
    years = fin_data.get("years", []) if isinstance(fin_data, dict) else []
    ratios = {
        "years": years,
        "cash_runway_months": [],
        "profit_quality": [],
        "cash_to_revenue_ratio": [],
        "gross_margin": [],
        "gross_margin_trend": [],
        "deducted_np_ratio": [],
        "rd_expense_ratio": [],
        "ebitda_margin": [],
        "ar_turnover_days": [],
        "inventory_turnover_days": [],
        "nwc_change_ratio": [],
        "asset_turnover": [],
        "interest_bearing_debt_ratio": [],
        "equity_dilution_rate": [],
        "current_ratio": [],
    }

    def get_value(key, index):
        values = fin_data.get(key, []) if isinstance(fin_data, dict) else []
        if not isinstance(values, list) or index >= len(values):
            return None
        return values[index]

    def safe_div(numerator, denominator):
        if numerator is None or denominator is None:
            return None
        if denominator == 0:
            return None
        return numerator / denominator

    for i in range(len(years)):
        revenue = get_value("revenue", i)
        cost_of_sales = get_value("cost_of_sales", i)
        gross_profit = get_value("gross_profit", i)
        rd_expense = get_value("rd_expense", i)
        ebitda = get_value("ebitda", i)
        net_profit = get_value("net_profit", i)
        non_recurring_items = get_value("non_recurring_items", i)
        operating_cash_flow = get_value("operating_cash_flow", i)
        investing_cash_flow = get_value("investing_cash_flow", i)
        cash_equivalents = get_value("cash_equivalents", i)
        cash_from_sales = get_value("cash_from_sales", i)
        accounts_receivable = get_value("accounts_receivable", i)
        inventory = get_value("inventory", i)
        accounts_payable = get_value("accounts_payable", i)
        advance_from_customers = get_value("advance_from_customers", i)
        total_assets = get_value("total_assets", i)
        current_assets = get_value("current_assets", i)
        current_liabilities = get_value("current_liabilities", i)
        short_term_borrowings = get_value("short_term_borrowings", i)
        long_term_borrowings = get_value("long_term_borrowings", i)
        non_current_liabilities_due_in_1yr = get_value("non_current_liabilities_due_in_1yr", i)
        equity_before_round = get_value("equity_before_round", i)
        new_equity_issued = get_value("new_equity_issued", i)

        if operating_cash_flow is not None and investing_cash_flow is not None and cash_equivalents is not None:
            monthly_net_burn = abs(operating_cash_flow + investing_cash_flow) / 12
            cash_runway = safe_div(cash_equivalents, monthly_net_burn)
        else:
            cash_runway = None
        ratios["cash_runway_months"].append(cash_runway)

        ratios["profit_quality"].append(safe_div(operating_cash_flow, net_profit))
        ratios["cash_to_revenue_ratio"].append(safe_div(cash_from_sales, revenue))
        ratios["gross_margin"].append(safe_div(gross_profit, revenue))
        if net_profit is None or non_recurring_items is None or net_profit == 0:
            ratios["deducted_np_ratio"].append(None)
        else:
            ratios["deducted_np_ratio"].append((net_profit - non_recurring_items) / net_profit)
        ratios["rd_expense_ratio"].append(safe_div(rd_expense, revenue))
        ratios["ebitda_margin"].append(safe_div(ebitda, revenue))
        if accounts_receivable in (None, 0) or revenue in (None, 0):
            ratios["ar_turnover_days"].append(None)
        else:
            turnover = safe_div(revenue, accounts_receivable)
            ratios["ar_turnover_days"].append(None if turnover in (None, 0) else 365 / turnover)
        if inventory in (None, 0) or cost_of_sales in (None, 0):
            ratios["inventory_turnover_days"].append(None)
        else:
            turnover = safe_div(cost_of_sales, inventory)
            ratios["inventory_turnover_days"].append(None if turnover in (None, 0) else 365 / turnover)

        if i == 0:
            ratios["gross_margin_trend"].append(None)
            ratios["nwc_change_ratio"].append(None)
            ratios["equity_dilution_rate"].append(None)
        else:
            prev_gross_margin = ratios["gross_margin"][i - 1]
            current_gross_margin = ratios["gross_margin"][i]
            if prev_gross_margin in (None, 0) or current_gross_margin is None:
                ratios["gross_margin_trend"].append(None)
            else:
                ratios["gross_margin_trend"].append((current_gross_margin - prev_gross_margin) / abs(prev_gross_margin))

            nwc_current = None
            nwc_prev = None
            if accounts_receivable is not None and inventory is not None and accounts_payable is not None and advance_from_customers is not None:
                nwc_current = accounts_receivable + inventory - accounts_payable - advance_from_customers
            prev_accounts_receivable = get_value("accounts_receivable", i - 1)
            prev_inventory = get_value("inventory", i - 1)
            prev_accounts_payable = get_value("accounts_payable", i - 1)
            prev_advance_from_customers = get_value("advance_from_customers", i - 1)
            if prev_accounts_receivable is not None and prev_inventory is not None and prev_accounts_payable is not None and prev_advance_from_customers is not None:
                nwc_prev = prev_accounts_receivable + prev_inventory - prev_accounts_payable - prev_advance_from_customers
            current_revenue = revenue
            prev_revenue = get_value("revenue", i - 1)
            if nwc_current is None or nwc_prev is None or current_revenue is None or prev_revenue is None or (current_revenue - prev_revenue) == 0:
                ratios["nwc_change_ratio"].append(None)
            else:
                ratios["nwc_change_ratio"].append((nwc_current - nwc_prev) / (current_revenue - prev_revenue))

            if equity_before_round in (None, 0):
                ratios["equity_dilution_rate"].append(None)
            else:
                ratios["equity_dilution_rate"].append(safe_div(new_equity_issued, equity_before_round))

        if total_assets in (None, 0):
            ratios["asset_turnover"].append(None)
            ratios["interest_bearing_debt_ratio"].append(None)
            ratios["current_ratio"].append(None)
        else:
            ratios["asset_turnover"].append(safe_div(revenue, total_assets))
            debt_parts = [short_term_borrowings, long_term_borrowings, non_current_liabilities_due_in_1yr]
            if any(part is None for part in debt_parts):
                ratios["interest_bearing_debt_ratio"].append(None)
            else:
                total_debt = short_term_borrowings + long_term_borrowings + non_current_liabilities_due_in_1yr
                ratios["interest_bearing_debt_ratio"].append(safe_div(total_debt, total_assets))
            ratios["current_ratio"].append(None if current_assets is None or current_liabilities is None else safe_div(current_assets, current_liabilities))

    return ratios
