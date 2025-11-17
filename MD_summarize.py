"""
Markdown文件分析脚本
读取指定目录下的所有markdown文件，调用LLM API生成研究报告
"""

import os
import glob
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
import requests
from pathlib import Path

# 配置区域 - 请修改这里的路径
MARKDOWN_DIRECTORY = "/path/to/your/markdown" 
# Example: if your file is "/Users/mac/Desktop/file.md", then MARKDOWN_DIRECTORY = "/Users/mac/Desktop"

API_BASE = "https://api.siliconflow.cn/v1"
# Buy an API key on siliconflow or elsewhere. Deepseek is cheap, almost free.

API_KEY = "your-api-key"
MODEL = "deepseek-ai/DeepSeek-R1"

class MarkdownAnalyzer:
    def __init__(self, api_key: str, api_base: str = None, model: str = "deepseek-ai/DeepSeek-R1"):
        """
        初始化分析器
        
        Args:
            api_key: LLM API密钥
            api_base: API基础URL（可选，用于自定义API端点）
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.api_base = api_base or "https://api.siliconflow.cn/v1"
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def read_markdown_files(self, directory: str) -> List[Dict[str, str]]:
        """
        读取目录下的所有markdown文件
        
        Args:
            directory: 目录路径
            
        Returns:
            包含文件名和内容的字典列表
        """
        md_files = []
        pattern = os.path.join(directory, "*.md")
        
        for file_path in glob.glob(pattern):
            # 跳过文件名开头为research_report的文件
            filename = os.path.basename(file_path)
            if filename.startswith("research_report"):
                print(f"跳过文件: {file_path}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    md_files.append({
                        'filename': filename,
                        'content': content,
                        'path': file_path
                    })
                print(f"已读取文件: {file_path}")
            except Exception as e:
                print(f"读取文件失败 {file_path}: {e}")
        
        return md_files
    
    def call_llm_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        调用LLM API
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            
        Returns:
            API响应内容
        """
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                json=data,
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        
        except requests.exceptions.RequestException as e:
            print(f"API调用失败: {e}")
            return ""
        except KeyError as e:
            print(f"API响应格式错误: {e}")
            return ""
    
    def analyze_papers(self, md_files: List[Dict[str, str]]) -> str:
        """
        分析论文内容并生成研究报告
        
        Args:
            md_files: markdown文件列表
            
        Returns:
            生成的研究报告
        """
        # 构建分析提示词
        papers_content = ""
        for i, file_info in enumerate(md_files, 1):
            papers_content += f"\n=== 论文 {i}: {file_info['filename']} ===\n"
            papers_content += file_info['content'] + "\n"
        
#         prompt = f"""
# 你是一位专业的研究分析师。请分析以下论文总结内容，生成一份综合研究报告。

# 论文内容：
# {papers_content}

# 你可以参考以下结构及其中建议的内容生成研究报告：

# # 研究报告

# ## 1. 研究背景
# - 分析这些论文共同关注的研究领域
# - 总结该领域的发展现状和重要性

# ## 2. 主要现存问题
# - 识别论文中提到的核心问题和挑战
# - 按重要性排序，详细说明每个问题

# ## 3. 解决方案分析
# - 总结论文中提出的各种解决方案
# - 分析每种方案的优缺点
# - 评估解决方案的可行性和效果

# ## 4. 横向对比分析
# - 对比不同论文的方法和观点
# - 识别共识和分歧点
# - 分析各方案的创新性和实用性

# ## 5. 发展趋势与展望
# - 基于现有研究分析未来发展方向
# - 提出潜在的研究机会
# - 给出研究建议

# ## 6. 结论
# - 总结主要发现
# - 提出关键洞察

# 请确保报告内容详实、逻辑清晰、分析深入。使用中文撰写。
# """
        prompt = f"""
        你是一位专业的研究分析师。请分析以下论文总结内容，生成一份该选题的研究报告。
        
        论文内容：
        {papers_content}
        
        请确保报告内容详实、逻辑清晰、分析深入。使用中文撰写。
        如果涉及引用，请标明引用内容来自哪一篇论文。
        """
        print("正在生成API请求...")
        report = self.call_llm_api(prompt, max_tokens=65535)

        return report

    def save_report(self, report: str, output_path: str):
        """
        保存报告到文件

        Args:
            report: 报告内容
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"研究报告已保存到: {output_path}")
        except Exception as e:
            print(f"保存报告失败: {e}")


def main():
    # 使用硬编码的配置
    directory = MARKDOWN_DIRECTORY
    api_key = API_KEY
    api_base = API_BASE
    model = MODEL

    # 检查目录是否存在
    if not os.path.isdir(directory):
        print(f"错误: 目录 '{directory}' 不存在")
        print(f"请修改脚本中的 MARKDOWN_DIRECTORY 变量为正确的路径")
        return

    # 检查API密钥是否已配置
    if api_key == "your-api-key-here":
        print("错误: 请修改脚本中的 API_KEY 变量为你的实际API密钥")
        return

    # 生成输出文件名（保存在同一目录下）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(directory, f"research_report_{timestamp}.md")

    # 创建分析器
    analyzer = MarkdownAnalyzer(
        api_key=api_key,
        api_base=api_base,
        model=model
    )

    print(f"开始分析目录: {directory}")

    # 读取markdown文件
    md_files = analyzer.read_markdown_files(directory)

    if not md_files:
        print("未找到任何markdown文件")
        return

    print(f"找到 {len(md_files)} 个markdown文件")

    # 分析论文并生成报告
    report = analyzer.analyze_papers(md_files)

    # 在报告末尾追加“论文编号 ↔ 文件名”的对应关系，方便查看引用来源
    if report:
        appendix = "\n\n---\n\n参考论文列表（编号与文件名对应）：\n"
        for i, file_info in enumerate(md_files, 1):
            appendix += f"\n论文 {i}: {file_info['filename']}\n"
        report += appendix

    if not report:
        print("分析失败，报告未保存")
    else:
        # 保存报告
        analyzer.save_report(report, output_path)
        print("分析完成！")


if __name__ == "__main__":
    main()
