import os
import json
from groq import Groq

# Use the API key provided by the user as default fallback
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def generate_ai_response(prompt, system_prompt="You are a helpful assistant.", json_mode=False):
    """
    Exposes a unified interface to generate AI completions using Llama 3.1 on Groq.
    If the API key is invalid or rates are exceeded, falls back to a high-quality mock response.
    """
    if not GROQ_API_KEY:
        print("[GROQ CLIENT] No API Key found. Using mock fallback.")
        return generate_mock_fallback(prompt, json_mode)

    try:
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Using Groq Model
        model = "openai/gpt-oss-20b"
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1000
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            
        chat_completion = client.chat.completions.create(**kwargs)
        res_text = chat_completion.choices[0].message.content or ""
        if not res_text.strip():
            print("[GROQ CLIENT WARNING] Empty response from model. Utilizing mock fallback.")
            return generate_mock_fallback(prompt, json_mode)
        return res_text
    except Exception as e:
        print(f"[GROQ CLIENT ERROR] Connection failed: {e}. Utilizing mock fallback.")
        return generate_mock_fallback(prompt, json_mode)


def generate_ai_response_with_history(latest_message, conversation_history=None, system_prompt="You are a helpful assistant.", is_voice=False):
    """
    Sends the full conversation history to Groq so the model maintains context
    across multiple turns within the same chat session.

    conversation_history: list of dicts with keys 'role' ('user'|'assistant') and 'content' (str)
    latest_message: the newest user message (will be appended as the final 'user' turn)
    """
    if conversation_history is None:
        conversation_history = []

    if not GROQ_API_KEY:
        print("[GROQ CLIENT] No API Key found. Using mock fallback.")
        return generate_mock_fallback_with_history(latest_message, conversation_history, is_voice=is_voice)

    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Build messages array: system → history turns → latest user message
        messages = [{"role": "system", "content": system_prompt}]

        for turn in conversation_history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            # Normalise role names (frontend may send 'bot' instead of 'assistant')
            if role == "bot":
                role = "assistant"
            if content:
                messages.append({"role": role, "content": content})

        # Append the latest user message
        messages.append({"role": "user", "content": latest_message})

        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.4,
            max_tokens=300 if is_voice else 1200
        )
        res_text = chat_completion.choices[0].message.content or ""
        if not res_text.strip():
            print("[GROQ CLIENT WARNING] Empty response from model. Utilizing mock fallback.")
            return generate_mock_fallback_with_history(latest_message, conversation_history, is_voice=is_voice)
        return res_text

    except Exception as e:
        print(f"[GROQ CLIENT ERROR] History call failed: {e}. Using mock fallback.")
        return generate_mock_fallback_with_history(latest_message, conversation_history, is_voice=is_voice)


