# build_all_vectorstores.py
# ✅ 构建多个向量数据库（每个学科一个 vectorstore 子目录）

import os
import json
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ✅ 自动定位项目路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ 输入 JSON 路径（来自 PDF 提取）
PDF_ROOT = os.path.join(BASE_DIR, "..", "data", "pdf_output")

# ✅ 输出 FAISS 向量数据库路径
VECTORSTORE_ROOT = os.path.join(BASE_DIR, "..", "data", "vectorstore")

# ✅ 初始化嵌入模型（只初始化一次）
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ✅ 遍历每个课程目录
for subject in os.listdir(PDF_ROOT):
    subject_path = os.path.join(PDF_ROOT, subject)
    if not os.path.isdir(subject_path):
        continue

    all_docs = []
    for file in os.listdir(subject_path):
        if file.endswith(".json"):
            file_path = os.path.join(subject_path, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, dict):
                    continue

                for page, content in data.items():
                    if content.strip():
                        all_docs.append(Document(
                            page_content=content,
                            metadata={
                                "domain": subject,
                                "filename": file,
                                "page": page
                            }
                        ))
                print(f"✅ 加载：{file_path}")
            except Exception as e:
                print(f"❌ 错误：{file_path}，原因：{e}")

    if not all_docs:
        print(f"⚠️ 跳过：{subject}（无有效文档）")
        continue

    # ✅ 切分文本 & 构建数据库
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(all_docs)

    # ✅ 输出目录统一为 group_project/data/vectorstore/{subject}
    subject_vectorstore_path = os.path.join(VECTORSTORE_ROOT, subject)
    os.makedirs(subject_vectorstore_path, exist_ok=True)

    db = FAISS.from_documents(split_docs, embedding)
    db.save_local(subject_vectorstore_path)

    print(f"✅ 构建完成：{subject}，保存到 {subject_vectorstore_path}，共 {len(split_docs)} 块")

print("🎉 所有向量数据库已构建完成！")