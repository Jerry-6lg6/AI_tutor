# utils/pdf_pipeline.py

import os
from utils.pdf_to_json import convert_pdf_to_json
from utils.build_all_vectorstores import build_vectorstore_for_subject

def handle_uploaded_pdf(course: str, pdf_path: str, base_pdf_dir: str, base_json_dir: str, vectorstore_dir: str):
    """
    一键处理上传的 PDF：
    - 保存自己到 data/pdf/<course>/xxx.pdf
    - 解析成 JSON 到 data/pdf_output/<course>/xxx.json
    - 重新构建 FAISS 向量库
    """
    filename = os.path.basename(pdf_path)

    # 1. 移动 PDF 到 pdf/<course>/
    pdf_target_dir = os.path.join(base_pdf_dir, course)
    os.makedirs(pdf_target_dir, exist_ok=True)
    pdf_target_path = os.path.join(pdf_target_dir, filename)
    os.rename(pdf_path, pdf_target_path)

    # 2. 转换为 JSON
    json_target_dir = os.path.join(base_json_dir, course)
    os.makedirs(json_target_dir, exist_ok=True)
    convert_pdf_to_json(pdf_target_path, json_target_dir)

    # 3. 重新构建该课程的向量库
    build_vectorstore_for_subject(course, base_json_dir, vectorstore_dir)