def generate_mock_fallback_with_history(latest_message, conversation_history, is_voice=False):
    """
    Context-aware mock fallback that inspects conversation history and latest message
    to return category-specific sales recommendations and qualifying questions.
    """
    # Only filter for user messages to avoid matching assistant's generic suggestion prompts
    user_turns = [t.get("content", "") for t in conversation_history if t.get("role") == "user"]
    all_text = " ".join(user_turns) + " " + latest_message
    all_lower = all_text.lower()

    # --- 1. Real Estate Category ---
    if "land" in all_lower or "agricultural" in all_lower or "property" in all_lower or "apartment" in all_lower or "house" in all_lower or "hyderabad" in all_lower:
        # Check if we have already collected location, size, purpose, and budget
        has_location = "hyderabad" in all_lower or "near" in all_lower
        has_size = "acre" in all_lower or "sq ft" in all_lower or "guntas" in all_lower
        has_purpose = "agricultural" in all_lower or "residential" in all_lower or "commercial" in all_lower
        has_budget = "lakh" in all_lower or "crore" in all_lower or "50" in all_lower or "₹" in all_lower

        if not (has_size and has_purpose and has_budget):
            if is_voice:
                return "I would be happy to assist with your land search near Hyderabad. Could you please tell me your preferred size, purpose, and budget?"
            # Ask qualifying questions based on missing fields
            questions = []
            if not has_size:
                questions.append("• What is your preferred land size requirement (e.g., 1 Acre, 2 Acres, or in Sq. Ft.)?")
            if not has_purpose:
                questions.append("• What is the primary purpose of the purchase (e.g., residential, commercial, or agricultural)?")
            if not has_budget:
                questions.append("• What is your budget range for this property?")
            
            return (
                "I would be happy to assist you with your land search near Hyderabad! To find the best listings, could you please provide:\n\n" +
                "\n".join(questions)
            )
        else:
            if is_voice:
                return "I found a 1.5-acre agricultural land in Shadnagar for 45 Lakhs, and a 1-acre farm land near Ibrahimpatnam for 48 Lakhs. Would you like to schedule a site visit?"
            # Recommend listings
            return (
                "Based on your requirement for land near Hyderabad, here are a few matched properties:\n\n"
                "1. **1.5 Acres Agricultural Land in Shadnagar** (₹45,000,000 / 45 Lakhs)\n"
                "   • Clear title, red soil, fully fenced. Perfect for organic farming.\n"
                "2. **1 Acre Farm Land near Ibrahimpatnam** (₹48,000,000 / 48 Lakhs)\n"
                "   • Good water source, close to the main highway.\n\n"
                "Would you like to schedule a site visit for either of these?"
            )

    # --- 2. Construction Materials / Hardware Category ---
    if "cement" in all_lower or "steel" in all_lower or "rod" in all_lower or "construction" in all_lower:
        has_quantity = "ton" in all_lower or "bag" in all_lower or "kg" in all_lower
        has_brand = "tata" in all_lower or "jsw" in all_lower or "ultratech" in all_lower
        has_budget = "budget" in all_lower or "₹" in all_lower or "lakh" in all_lower

        if not (has_quantity and has_brand):
            if is_voice:
                return "I can certainly help you source construction materials. Could you please share the required quantity and your preferred brand?"
            questions = []
            if not has_quantity:
                questions.append("• What is the required quantity (e.g., in tons for steel or bags for cement)?")
            if not has_brand:
                questions.append("• Do you have a preferred brand (e.g., TATA Tiscon, JSW NeoSteel for rods; UltraTech, Ambuja for cement)?")
            
            return (
                "I can certainly help you source high-quality construction materials! To give you an accurate quote, could you share:\n\n" +
                "\n".join(questions) + "\n• Also, what is the construction type (residential/commercial) and your approximate budget?"
            )
        else:
            if is_voice:
                return "I can offer TATA Tiscon steel rods for 68,000 rupees per ton, or JSW Neosteel for 66,500 rupees per ton. Shall I book an order for you?"
            return (
                "Here is our quote for construction steel/cement:\n\n"
                "1. **TATA Tiscon 550SD Steel Rods** — ₹68,000 per Ton\n"
                "   • High ductility, corrosion-resistant, certified quality.\n"
                "2. **JSW Neosteel Fe 550D** — ₹66,500 per Ton\n"
                "   • Excellent bendability and earthquake resistance.\n\n"
                "Shall I place a booking order or draft a proforma invoice for you?"
            )

    # --- 3. Vehicles Category ---
    if "car" in all_lower or "vehicle" in all_lower or "bike" in all_lower or "auto" in all_lower:
        # Detect budget
        has_budget = "lakh" in all_lower or "crore" in all_lower or "15" in all_lower or "₹" in all_lower
        has_fuel = "petrol" in all_lower or "diesel" in all_lower or "ev" in all_lower or "cng" in all_lower
        has_usage = "city" in all_lower or "highway" in all_lower or "family" in all_lower

        if not has_budget:
            return "What is your budget range for the vehicle, and do you prefer a hatchback, SUV, or sedan?"
        
        # If budget is provided but not fuel/usage, qualify first
        if not (has_fuel or has_usage):
            return "Understood. What will be your primary usage (e.g. daily city commute, weekend highway trips) and fuel preference (Petrol, Diesel, EV)?"

        # If we have budget + info, recommend
        if is_voice:
            return "I recommend the Tata Nexon starting at 8.5 Lakhs, or the Hyundai Creta starting at 11 Lakhs. Would you like to book a test drive?"
        return (
            "Based on your budget and preferences, here are the top vehicle recommendations:\n\n"
            "1. **Tata Nexon (Petrol/EV)** (₹8.5 Lakhs - ₹15 Lakhs)\n"
            "   • 5-star GNCAP safety rating, high ground clearance, modern features.\n"
            "2. **Hyundai Creta (Petrol/Diesel)** (₹11 Lakhs - ₹15 Lakhs for base/mid variants)\n"
            "   • Excellent cabin comfort, premium dashboard, high resale value.\n"
            "3. **Kia Sonet (Petrol)** (₹8 Lakhs - ₹14.5 Lakhs)\n"
            "   • Tech-loaded cabin, sporty styling, smooth automatic options.\n\n"
            "Would you like to book a test drive or compare details?"
        )

    # --- 4. Fashion Category ---
    if "fashion" in all_lower or "clothing" in all_lower or "shoes" in all_lower or "dress" in all_lower or "wear" in all_lower:
        has_size = "size" in all_lower or "medium" in all_lower or "large" in all_lower or "uk" in all_lower
        has_style = "formal" in all_lower or "casual" in all_lower or "party" in all_lower

        if not (has_size and has_style):
            return "I'd love to help you find the perfect outfit! Could you please share your size, style preference (formal, casual, ethnic), and the occasion you are dressing for?"
        else:
            if is_voice:
                return "I recommend our Classic Slim Fit Cotton Shirt for 1,899 rupees, or the Stretchable Comfort Chinos for 2,499 rupees. Shall I add these to your cart?"
            return (
                "Here are some handpicked options for you:\n\n"
                "1. **Classic Slim Fit Cotton Shirt** — ₹1,899\n"
                "   • Breathable premium fabric, ideal for formal and semi-formal wear.\n"
                "2. **Stretchable Comfort Chinos** — ₹2,499\n"
                "   • All-day stretch fabric, clean modern look.\n\n"
                "Shall I add these to your cart or look for alternative patterns?"
            )

    # --- 5. Electronics / Laptop Category (Fallback) ---
    # Detect budget (handling commas like 60,000 and 'k' notation like 60k)
    budget = None
    import re
    clean_text_for_budget = re.sub(r'(\d+),(\d+)', r'\1\2', all_text)
    k_matches = re.findall(r'(\d+)\s*k\b', clean_text_for_budget, re.IGNORECASE)
    if k_matches:
        budget = int(k_matches[-1]) * 1000
    else:
        budget_matches = re.findall(r'[\u20B9₹]?\s*(\d{4,7})', clean_text_for_budget)
        if budget_matches:
            budget = int(budget_matches[-1])

    is_gaming    = "gaming" in all_lower or "game" in all_lower
    is_office    = "office" in all_lower or "work" in all_lower or "business" in all_lower or "study" in all_lower
    is_video     = "video editing" in all_lower or "editing" in all_lower or "render" in all_lower
    is_laptop    = "laptop" in all_lower or "computer" in all_lower or "notebook" in all_lower or is_gaming or is_office or is_video

    if is_laptop:
        if is_gaming:
            b_val = budget or 60000
            if is_voice:
                return f"For gaming around {b_val} rupees, I recommend the Lenovo IdeaPad Gaming 3 or ASUS TUF Gaming F15. Would you like to check specifications?"
            return (
                f"Based on your gaming requirement and ₹{b_val:,} budget, here are my top picks:\n\n"
                "1. **Lenovo IdeaPad Gaming 3** (₹57,000)\n"
                "   • AMD Ryzen 5 6600H + NVIDIA RTX 3050 4GB • 120Hz IPS • 8GB RAM, 512GB SSD\n"
                "   ✅ Excellent budget gaming performance\n\n"
                "2. **ASUS TUF Gaming F15** (₹59,000)\n"
                "   • Intel Core i5 11th Gen + RTX 3050 • 144Hz IPS • 8GB RAM, 512GB SSD\n"
                "   ✅ Durable build quality with military-grade toughness\n\n"
                "3. **HP Victus 15** (₹58,000)\n"
                "   • AMD Ryzen 5 7535U + RTX 2050/3050 • 144Hz display • 8GB RAM, 512GB SSD\n"
                "   ✅ Sleek design suitable for work and gaming\n\n"
                "Would you like me to compare any of these in detail?"
            )
        if is_video:
            b_val = budget or 60000
            if is_voice:
                return f"For video editing around {b_val} rupees, I recommend the ASUS Vivobook Pro 15 or Lenovo IdeaPad Slim 5. Should I share specs?"
            return (
                f"For video editing around ₹{b_val:,}, here are recommended options:\n\n"
                "1. **ASUS Vivobook Pro 15** (₹58,000) — OLED display, Ryzen 5, 16GB RAM\n"
                "2. **Lenovo IdeaPad Slim 5** (₹62,000) — Intel i5 13th Gen, Iris Xe, 16GB RAM\n\n"
                "Both feature color-accurate displays for editing. Which brand do you prefer?"
            )
        if is_office:
            b_val = budget or 50000
            if is_voice:
                return f"For office work around {b_val} rupees, I recommend the Lenovo ThinkPad E14 or Dell Inspiron 14. Do you have a brand preference?"
            return (
                f"For office/work use around ₹{b_val:,}, here are top choices:\n\n"
                "1. **Lenovo ThinkPad E14** (₹55,000) — Best-in-class keyboard, rugged build\n"
                "2. **Dell Inspiron 14** (₹52,000) — Lightweight, solid battery life\n"
                "3. **HP 15s** (₹48,000) — Intel i5 12th Gen, 16GB RAM, 512GB SSD\n\n"
                "Would you like more details on any of these?"
            )
        if budget:
            if is_voice:
                return f"Under {budget} rupees, I recommend Lenovo IdeaPad Slim 3 or ASUS Vivobook 15. What will you primarily use it for?"
            return (
                f"Under ₹{budget:,}, here are great laptop choices:\n\n"
                "1. **Lenovo IdeaPad Slim 3** (₹54,000) — Intel i5 12th Gen, 16GB RAM\n"
                "2. **ASUS Vivobook 15** (₹52,000) — Ryzen 5, 16GB RAM, FHD Display\n\n"
                "What will you primarily use the laptop for? (Gaming, Office work, Video editing, Study)"
            )
        return "What will you primarily use the laptop for? (Gaming, Office work, Video editing, College/Study, General use)"

    if is_voice:
        return "Hello! I am your Salesbot voice assistant. I can help you find products or services across Real Estate, Vehicles, Electronics, Fashion, or Construction. What are you looking for today?"
    return (
        "Hello! I am your Salesbot AI Assistant. I can help you find products or services "
        "across any domain — including Real Estate, Vehicles, Construction Materials, Electronics, or Fashion. "
        "What are you looking for today?"
    )



