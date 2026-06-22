from dotenv import load_dotenv
load_dotenv()

import app  # 导入你正在写的 app.py，里面已经有 extract_text_from_pdf 和 extract_financials

# 读取本地PDF文件，模拟上传
with open(r"E:\投研agent\diligence-pilot\test_report.pdf", "rb") as f:
    # 注意：extract_text_from_pdf 期望的参数是类似 Streamlit 上传文件的对象
    # 这里我们需要模拟一个对象，最简单的做法是直接调用 pymupdf 的底层逻辑
    # 但因为我们还没有上传对象，直接复制 app 里 extract_text_from_pdf 的内部逻辑更稳妥
    # 所以我们绕过 Streamlit 的上传对象，直接调用 pymupdf
    import pymupdf
    doc = pymupdf.open(stream=f.read())
    full_text = ""
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        full_text += f"\n[page_{page_num}]\n{text}"

# 打印全文前500字符，看看提取效果
print("===== PDF提取文本预览（前500字符）=====")
print(full_text[:500])

# 调用财务提取函数
print("\n===== 调用 extract_financials =====")
fin_data, raw_response = app.extract_financials(full_text)
print("解析后的字典:", fin_data)
print("LLM原始返回:", raw_response)