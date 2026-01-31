# src/chatbot.py
print("🔥 CHATBOT.PY LOADED 🔥")

import os
import json
import re
import requests
from datetime import datetime
from src.autocorrect import autocorrect_query
from src.mathbot import handle_math_query

# ---------------- FILE SETUP ---------------- #

DATA_DIR = "src/data"
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
PROGRAMMING_FILE = os.path.join(DATA_DIR, "programming.json")

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"chat_history": []}, f, indent=4)

HEADERS = {"User-Agent": "INDB-Diet-Pro/1.0"}

last_topic = None

# ---------------- MEMORY ---------------- #

def load_memory():
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

def remember_chat(question, answer):
    memory = load_memory()
    history = memory.get("chat_history", [])
    history.append({"q": question, "a": answer})
    memory["chat_history"] = history[-20:]
    save_memory(memory)

def recall_previous(msg):
    memory = load_memory()
    for item in reversed(memory.get("chat_history", [])):
        if msg in item["q"]:
            return item["a"]
    return None

# ---------------- ENTITY CLEANING ---------------- #

def clean_entity(msg):
    remove = [
        "who is", "what is", "tell me about", "explain",
        "details of", "information about", "when was", "when is"
    ]
    msg = msg.lower()
    for r in remove:
        msg = msg.replace(r, "")
    return msg.replace("?", "").strip()

# ---------------- SEARCH ---------------- #

def wikipedia_search(query):
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 1,
            "namespace": 0,
            "format": "json"
        }
        r = requests.get(search_url, params=params, timeout=6)
        data = r.json()

        if not data[1]:
            return None

        title = data[1][0].replace(" ", "_")
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        res = requests.get(summary_url, timeout=6)

        if res.status_code == 200:
            return res.json().get("extract")
    except:
        return None

def duckduckgo_search(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        res = requests.get(url, params=params, headers=HEADERS, timeout=6)
        data = res.json()

        if data.get("AbstractText"):
            return data["AbstractText"]

        for t in data.get("RelatedTopics", []):
            if isinstance(t, dict) and t.get("Text"):
                return t["Text"]
    except:
        return None

# ---------------- FACT MEMORY ---------------- #

def remember_fact(msg):
    memory = load_memory()

    if "my name is" in msg:
        name = msg.split("my name is")[-1].strip().title()
        memory["user_name"] = name
        save_memory(memory)
        return f"Got it 👍 Your name is {name}."

    if "my birthdate is" in msg or "my dob is" in msg:
        date_str = msg.replace("my birthdate is", "").replace("my dob is", "").strip()
        try:
            dob = datetime.strptime(date_str, "%d-%m-%Y")
            memory["dob"] = date_str
            memory["age"] = datetime.now().year - dob.year
            save_memory(memory)
            return "Your birthdate is saved."
        except:
            return "Please use DD-MM-YYYY format."

    return None

def recall_fact(msg):
    memory = load_memory()

    if "my name" in msg and "user_name" in memory:
        return memory["user_name"]

    if "my birthdate" in msg and "dob" in memory:
        return memory["dob"]

    if "my age" in msg and "age" in memory:
        return str(memory["age"])

    return None

# ---------------- TECH / PROGRAMMING ---------------- #

def get_programming_answer(msg):
    if not os.path.exists(PROGRAMMING_FILE):
        return None

    with open(PROGRAMMING_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key, value in data.items():
        if key in msg:
            return value
    return None

# ---------------- INTENT DETECTION ---------------- #

def detect_intent(msg):
    if re.search(r"\b(hi|hello|hey)\b", msg):
        return "SMALL_TALK"

    if any(k in msg for k in ["sin", "cos", "area", "derivative", "+", "-", "*", "/", "^"]):
        return "MATH"

    if any(k in msg for k in ["python", "java", "c++", "programming"]):
        return "TECH"

    if any(k in msg for k in ["my name", "my age", "my birth"]):
        return "PERSONAL"

    return "FACT"

# ---------------- MAIN RESPONSE ---------------- #

def get_smart_response(message: str) -> str:
    original = message
    corrected = autocorrect_query(message)

    print("📝 USER :", original)
    print("🧠 FIXED:", corrected)

    # 🔥 use corrected text from now on
    message = corrected
    global last_topic

    msg = message.lower().strip()
    print("🧪 MSG:", msg)

    intent = detect_intent(msg)
    print("🧠 INTENT:", intent)

    # 1️⃣ Small talk
    if intent == "SMALL_TALK":
        return "Hey 👋 How can I help you?"

    # 2️⃣ Math → delegate
    if intent == "MATH":
        math_answer = handle_math_query(msg)
        if math_answer != "Unknown math query":
            return math_answer

    # 3️⃣ Save personal facts
    saved = remember_fact(msg)
    if saved:
        remember_chat(message, saved)
        return saved

    # 4️⃣ Recall personal facts
    recalled = recall_fact(msg)
    if recalled:
        return recalled

    # 5️⃣ Programming / Tech
    if intent == "TECH":
        tech = get_programming_answer(msg)
        if tech:
            remember_chat(message, tech)
            return tech

    # 6️⃣ Factual lookup
    entity = clean_entity(msg)
    last_topic = entity

    summary = wikipedia_search(entity) or duckduckgo_search(entity)
    if summary:
        remember_chat(message, summary)
        return summary

    # 7️⃣ Recall similar past question
    past = recall_previous(msg)
    if past:
        return past

    return "I couldn’t find a direct answer to that."