def generate_mock_fallback(prompt, json_mode):
    """
    High-fidelity mock response generator that returns structurally correct responses
    matching the expected API format of each agent when live keys are unavailable.
    """
    prompt_lower = prompt.lower()
    
    if json_mode:
        # 1. Lead Qualification Extraction
        if "lead" in prompt_lower or "extract" in prompt_lower:
            return json.dumps({
                "product": "Gaming Laptop",
                "budget": 80000,
                "timeline": "This Week",
                "intent": "High"
            })
        
        # 2. Campaign Generator
        elif "campaign" in prompt_lower or "discount" in prompt_lower:
            return json.dumps({
                "title": "Laptop Mega Sale",
                "subject": "Get 20% Off - Limited Time Only!",
                "body": "Hi there!\n\nWe are launching our Laptop Mega Sale. Get up to 20% discount on all premium laptops this week. Don't miss out on these exclusive deals!",
                "cta": "Shop Now"
            })
            
        # 3. Event Invitation Generator
        elif "event" in prompt_lower or "invitation" in prompt_lower:
            return json.dumps({
                "subject": "You're Invited: Exclusive Summit!",
                "body": "Dear Guest,\n\nWe are pleased to invite you to our upcoming event. Learn how automation can elevate your business workflows. We look forward to seeing you there."
            })
            
        # 4. Customer Re-engagement
        elif "re-engage" in prompt_lower or "miss you" in prompt_lower or "reengagement" in prompt_lower:
            return json.dumps({
                "subject": "We Miss You at Salesbot!",
                "body": "Hi Customer,\n\nIt's been a while since your last interaction. We've introduced brand new AI automation features that we think you'll love. Click here to check them out!"
            })
            
        # 5. Feedback Analysis
        elif "feedback" in prompt_lower or "survey" in prompt_lower:
            if "excellent" in prompt_lower or "slow" in prompt_lower:
                return json.dumps({
                    "sentiment": "Positive",
                    "summary": "Customer liked product quality but disliked delivery speed.",
                    "strengths": ["Product Quality"],
                    "weaknesses": ["Delivery Speed"]
                })
            return json.dumps({
                "sentiment": "Neutral",
                "summary": "General customer feedback received.",
                "strengths": ["Customer Service"],
                "weaknesses": []
            })
            
        # 6. Market Insights
        elif "insights" in prompt_lower or "aggregate" in prompt_lower:
            return json.dumps({
                "top_interests": ["Gaming Laptop", "Business Ultrawide"],
                "common_issues": ["Delivery Delay", "High Shipping Cost"],
                "recommendations": ["Improve logistics partners", "Offer free shipping above limit"]
            })
            
        # 7. Email Generator
        elif "email" in prompt_lower:
            return json.dumps({
                "subject": "System Notification",
                "body": "This is a generated email layout based on your request specifications. Thank you."
            })
            
        # Default JSON
        return json.dumps({
            "message": "Success",
            "details": "Mock fallback response"
        })
    else:
        # Conversational Response for Telesales Assistant
        if "laptop under" in prompt_lower:
            return "I would highly recommend the Lenovo IdeaPad Slim 3 or Asus Vivobook 15. Both offer great AMD/Intel processors, 16GB RAM, and 512GB SSD storage for under ₹60,000, making them perfect for multitasking and general use!"
        elif "gaming" in prompt_lower:
            return "For gaming, the Asus ROG Strix or HP Victus series are excellent choices. They feature high refresh rate screens, NVIDIA RTX GPUs, and great cooling systems to handle long gaming sessions smoothly."
        
        return "Hello! I am your AI Telesales Assistant. I can help you find products, compare options, understand discounts, and make buying decisions. What are you looking to buy today?"
