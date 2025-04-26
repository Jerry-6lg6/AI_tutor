
# AI Tutor - RAG-Powered Assistant for Computer Science Students

Welcome to the RAG-powered AI tutor for computer science learning. This system is designed to assist students with academic queries related to

- Algorithms  
  Suitable for University of Liverpool Year 2 Computer Science students enrolled in Complexity of Algorithms (COMP201)

- SQL and XML  
  Suitable for students taking Database Development (COMP207)

- Programming & Software Engineering  
  Suitable for students in Software Engineering (COMP201)

- Other related programming language:
  Python, Java, C, C++...

This system leverages Retrieval-Augmented Generation (RAG) and the DeepSeek-R18B large language model to deliver context-aware, accurate responses — a significant enhancement over standard LLMs.

---

## 🚀 Features

- LLM-based conversational assistant
- Retrieval-augmented responses
- File and folder-based knowledge injection
- LightDark mode UI

---

## 🖥 Environment & Requirements

- OS Windows 1011, macOS, Linux  
- Python 3.12 or higher  
- Hardware Minimum 16GB RAM (to run 8B model locally)  
- Disk Space 30GB+ (for model + dependencies)  
- Internet Access Required for Ollama and model downloads

---

# 🚀 Installation Guide

This guide will walk you through installing Ollama, downloading the DeepSeek-R1:8B model, and setting up the Python development environment for the project.

---

## 📦 1. Install Ollama

**Ollama** is a tool for running large language models locally.

### 🔧 Installation Steps

1. Visit the official website: [https://ollama.com/](https://ollama.com/)
2. Download and install Ollama according to your operating system.
3. After installation, open your terminal and run:

```bash
ollama list
```

> ✅ If a list (even if empty) appears, Ollama has been installed successfully!

---

## 🧐 2. Download and Run DeepSeek-R1:8B Model

### 🚀 Run the following command in your terminal:

```bash
ollama run deepseek-r1:8b
```

> ⚠️ **Note:** The model file is large (\~20GB+). Downloading may take a significant amount of time depending on your internet speed.

---

## 🐍 3. Set Up Python Development Environment

### 📁 Step 1: Clone or Download Project Source Code

Clone the repository or download the project files to your local machine.

### 📊 Step 2: Create and Activate a Python Virtual Environment

#### macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 📦 Step 3: Install Required Dependencies

#### ✅ Recommended: Use `requirements.txt`

Make sure you are in the `group_project` folder, then run:

```bash
pip install -r requirements.txt
```

#### 🛠️ Alternatively, install manually:

```bash
pip install dash dash-bootstrap-components feffery-antd-components transformers torch faiss-cpu httpx pandas numpy plotly
```
### 
--- 📦 Step 4: Install Required Dependencies

## ✅ All Set!

You have successfully installed all required tools and dependencies. 🎉\
You are now ready to start developing and running your local AI projects!

---

> If you encounter any issues, please refer to the official documentation or reach out to the project maintainers.


