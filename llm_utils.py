"""
通用 LLM 调用模块
"""
import os
import requests

import streamlit as st


def get_config_value(key, default=None):
    if hasattr(st, "secrets"):
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return os.getenv(key, default)


def call_llm(system_prompt, user_prompt, json_mode=False):
    """
    通用大模型请求函数。直接通过 requests 发送 HTTP POST。
    """
    base_url = get_config_value("LLM_BASE_URL", "https://api.deepseek.com")
    api_key = get_config_value("LLM_API_KEY", "")
    model = get_config_value("LLM_MODEL", "deepseek-v4-flash")

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
        "max_tokens": 16384
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"LLM调用出错: {str(e)}"
