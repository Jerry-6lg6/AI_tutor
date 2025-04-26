import pdfplumber
import os
import json


def convert_pdf_to_json(pdf_path: str, output_json_path: str):
    import pdfplumber
    import json

    pdf_data = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pdf_data[f"Page {page_number}"] = text

    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(pdf_data, json_file, ensure_ascii=False, indent=4)

    print(f"✅ 已转换 PDF 为 JSON：{output_json_path}")
    
def convert_all_pdfs_to_json(pdf_root: str, output_root: str):
    """
    遍历 pdf_root 下的课程文件夹，将其中 PDF 转换为 JSON，保存到 output_root 下同名子文件夹。
    例如：
        输入：data/pdf/cmu/lecture1.pdf
        输出：data/pdf_output/cmu/lecture1.json
    """
    for subject in os.listdir(pdf_root):
        subject_path = os.path.join(pdf_root, subject)
        if not os.path.isdir(subject_path):
            continue

        output_subject_path = os.path.join(output_root, subject)
        os.makedirs(output_subject_path, exist_ok=True)

        for file_name in os.listdir(subject_path):
            if file_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(subject_path, file_name)
                pdf_filename = os.path.splitext(file_name)[0]
                json_output = os.path.join(output_subject_path, f"{pdf_filename}.json")
                pdf_data = {}

                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page_number, page in enumerate(pdf.pages, start=1):
                            text = page.extract_text()
                            if text:
                                pdf_data[f"Page {page_number}"] = text
                            print(f"✅ 提取 {file_name} 的第 {page_number} 页")

                    with open(json_output, "w", encoding="utf-8") as json_file:
                        json.dump(pdf_data, json_file, ensure_ascii=False, indent=4)

                    print(f"🎉 完成：{file_name} 的 JSON 已保存到 {json_output}")
                except Exception as e:
                    print(f"❌ 错误：{file_name} 提取失败，原因：{e}")

    print("✅ 所有课程 PDF 已转换为 JSON 文件！")