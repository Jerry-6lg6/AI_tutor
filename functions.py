from transformers import AutoTokenizer, AutoModel
import torch
import json
from tqdm import tqdm
import numpy as np
import faiss
import os
import requests
import httpx
from typing import AsyncGenerator
from memory import history_pool
import pickle
from utils.vector_utils import load_vectorstore, search_top_k


def get_dropdown_options_from_folder(folder_path):
    options = []
    for folder_name in os.listdir(folder_path):
        folder_path_full = os.path.join(folder_path, folder_name)
        if os.path.isdir(folder_path_full):
            # 新格式支持检测
            index_base = os.path.join(folder_path_full, "index")
            if os.path.exists(index_base + ".faiss") and os.path.exists(index_base + ".pkl"):
                label = folder_name.replace("_folder", "")
                options.append({'label': label, 'value': label})
            # 原格式支持
            elif os.path.exists(os.path.join(folder_path_full, "f_index")):
                label = folder_name.replace("_folder", "")
                options.append({'label': label, 'value': label})
    return options


def get_text_auto(key, query):
    base_folder = os.path.join("data", f"{key}_folder")
    new_index_path = os.path.join(base_folder, "index")
    faiss_path = new_index_path + ".faiss"
    pkl_path = new_index_path + ".pkl"

    if os.path.exists(faiss_path) and os.path.exists(pkl_path):
        index, metadata = load_vectorstore(new_index_path)
        return search_top_k(query, index, metadata, emboding_bge)
    else:
        return get_text_old(key, query)


def form_prompt(q, key):
    base_path = os.path.join("data", f"{key}_folder", "index")
    index, metadata = load_vectorstore(base_path)
    source = search_top_k(q, index, metadata, emboding_bge)

    prompt = f'''
    #Objective#                
    <query>{q}</query>
    <source>{source}</source>
    请结合<source>中内容回答<query>中提出的问题...（略）
    '''
    return prompt


def load_vectorstore(path_base: str):
    """
    加载 FAISS 索引和对应的 metadata。
    参数:
        path_base: 不带扩展名的路径（如 group_project/data/Database Systems_folder/index）
    返回:
        index: faiss.Index
        metadata: List[str]
    """
    faiss_path = path_base + ".faiss"
    meta_path = path_base + ".pkl"

    if not os.path.exists(faiss_path) or not os.path.exists(meta_path):
        raise FileNotFoundError("向量数据库或元数据文件不存在")

    index = faiss.read_index(faiss_path)
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata


def search_top_k(query: str, index, metadata, embed_model, k=5):
    # 将query进行embedding
    emb = embed_model(query)
    emb_np = emb.numpy().astype('float32').reshape(1, -1)

    # 检索 top-k
    D, I = index.search(emb_np, k)
    matched_texts = [metadata[i] for i in I[0] if i < len(metadata)]
    return "\n\n".join(matched_texts)


def emboding_bge(s):
    # 使用相对路径加载模型
    relative_model_path = "bge-large-en-v1.5"

    tokenizer = AutoTokenizer.from_pretrained(relative_model_path)
    model = AutoModel.from_pretrained(relative_model_path)

    # 测试推理
    max_length = 512
    encoded_input = tokenizer(s, max_length=max_length, padding=True, truncation=True, return_tensors='pt')

    with torch.no_grad():
        model_output = model(**encoded_input)
        sentence_embeddings = model_output.last_hidden_state[:, 0, :].squeeze(0)
        # sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

    # print("Sentence embeddings:", sentence_embeddings)
    return sentence_embeddings


def database_build(str):
    folder_path = 'data'
    # Loop through the directory
    for root, dirs, files in os.walk(folder_path):
        if len(dirs) == 0:
            vector = {}
            for filename in tqdm(files):
                new_filename = filename.rsplit('.', 1)[0]
                v = emboding_bge(new_filename)
                v_array = v.numpy().tolist()
                vector[filename] = v_array
            new_path = root.rsplit("\\", 1)[0]
            path_parts = root.split("\\")
            name = f'{path_parts[2]}_index'
            full_file_path = os.path.join(new_path, name)
            # print(full_file_path)
            with open(full_file_path, 'w', encoding='utf-8') as file:
                json.dump(vector, file, ensure_ascii=False, indent=4)

            # print(f'{root}\n{dirs}\n{files}\n...........')

    return 0


