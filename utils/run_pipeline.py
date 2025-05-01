import os
import json
import shutil
import pdfplumber
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# === Path Settings ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_INPUT_DIR = os.path.join(BASE_DIR, "..", "uploads")
JSON_OUTPUT_DIR = os.path.join(BASE_DIR, "..", "uploads", "uploads_pdf_json")
VECTORSTORE_BASE = os.path.join(BASE_DIR, "..", "data")

# === Step 1: Convert PDFs to JSON ===
def convert_all_pdfs_to_json(pdf_root: str, output_root: str):
    if os.path.exists(output_root):
        shutil.rmtree(output_root)
        print(f"🧹 Cleared old JSON folder: {output_root}")
    os.makedirs(output_root, exist_ok=True)

    for file_name in os.listdir(pdf_root):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_root, file_name)
            pdf_filename = os.path.splitext(file_name)[0]
            json_output = os.path.join(output_root, f"{pdf_filename}.json")
            pdf_data = {}

            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_number, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text()
                        if text:
                            pdf_data[f"Page {page_number}"] = text
                        print(f"Extracted page {page_number} from {file_name}")

                with open(json_output, "w", encoding="utf-8") as json_file:
                    json.dump(pdf_data, json_file, ensure_ascii=False, indent=4)

                print(f"✅ JSON saved: {json_output}")
            except Exception as e:
                print(f"❌ Failed to extract {file_name}: {e}")
    print("✅ All PDFs converted to JSON.")

# === Step 2: Build Vectorstore ===
def build_vectorstore_from_json(json_dir: str, output_base: str):
    def get_new_upload_folder(base_dir, prefix="pdf_upload"):
        i = 1
        while True:
            folder_name = f"{prefix}({i})"
            full_path = os.path.join(base_dir, folder_name)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                return full_path
            i += 1

    all_docs = []
    for file in os.listdir(json_dir):
        if file.endswith(".json"):
            file_path = os.path.join(json_dir, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    for page, content in data.items():
                        if content and isinstance(content, str) and content.strip():
                            all_docs.append(Document(
                                page_content=content,
                                metadata={"filename": file, "page": page}
                            ))
                    print(f"Loaded: {file}")
                else:
                    print(f"⚠️ Skipped (not a dict): {file}")
            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")

    if not all_docs:
        print("⚠️ No valid documents. Vectorstore not built.")
        return

    # Embedding
    embedding = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
        query_instruction="Represent this sentence for retrieving relevant documents:"
    )

    # Split & save
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(all_docs)
    output_dir = get_new_upload_folder(output_base)
    db = FAISS.from_documents(split_docs, embedding)
    db.save_local(output_dir)

    print(f"🎉 Vectorstore built with {len(split_docs)} chunks → {output_dir}")

# === Step 3: Clean processed PDFs
def clean_uploaded_pdfs(pdf_root: str):
    for file in os.listdir(pdf_root):
        file_path = os.path.join(pdf_root, file)
        if os.path.isfile(file_path) and file.lower().endswith(".pdf"):
            os.remove(file_path)
    print(f"🗑️ Cleaned uploaded PDFs in: {pdf_root}")

# === Main Runner
def run_full_pipeline():
    print("🚀 Starting pipeline: process newly uploaded PDFs")
    convert_all_pdfs_to_json(PDF_INPUT_DIR, JSON_OUTPUT_DIR)
    build_vectorstore_from_json(JSON_OUTPUT_DIR, VECTORSTORE_BASE)
    clean_uploaded_pdfs(PDF_INPUT_DIR)  # ✅ only clean after processing
    print("✅ Done! Vectorstore created and upload folder cleared.")

# === Entry Point
if __name__ == "__main__":
    run_full_pipeline()