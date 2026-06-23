"""
配置常量模块
"""
THRESHOLD_MAP = {
    "cash_runway_months": {"min": 18, "warn_min": 12},
    "profit_quality": {"min": 0.8, "warn_min": 0.5},
    "cash_to_revenue_ratio": {"min": 0.85, "warn_min": 0.8},
    "gross_margin": {"stable": True},
    "gross_margin_trend": {"min": -0.1, "warn_min": -0.2},
    "deducted_np_ratio": {"min": 0.7, "warn_min": 0.5},
    "rd_expense_ratio": {"min": 0.10, "max": 0.25, "warn_min": 0.05, "warn_max": 0.30},
    "ebitda_margin": {"trend": "up"},
    "ar_turnover_days": {"max": 90, "warn_max": 120},
    "inventory_turnover_days": {"max": 180, "warn_max": 180},
    "nwc_change_ratio": {"max": 0.5, "warn_max": 1.0},
    "asset_turnover": {},
    "interest_bearing_debt_ratio": {"max": 0.30},
    "equity_dilution_rate": {"max": 0.20, "warn_max": 0.30},
    "current_ratio": {"min": 1.5},
}

TAB_NAMES = ["财务透视", "💡 投资亮点", "异常标记", "🌐 行业研究", "投资逻辑", "💬 重点沟通清单"]

PAGE_TITLE = "DiligencePilot Demo | 硬科技AI投研助手"
PAGE_SUBTITLE = "聚焦半导体、新能源、高端制造 · 7维投资逻辑框架"
UPLOADER_HINT = "支持文字型PDF，分析时长约60秒"
PLACEHOLDER_TEXT = "👈 请上传一份硬科技公司的尽调报告PDF，然后点击「开始分析」。"
SPINNER_TEXT = "Thinking..."
