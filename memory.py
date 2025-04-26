from collections import deque
from typing import Dict
import json
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), "data_memory")
os.makedirs(DATA_DIR, exist_ok=True)


class SimpleChatMemory:
    def __init__(self, max_length=3):
        self.window = deque(maxlen=max_length)
        self.text = ''
        self.prompt = f'''#Context#
You are a professional computer instructor who focuses on answering students' computer questions. Your has the ability to summarize the answer you given in sentences without losing any main point.
#Objective#
<text>{self.text}</text>
Please summarize the contents between <text> and </text>, and list them as summary sentences. Sentences are composed of subject, predicate and object, and the subject cannot use pronouns. Each sentence can be redundant, but all summary sentences can summarize the entire text. For the content that has a parallel relationship, please summarize separately, and the summary contains all the details of the text.
For the content that does not have a whole paragraph or complete sentence, please also extract and summarize, the summarized sentences should be able to fully reflect the text. If there is a paragraph in the text that is specific details, please reserve the output as a separate knowledge point. A continuous, uninterrupted list of string format is generated to generate answers.
#Style#
Clear logic, step-by-step explanation
#Tone#
Be simple and clear, but keep it professional
#Response#
Your answer only needs to contain a summary, here is a specific example of the generation: [' summary knowledge point 1', 'summary knowledge point 2',...,' summary knowledge point n'], please generate in strict accordance with this format, do not have a newline symbol and other symbols appear, each knowledge point is a string, and the knowledge point is separated by a comma without being interrupted by other content."'''

    def add_message(self, query, content):
        self.window.append({"query": query, "content": content})
        self.text = content

    def get_messages(self):
        return list(self.window)

    def clear(self):
        self.window.clear()
        return 0

    def save_to_file(self, user_id: str, session_id: str):
        file_path = os.path.join(DATA_DIR, f"{user_id}_{session_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.get_messages(), f, ensure_ascii=False, indent=2)


class ChatHistoryPool:
    def __init__(self):
        # 结构：{ user_id: { session_id: ChatHistoryManager } }
        self.pool: Dict[str, Dict[str, SimpleChatMemory]] = {}

    def get_or_create(self, user_id: str, session_id: str) -> SimpleChatMemory:
        if user_id not in self.pool:
            self.pool[user_id] = {}
        if session_id not in self.pool[user_id]:
            self.pool[user_id][session_id] = SimpleChatMemory()
        return self.pool[user_id][session_id]

    def clear_session(self, user_id: str, session_id: str):
        if user_id in self.pool and session_id in self.pool[user_id]:
            self.pool[user_id][session_id].clear()

    def clear_user_all_sessions(self, user_id: str):
        if user_id in self.pool:
            del self.pool[user_id]

    def get_user_sessions(self, user_id: str) -> Dict[str, SimpleChatMemory]:
        return self.pool.get(user_id, {})

    def save_to_file(self, user_id: str, session_id: str):
        file_path = os.path.join(DATA_DIR, f"{user_id}_{session_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.get_or_create(user_id=user_id, session_id=session_id), f, ensure_ascii=False, indent=2)

    def load_all_from_files(self):
        if not os.path.exists(DATA_DIR):
            return
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                try:
                    user_id, session_id = filename.replace(".json", "").split("_", 1)
                    file_path = os.path.join(DATA_DIR, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    memory = SimpleChatMemory.from_dict(data)
                    if user_id not in self.pool:
                        self.pool[user_id] = {}
                    self.pool[user_id][session_id] = memory
                except Exception as e:
                    print(f"⚠️ 加载聊天记录失败: {filename} → {e}")


# 实例
history_pool = ChatHistoryPool()
