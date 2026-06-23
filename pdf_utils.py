"""
PDF 文本提取模块
"""
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


def extract_text_from_pdf(uploaded_file):
    """
    从前端上传的 PDF 文件读取纯文本。
    返回带 [page_x] 页码标记的全文字符串。
    """
    try:
        doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
        full_text = ""
        for i, page in enumerate(doc):
            text = page.get_text()
            full_text += f"\n\n[page_{i+1}]\n{text}"
        return full_text.strip()
    except Exception as e:
        return f"PDF解析失败: {str(e)}"
