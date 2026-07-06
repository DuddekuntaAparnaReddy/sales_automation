# -*- coding: utf-8 -*-
import sys, io, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("VALIDATION: Promotional Campaign Assistant")
print("=" * 60)

# 1. Stats
print("\n[1] GET /api/campaigns/stats")
r = requests.get(f"{BASE}/api/campaigns/stats")
print(f"    Status: {r.status_code}")
if r.ok:
    d = r.json()
    print(f"    Response: {d}")
    assert "total_campaigns" in d, "Missing total_campaigns key"
    print("    PASS")
else:
    print("    FAIL:", r.text)

# 2. Create Campaign with AI
print("\n[2] POST /campaign (with AI generation)")
payload = {
    "campaign_name":   "Gaming Laptop Festival Sale",
    "campaign_type":   "Festival Offer",
    "product_name":    "Gaming Laptop",
    "offer_details":   "20% off on all Gaming Laptops",
    "target_audience": "Students",
    "start_date":      "2026-07-01",
    "end_date":        "2026-07-31",
    "status":          "Active"
}
r = requests.post(f"{BASE}/campaign", json=payload)
print(f"    Status: {r.status_code}")
d = r.json()
if r.ok:
    print(f"    campaign_id: {d.get('campaign_id')}")
    ai = d.get('ai_content', {})
    print(f"    AI Title:   {ai.get('title','—')}")
    print(f"    AI Subject: {ai.get('subject','—')}")
    print(f"    AI CTA:     {ai.get('cta','—')}")
    print(f"    AI Body (first 80 chars): {str(ai.get('body',''))[:80]}...")
    created_id = d.get('campaign_id')
    print("    PASS")
else:
    print("    FAIL:", d)
    created_id = None

# 3. GET /campaigns (with status filter)
print("\n[3] GET /campaigns?status=Active")
r = requests.get(f"{BASE}/campaigns?status=Active")
print(f"    Status: {r.status_code}")
campaigns = r.json()
if isinstance(campaigns, list):
    print(f"    Count: {len(campaigns)}")
    if campaigns:
        c = campaigns[0]
        print(f"    First campaign: {c.get('campaign_name')} | product: {c.get('product_name')} | ai_title: {c.get('ai_title')}")
    print("    PASS")
else:
    print("    FAIL:", campaigns)

# 4. GET /campaign/<id>
if created_id:
    print(f"\n[4] GET /campaign/{created_id}")
    r = requests.get(f"{BASE}/campaign/{created_id}")
    print(f"    Status: {r.status_code}")
    if r.ok:
        c = r.json()
        print(f"    ai_subject: {c.get('ai_subject','—')}")
        print(f"    ai_cta:     {c.get('ai_cta','—')}")
        print(f"    status:     {c.get('status','—')}")
        print("    PASS")
    else:
        print("    FAIL:", r.text)

# 5. Search
print("\n[5] GET /campaigns?search=Gaming")
r = requests.get(f"{BASE}/campaigns?search=Gaming")
print(f"    Status: {r.status_code}")
if r.ok:
    results = r.json()
    print(f"    Results: {len(results)} campaigns found")
    print("    PASS")
else:
    print("    FAIL")

# 6. DELETE
if created_id:
    print(f"\n[6] DELETE /campaign/{created_id}")
    r = requests.delete(f"{BASE}/campaign/{created_id}")
    print(f"    Status: {r.status_code}")
    print(f"    Response: {r.json()}")
    print("    PASS" if r.ok else "    FAIL")

print("\n" + "=" * 60)
print("Validation complete.")
print("=" * 60)
