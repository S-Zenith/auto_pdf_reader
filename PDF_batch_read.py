import os
import fitz
from pdf2image import convert_from_path
import pytesseract
import requests
from tqdm import tqdm  # 进度条显示

# 配置参数
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
# Buy an API key on siliconflow or elsewhere. Deepseek is cheap, almost free.

DEEPSEEK_API_KEY = "your-api-key"

INPUT_DIR = "/path/to/your/pdf"
# Example: if your file is "/Users/mac/Desktop/file.pdf", then INPUT_DIR = "/Users/mac/Desktop"

def parse_pdf(pdf_path):
    """解析PDF文件（含OCR处理）"""
    full_text = []

    try:
        # 文本提取
        doc = fitz.open(pdf_path)
        for page in doc:
            full_text.append(page.get_text())

        # 图片OCR处理（根据需求可选，可能不靠谱）
        # images = convert_from_path(pdf_path)
        # for img in images:
        #     text = pytesseract.image_to_string(
        #         img, config='--psm 6 -l eng+chi_sim')
        #     if len(text.strip()) > 20:  # 过滤无效OCR结果
        #         full_text.append(f"\n[OCR Result]\n{text}")

    except Exception as e:
        print(f"\n解析失败 {pdf_path}: {str(e)}")
        return None

    return "\n".join(full_text)


def summarize_text(text):
    """调用LLM API生成总结"""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    prompt = f"""

You are a helpful assistant. Context information is below.

Please tell me the title of the article, the institution(s) of authors, and the publish year of the article.

Then, using the provided context information, write a comprehensive summary of the artical. Use prior knowledge only if the given context didn't provide enough information. Espectially, notice the problem/difficulties that this work deals with, and how it solves the problems.

Reply in zh-CN. For key terms or specialized nouns, please provide the original term in parentheses.

Context: 
{text[:65535]}"""  # 控制上下文长度

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "model": "deepseek-ai/DeepSeek-R1",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"\nAPI调用失败: {str(e)}")
        return None


def process_single_file(pdf_path):
    """处理单个PDF文件"""
    # 生成输出路径
    base_name = os.path.splitext(pdf_path)[0]
    md_path = f"{base_name}.md"

    # 跳过已处理文件
    if os.path.exists(md_path):
        return "skipped"

    # 解析PDF
    pdf_text = parse_pdf(pdf_path)
    if not pdf_text:
        return "failed"

    # 生成总结
    summary = summarize_text(pdf_text)
    if not summary:
        return "failed"

    # 保存结果
    try:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 文献总结\n\n")
            f.write(f"**源文件**: `{os.path.basename(pdf_path)}`\n\n")
            f.write(summary)
        return "success"
    except Exception as e:
        print(f"\n写入失败 {md_path}: {str(e)}")
        return "failed"


def batch_process_pdfs(root_dir):
    """批量处理目录中的所有PDF"""
    # 收集所有PDF文件
    pdf_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, f))

    print(f"找到 {len(pdf_files)} 个PDF文件")

    # 处理进度跟踪
    stats = {"success": 0, "failed": 0, "skipped": 0}

    # 使用进度条
    with tqdm(total=len(pdf_files), desc="处理进度") as pbar:
        for pdf_path in pdf_files:
            result = process_single_file(pdf_path)
            stats[result] += 1
            pbar.update(1)
            pbar.set_postfix(stats)

    # 打印统计结果
    print(f"\n处理完成：")
    print(f"成功: {stats['success']}")
    print(f"跳过: {stats['skipped']}")
    print(f"失败: {stats['failed']}")


if __name__ == "__main__":
    # 安装依赖：pip install pymupdf pdf2image pytesseract requests tqdm
    batch_process_pdfs(INPUT_DIR)
