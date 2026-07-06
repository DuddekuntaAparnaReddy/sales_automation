# -*- coding: utf-8 -*-
import sys, io, requests, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("VALIDATION: Survey & Market Research Bot")
print("=" * 60)

# 1. Fetch initial survey stats
print("\n[1] GET /api/surveys/stats")
r = requests.get(f"{BASE}/api/surveys/stats")
print(f"    Status: {r.status_code}")
if r.ok:
    print(f"    Initial Stats: {r.json()}")
else:
    print(f"    Error: {r.text}")

# 2. Create survey
print("\n[2] POST /api/surveys (Create Q4 Product Survey)")
payload = {
    "title": "Q4 Product Preferences Survey",
    "description": "Help us identify which products and features our customer base prefers in late 2026.",
    "category": "Market Research",
    "expiry_date": "2026-12-31",
    "created_by": 1,
    "questions": [
        {
            "question_text": "How satisfied are you with our laptop products?",
            "question_type": "rating"
        },
        {
            "question_text": "Would you recommend our store to a friend?",
            "question_type": "choice"
        },
        {
            "question_text": "What specific improvements or products would you like to see next?",
            "question_type": "text"
        }
    ]
}
r = requests.post(f"{BASE}/api/surveys", json=payload)
print(f"    Status: {r.status_code}")
survey_id = None
if r.ok:
    d = r.json()
    survey_id = d.get("survey_id")
    print(f"    Created Survey ID: {survey_id}")
else:
    print(f"    Error: {r.text}")

if not survey_id:
    print("Cannot proceed without a survey ID.")
    sys.exit(1)

# 3. GET /api/surveys?status=Active
print("\n[3] GET /api/surveys?status=Active")
r = requests.get(f"{BASE}/api/surveys?status=Active")
print(f"    Status: {r.status_code}")
if r.ok:
    surveys = r.json()
    matched = [s for s in surveys if s.get("id") == survey_id]
    if matched:
        print(f"    Survey verified in active list: {matched[0].get('title')}")
    else:
        print("    Survey NOT found in active list!")
else:
    print(f"    Error: {r.text}")

# 4. Submit 3 user responses
print("\n[4] POST /api/surveys/<id>/responses (Submit 3 responses)")
responses = [
    {
        "user_id": None,
        "response_data": {
            "How satisfied are you with our laptop products?": "5 Stars",
            "Would you recommend our store to a friend?": "Yes",
            "What specific improvements or products would you like to see next?": "Excellent build quality. Please introduce high-performance gaming laptops under 1 lakh."
        }
    },
    {
        "user_id": None,
        "response_data": {
            "How satisfied are you with our laptop products?": "4 Stars",
            "Would you recommend our store to a friend?": "Yes",
            "What specific improvements or products would you like to see next?": "The laptops are great, but the shipping/delivery speed was quite slow. Took over a week."
        }
    },
    {
        "user_id": None,
        "response_data": {
            "How satisfied are you with our laptop products?": "3 Stars",
            "Would you recommend our store to a friend?": "Maybe",
            "What specific improvements or products would you like to see next?": "I want more student discounts. Gaming laptop discounts are nice, but general work laptops should have coupons too."
        }
    }
]

for idx, resp in enumerate(responses):
    r = requests.post(f"{BASE}/api/surveys/{survey_id}/responses", json=resp)
    print(f"    Submission {idx+1} status: {r.status_code} | {r.json().get('message')}")

# 5. GET /api/surveys/<id>/responses
print("\n[5] GET /api/surveys/<id>/responses")
r = requests.get(f"{BASE}/api/surveys/{survey_id}/responses")
print(f"    Status: {r.status_code}")
if r.ok:
    saved_resps = r.json()
    print(f"    Total responses retrieved: {len(saved_resps)}")
else:
    print(f"    Error: {r.text}")

# 6. POST /api/surveys/<id>/insights (Trigger Llama 3.1)
print("\n[6] POST /api/surveys/<id>/insights (Trigger Llama 3.1)")
r = requests.post(f"{BASE}/api/surveys/{survey_id}/insights")
print(f"    Status: {r.status_code}")
if r.ok:
    insights = r.json().get("insights", {})
    print(f"    Sentiment: {insights.get('sentiment')}")
    print(f"    Top Interests: {insights.get('top_interests')}")
    print(f"    Common Issues: {insights.get('common_issues')}")
    print(f"    Recommendations: {insights.get('recommendations')}")
else:
    print(f"    Error: {r.text}")

# 7. GET /api/surveys/stats (Verify stats increment)
print("\n[7] GET /api/surveys/stats")
r = requests.get(f"{BASE}/api/surveys/stats")
if r.ok:
    print(f"    Current Stats: {r.json()}")

# 8. DELETE survey
print("\n[8] DELETE /api/surveys/<id>")
r = requests.delete(f"{BASE}/api/surveys/{survey_id}")
print(f"    Status: {r.status_code} | {r.json().get('message')}")

print("\n" + "=" * 60)
print("Validation complete.")
print("=" * 60)
