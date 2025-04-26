import os
import json
import pickle
import faiss
import numpy as np

def search_top_k(query, index, metadata, embed_fn, k=5):
    emb = embed_fn(query)
    v = emb.numpy().astype('float32').reshape(1, -1)
    D, I = index.search(v, k)
    return "\n\n".join([metadata[i] for i in I[0] if i < len(metadata)])

def load_vectorstore(base_path):
    """
    通用加载向量数据库：自动识别格式（.json+.json+.faiss 或 .faiss+.pkl）

    base_path: 不带扩展名的主路径（如 ./data/c_folder/c 或 ./data/Database Systems_folder/index）
    返回：
        index: FAISS 索引
        metadata: 对应文本或文件名列表
    """
    faiss_path = base_path + ".faiss"
    pkl_path = base_path + ".pkl"
    json_index_path = base_path + "_index"
    json_links_path = base_path + "_links.json"
    f_index_path = os.path.join(os.path.dirname(base_path), "f_index")

    if os.path.exists(faiss_path) and os.path.exists(pkl_path):
        # 新结构：index.faiss + index.pkl
        index = faiss.read_index(faiss_path)
        with open(pkl_path, "rb") as f:
            metadata = pickle.load(f)
        return index, metadata

    elif os.path.exists(json_index_path) and os.path.exists(json_links_path) and os.path.exists(f_index_path):
        # 原结构：_index + _links.json + f_index（模拟 metadata）
        index = faiss.read_index(f_index_path)
        with open(json_links_path, "r", encoding="utf-8") as f:
            metadata = list(json.load(f).keys())  # 或者 value 值，看你想展示啥
        return index, metadata

    else:
        raise FileNotFoundError(f"未找到有效向量数据库结构：{base_path}")