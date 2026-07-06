# -*- coding: utf-8 -*-
import sys, io, requests, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:8000/api/ai/chat"

def contains_word(text, word):
    # Match as complete word boundary
    pattern = r'\b' + re.escape(word.lower()) + r'\b'
    return bool(re.search(pattern, text.lower()))

def run_test(case_num, query, expected_keywords, unexpected_keywords=None):
    print(f"\n[TEST {case_num}] User: \"{query}\"")
    payload = {
        "query": query,
        "conversation_history": []
    }
    try:
        r = requests.post(BASE, json=payload)
        if not r.ok:
            print(f"    FAIL: Status {r.status_code} | {r.text}")
            return False
        
        reply = r.json().get("response", "")
        print(f"    Reply: {reply}")
        
        # Verify keywords
        passed = True
        for keyword in expected_keywords:
            if not contains_word(reply, keyword):
                print(f"    FAIL: Expected word '{keyword}' missing in reply.")
                passed = False
        
        if unexpected_keywords:
            for kw in unexpected_keywords:
                if contains_word(reply, kw):
                    print(f"    FAIL: Unexpected word '{kw}' found in reply.")
                    passed = False
                    
        if passed:
            print("    PASS")
        return passed
    except Exception as e:
        print(f"    FAIL: Exception {e}")
        return False

print("=" * 60)
print("TESTING: Universal Sales & Marketing AI Assistant")
print("=" * 60)

# Test 1: Laptop
run_test(
    1,
    "I need a gaming laptop under ₹100000",
    ["laptop", "gaming"],
    ["land", "cement", "car", "steel"]
)

# Test 2: Real Estate / Land
run_test(
    2,
    "I want agricultural land near Hyderabad",
    ["land", "acres", "budget"], # Llama asked for acres and budget
    ["laptop", "cement", "car", "steel"]
)

# Test 3: Construction Materials / Steel
run_test(
    3,
    "I need steel rods for construction",
    ["steel", "rods", "construction"],
    ["laptop", "hyderabad", "car"]
)

# Test 4: Vehicles / Car
run_test(
    4,
    "I want a car under 15 lakhs",
    ["car", "lakhs", "usage"],
    ["laptop", "cement", "hyderabad", "steel"]
)

print("=" * 60)
print("Testing complete.")
print("=" * 60)

