import os
import re
import fitz  # PyMuPDF
from tqdm import tqdm
import unicodedata


def sanitize_filename(title):
    """清理文件名中的非法字符"""
    # 保留允许的字符（汉字、字母、数字、下划线和连字符）
    cleaned = unicodedata.normalize('NFKC', title)  # 转换全角字符
    cleaned = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', cleaned)  # 替换非法字符
    cleaned = re.sub(r'_+', '_', cleaned)  # 合并连续下划线
    return cleaned.strip('_')[:200]  # 限制长度


def extract_pdf_title(pdf_path):
    """从PDF中提取标题（优先元数据，其次内容分析）"""
    try:
        with fitz.open(pdf_path) as doc:
            # 方法1：检查文档元数据
            # meta_title = doc.metadata.get('title', '').strip()
            # if meta_title and len(meta_title) > 3:
            #     return meta_title

            # 方法2：分析前两页内容
            for page_num in range(min(2, len(doc))):
                page = doc.load_page(page_num)
                text = page.get_text("text")

                # 查找可能标题的特征
                lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
                for line in lines[:10]:  # 检查前10行
                    if 10 <= len(line) <= 200 and not line.isdigit():
                        # 排除页眉页脚常见内容
                        if re.search(r'page|第.*页|confidential', line, re.I):
                            continue
                        return line

                # 方法3：查找最大字号文本
                blocks = page.get_text("dict")["blocks"]
                font_sizes = []
                for b in blocks:
                    if "lines" in b:
                        for line in b["lines"]:
                            for span in line["spans"]:
                                font_sizes.append((span["text"], span["size"]))
                if font_sizes:
                    largest = max(font_sizes, key=lambda x: x[1])
                    if largest[1] > 11:  # 忽略正文字号
                        return largest[0]

    except Exception as e:
        print(f"\n解析失败 {pdf_path}: {str(e)}")

    return None


def rename_pdf_file(pdf_path, new_name):
    """安全重命名文件"""
    dir_path = os.path.dirname(pdf_path)
    new_path = os.path.join(dir_path, new_name + ".pdf")

    # 处理重复文件名
    counter = 1
    while os.path.exists(new_path):
        new_path = os.path.join(dir_path, f"{new_name}_{counter}.pdf")
        counter += 1

    try:
        os.rename(pdf_path, new_path)
        return True
    except Exception as e:
        print(f"\n重命名失败 {pdf_path}: {str(e)}")
        return False


def process_folder(root_dir):
    """处理目录及其子目录"""
    pdf_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, f))

    print(f"找到 {len(pdf_files)} 个PDF文件")

    stats = {"renamed": 0, "failed": 0, "skipped": 0}

    with tqdm(total=len(pdf_files), desc="处理进度") as pbar:
        for pdf_path in pdf_files:
            try:
                title = extract_pdf_title(pdf_path)
                if not title:
                    stats["skipped"] += 1
                    pbar.update(1)
                    continue

                clean_title = sanitize_filename(title)
                if not clean_title:
                    stats["skipped"] += 1
                    pbar.update(1)
                    continue

                if rename_pdf_file(pdf_path, clean_title):
                    stats["renamed"] += 1
                else:
                    stats["failed"] += 1

                pbar.update(1)
                pbar.set_postfix(stats)

            except Exception as e:
                print(f"\n处理异常 {pdf_path}: {str(e)}")
                stats["failed"] += 1
                pbar.update(1)

    print("\n处理结果：")
    print(f"成功重命名: {stats['renamed']}")
    print(f"失败文件: {stats['failed']}")
    print(f"跳过文件: {stats['skipped']}")


if __name__ == "__main__":
    # 配置参数
    PDF_DIR = "/path/to/your/pdf"  # 修改为你的PDF目录

    # 安装依赖：pip install pymupdf tqdm
    process_folder(PDF_DIR)