def add_index(database, key, dim=1024):
    path_index = os.path.join("data", f"{key}_folder", "index.faiss")
    index = faiss.IndexFlatL2(dim)
    v_all = []
    for k, v in database.items():
        v_modi = np.array(v, dtype='float32')
        v_all.append(v_modi)
    v_input = np.stack(v_all)
    index.add(v_input)
    faiss.write_index(index, path_index)
    return path_index


def search(str, k=3, index: faiss.IndexFlatL2 = None, map: dict = None):
    v_read = emboding_bge(str)
    v = v_read.numpy()
    v = v.astype(np.float32)
    D, I = index.search(np.array([v]), k)
    list_I = I.tolist()
    key_list = []
    for value in list_I[0]:
        key_list.append(list(map.keys())[value])
    unique_list = list(set(key_list))

    return unique_list


def get_text(key='sql', query: str = None):
    path = os.path.join("data", f"{key}_folder")
    text_list = []
    for root, dirs, files in os.walk(path):
        if len(root.split("\\")) == 3:
            path_index = os.path.join("data", f"{key}_folder", "f_index")
            path_map = os.path.join("data", f"{key}_folder", f"{key}_index")
            print(path_index)
            with open(path_map, 'r', encoding='utf-8') as file:
                map = json.load(file)
            index = faiss.read_index(path_index)
            unique_list = search(query, index=index, map=map)
            print(unique_list)
            for i in unique_list:
                full_name = f"{i}"
                path_text = os.path.join(root, full_name)
                with open(path_text, 'r', encoding='utf-8') as file:
                    text = json.load(file)
                    text_list.append(text)

    return text_list


def get_text_old(key, query):
    # 加载旧结构的 f_index、c_index、links.json 等
    f_index_path = os.path.join("data", f"{key}_folder", "f_index")
    c_index_path = os.path.join("data", f"{key}_folder", f"{key}_index.json")
    links_path = os.path.join("data", f"{key}_folder", "c_links.json")
    return get_text(key, query)  # alias 原来旧函数


def form_history(text):
    history = f'''
    #Menory#
    The following text is your memory of the conversation.
    <text>{text}</text>
    '''
    return history


def form_context(text):
    context = f'''
#Context#
You are a senior computer science teacher, helping college students majoring in computer science to learn related courses, and you are good at answering questions for students.


    '''
    return context


prompt_based = '''
    #Context#
    You are a senior computer science teacher, helping college students majoring in computer science to learn related courses, and you are good at answering questions for students.
    #Objective#                
    <query>{q}</query>
    <source>{source}</source>
    Please answer the questions between <query> and </query> by combining the contents between <source> and </source> and the relevant information between <source> and </source>.
    Explain the question in plain language, provide correct, direct, clear, step-by-step answers, and summarize relevant knowledge points. Give priority to the explanation of subject knowledge points. If it is related to a programming problem, please provide the full working code on top of the previous one, with comments.
    #Style#
    Logical and structured
    #Tone#
    Professional and friendly, be patient with beginners
    Can encourage students
    #Response#
    Your answers need to be direct, clear, and structured'''


def form_prompt(q, key):
    source = get_text_auto(key=key, query=q)
    prompt_filled = prompt_based.format(q=q, source=source)
    return prompt_filled


def query_ollama(q, user_id: str, session_id: str, key: str, prompt_new: str, model='deepseek-r1:8b', temperature=0.6,
                 input_prompt=None) -> str:
    if input_prompt and prompt_new:
        prompt = prompt_new
    else:
        history = history_pool.get_or_create(user_id, session_id)
        prompt = form_history(history) + form_prompt(q, key)

    data = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False  # Non-streaming output
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=data, timeout=None)
        response.raise_for_status()
        json_data = response.json()
        reply = json_data.get("response", "")
    except requests.RequestException as e:
        reply = f"Request error: {e}"
    except json.JSONDecodeError:
        reply = "Failed to decode response from model."

    history.add_message(query=q, content=reply)
    return reply


# Example usage
# response = query_ollama("how dose the computer work")
# print(response)

if __name__ == '__main__':
    print("hello_world")
