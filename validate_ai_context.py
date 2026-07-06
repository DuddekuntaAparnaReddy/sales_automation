# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests, json, time

BASE = "http://127.0.0.1:8000"

def chat(query, history):
    r = requests.post(f"{BASE}/api/ai/chat", json={
        "query": query,
        "conversation_history": history
    })
    return r.json().get("response", "[no response]")

print("=" * 60)
print("VALIDATION: Context-Aware AI Chatbot Test")
print("=" * 60)

# Turn 1: user mentions budget
history = []
q1 = "I need a laptop under ₹100000"
print(f"\n[User]: {q1}")
r1 = chat(q1, history)
print(f"[Bot ]: {r1}")
history.append({"role": "user", "content": q1})
history.append({"role": "assistant", "content": r1})

time.sleep(1)

# Turn 2: user provides use case — AI MUST now recommend, not ask again
q2 = "Gaming"
print(f"\n[User]: {q2}")
r2 = chat(q2, history)
print(f"[Bot ]: {r2}")

print("\n" + "=" * 60)
print("PASS if response above contains laptop recommendations.")
print("FAIL if response above asks 'What are you looking for?' again.")
print("=" * 60)

# Check for failure keywords
fail_keywords = ["what product", "what are you looking", "what type of product", "what will you use"]
passed = not any(kw.lower() in r2.lower() for kw in fail_keywords)
print(f"\nResult: {'✅ PASS' if passed else '❌ FAIL'}")
