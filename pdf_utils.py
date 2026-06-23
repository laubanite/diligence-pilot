"""
PDF / DOCX 文本提取模块
"""
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


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


def extract_text_from_docx(uploaded_file):
    """
    从前端上传的 DOCX 文件读取纯文本。
    返回带段落标记的全文字符串。
    """
    if DocxDocument is None:
        return "DOCX解析失败: 未安装 python-docx 库"

    try:
        doc = DocxDocument(stream=uploaded_file.read())
        paragraphs = []
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                paragraphs.append(f"[para_{i+1}] {para.text.strip()}")
        return "\n\n".join(paragraphs) if paragraphs else "DOCX解析失败: 文档无有效文本内容"
    except Exception as e:
        return f"DOCX解析失败: {str(e)}"


def extract_text(uploaded_file):
    """
    自动检测文件类型并提取文本。
    支持 .pdf 和 .docx。
    """
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return f"不支持的文件格式: {name}"
