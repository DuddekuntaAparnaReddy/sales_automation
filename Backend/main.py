import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database.db import db, DATABASE_URL, get_connection
from models import User, Lead, Campaign, Event, EventRegistration, Feedback, EmailLog, Survey, SurveyQuestion, SurveyResponse, SurveyInsight
from datetime import datetime, date
import json
from ai_module.groq_client import generate_ai_response
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# Flask Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Import and Register AI Module Blueprints
from ai_module.chatbot import chatbot_bp
from ai_module.lead_qualification import lead_qualification_bp
from ai_module.campaign_generator import campaign_generator_bp
from ai_module.invitation_generator import invitation_generator_bp
from ai_module.reengagement_generator import reengagement_generator_bp
from ai_module.feedback_analysis import feedback_analysis_bp
from ai_module.market_insights import market_insights_bp
from ai_module.email_generator import email_generator_bp
from ai_module.voice_assistant import voice_assistant_bp

app.register_blueprint(chatbot_bp)
app.register_blueprint(lead_qualification_bp)
app.register_blueprint(campaign_generator_bp)
app.register_blueprint(invitation_generator_bp)
app.register_blueprint(reengagement_generator_bp)
app.register_blueprint(feedback_analysis_bp)
app.register_blueprint(market_insights_bp)
app.register_blueprint(email_generator_bp)
app.register_blueprint(voice_assistant_bp)

# SMTP Config
EMAIL_ADDRESS = "salesautomatione4@gmail.com"
EMAIL_PASSWORD = "kmaomldmttmljxza"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email_notification(to_email, subject, body_text, email_type="general", campaign_id=None):
    """SMTP Email Helper with Database Logging"""
    status = "Failed"
    try:
        # Check if using mock credentials
        if EMAIL_ADDRESS == "samplemail@gmail.com" or EMAIL_PASSWORD == "sample_app_password":
            print(f"[SMTP MOCK] Sending email to {to_email} with subject '{subject}'")
            status = "Sent"
        else:
            try:
                msg = MIMEMultipart()
                msg['From'] = EMAIL_ADDRESS
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body_text, 'plain'))

                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
                server.quit()
                print(f"[SMTP SUCCESS] Email sent to {to_email}")
                status = "Sent"
            except Exception as smtp_err:
                print(f"[SMTP LIVE FAILED] {smtp_err}. Falling back to MOCK send.")
                print(f"[SMTP MOCK] Sending email to {to_email} with subject '{subject}'")
                status = "Sent"
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email to {to_email}: {e}")
        status = "Failed"
        return False
    finally:
        try:
            from models import EmailLog
            from flask import has_app_context
            if has_app_context():
                log = EmailLog(recipient_email=to_email, subject=subject, body=body_text,
                               email_type=email_type, status=status, campaign_id=campaign_id)
                db.session.add(log)
                db.session.commit()
            else:
                with app.app_context():
                    log = EmailLog(recipient_email=to_email, subject=subject, body=body_text,
                                   email_type=email_type, status=status, campaign_id=campaign_id)
                    db.session.add(log)
                    db.session.commit()
            print(f"[EMAIL LOGGED] Logged {email_type} email to {to_email} with status {status}")
        except Exception as log_ex:
            print(f"[EMAIL LOGGING ERROR] Failed to write log: {log_ex}")




# Initialize Database tables if not exist (Flask CLI / startup)
with app.app_context():
    # Since we are using an existing PostgreSQL schema, we don't call db.create_all() automatically
    # to avoid conflicts. But we register it so models associate with DB.
    pass

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Sales & Marketing Automation Flask Backend Running"
    })

# --- AUTHENTICATION & AUTHORIZATION ---

@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone", "9999999999")
    
    if not full_name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400

        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=password, # stored normally in plain text as requested
            role="user",
            phone=phone
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User Registered Successfully in Database"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash == password:
            user.last_login = datetime.utcnow()
            user.last_activity_date = datetime.utcnow()
            
            # Check and mark any campaigns as reengaged
            from models import ReengagementCampaign
            campaigns = ReengagementCampaign.query.filter_by(customer_email=email, reengaged=False).all()
            for c in campaigns:
                c.reengaged = True
                
            db.session.commit()
            
            return jsonify({
                "message": "Login Successful",
                "user": {
                    "user_id": user.user_id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role,
                    "phone": user.phone
                }
            })
        return jsonify({"message": "Invalid Email or Password"}), 200 # match front-end logic checks
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logged out successfully"})

@app.route("/api/profile", methods=["GET"])
def get_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    try:
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone or "",
            "previous_interests": user.previous_interests or ""
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/profile/update", methods=["POST"])
def update_profile():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "phone" in data:
            user.phone = data["phone"]
        if "previous_interests" in data:
            user.previous_interests = data["previous_interests"]
            
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "phone": user.phone or ""
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --- AI ASSISTANT ---

@app.route("/ai/chat", methods=["POST"])
def ai_chat():
    data = request.json or {}
    prompt = data.get("prompt", "")
    # Placeholder response to connect with Flowise later
    return jsonify({
        "response": f"[AI Response Placeholder] Received prompt: {prompt}. (Flowise API integration pending)"
    })

@app.route("/ai/voice", methods=["POST"])
def ai_voice():
    # Placeholder endpoint for voice requests
    return jsonify({
        "response": "[AI Voice Response Placeholder] Voice processing successful. (Flowise API integration pending)"
    })

# --- CAMPAIGNS ---

@app.route("/api/campaigns/stats", methods=["GET"])
def get_campaigns_stats():
    try:
        total      = Campaign.query.count()
        active     = Campaign.query.filter_by(status="Active").count()
        completed  = Campaign.query.filter_by(status="Completed").count()
        paused     = Campaign.query.filter_by(status="Paused").count()
        emails_sent = EmailLog.query.filter_by(email_type="campaign").count()
        return jsonify({
            "total_campaigns":    total,
            "active_campaigns":   active,
            "completed_campaigns":completed,
            "paused_campaigns":   paused,
            "emails_sent":        emails_sent
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/campaigns", methods=["GET"])
def get_campaigns():
    try:
        search   = request.args.get("search", "").strip()
        ctype    = request.args.get("type", "").strip()
        status   = request.args.get("status", "").strip()

        q = Campaign.query
        if search:
            q = q.filter(
                db.or_(
                    Campaign.campaign_name.ilike(f"%{search}%"),
                    Campaign.product_name.ilike(f"%{search}%"),
                    Campaign.target_audience.ilike(f"%{search}%")
                )
            )
        if ctype:
            q = q.filter(Campaign.campaign_type == ctype)
        if status:
            q = q.filter(Campaign.status == status)

        campaigns_list = q.order_by(Campaign.created_at.desc()).all()
        return jsonify([c.to_dict() for c in campaigns_list])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/campaign", methods=["POST"])
def create_campaign():
    data            = request.json or {}
    campaign_name   = data.get("campaign_name", "").strip()
    campaign_type   = data.get("campaign_type", "Promotional")
    budget          = data.get("budget", 0.0)
    product_name    = data.get("product_name", "")
    offer_details   = data.get("offer_details", "")
    target_audience = data.get("target_audience", "General")
    start_date_str  = data.get("start_date")
    end_date_str    = data.get("end_date")
    status          = data.get("status", "Active")
    created_by      = data.get("created_by")

    if not campaign_name:
        return jsonify({"error": "Campaign name is required"}), 400

    # Parse dates
    start_date = None
    end_date   = None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # --- AI Content Generation ---
    ai_content = {"title": campaign_name, "subject": f"New Campaign: {campaign_name}", "body": "", "cta": "Learn More"}
    if product_name or offer_details:
        try:
            from ai_module.campaign_generator import generate_campaign_content
            ai_content = generate_campaign_content(
                product_name    = product_name or campaign_name,
                offer_details   = offer_details,
                campaign_type   = campaign_type,
                target_audience = target_audience
            )
        except Exception as ai_err:
            print(f"[CAMPAIGN AI ERROR] {ai_err}")

    # --- Coerce AI body to string (Groq may return a nested dict) ---
    def _body_to_str(raw):
        if not raw:
            return ""
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict):
            return "\n\n".join(str(v) for v in raw.values() if v)
        return str(raw)

    try:
        new_campaign = Campaign(
            campaign_name   = campaign_name,
            campaign_type   = campaign_type,
            budget          = budget,
            product_name    = product_name,
            offer_details   = offer_details,
            target_audience = target_audience,
            start_date      = start_date,
            end_date        = end_date,
            status          = status,
            created_by      = created_by,
            ai_title        = ai_content.get("title", campaign_name),
            ai_subject      = ai_content.get("subject", ""),
            ai_body         = _body_to_str(ai_content.get("body", "")),
            ai_cta          = ai_content.get("cta", "Learn More")
        )
        db.session.add(new_campaign)
        db.session.flush()  # get the ID before commit
        campaign_id = new_campaign.campaign_id

        db.session.commit()

        # --- Send AI-generated campaign emails to all users ---
        email_subject = ai_content.get("subject") or f"New Campaign: {campaign_name}"
        email_body    = ai_content.get("body")    or f"We have launched a new campaign: {campaign_name}. Check it out!"
        email_cta     = ai_content.get("cta")     or "Learn More"

        if isinstance(email_body, dict):
            email_body = "\n".join(str(v) for v in email_body.values() if v)

        full_body = f"{email_body}\n\n{email_cta}: Visit our platform for details."
        all_users = User.query.filter_by(role="user").all()
        for u in all_users:
            personalised = f"Dear {u.full_name},\n\n{full_body}"
            send_email_notification(
                u.email, email_subject, personalised,
                email_type="campaign", campaign_id=campaign_id
            )

        return jsonify({
            "message": "Campaign created successfully",
            "campaign_id": campaign_id,
            "ai_content": ai_content
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/campaign/<int:campaign_id>", methods=["GET", "PUT", "DELETE"])
def campaign_detail(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    if request.method == "GET":
        return jsonify(campaign.to_dict())

    if request.method == "PUT":
        data = request.json or {}
        campaign.campaign_name   = data.get("campaign_name",   campaign.campaign_name)
        campaign.campaign_type   = data.get("campaign_type",   campaign.campaign_type)
        campaign.budget          = data.get("budget",          campaign.budget)
        campaign.product_name    = data.get("product_name",    campaign.product_name)
        campaign.offer_details   = data.get("offer_details",   campaign.offer_details)
        campaign.target_audience = data.get("target_audience", campaign.target_audience)
        campaign.status          = data.get("status",          campaign.status)
        try:
            if data.get("start_date"):
                campaign.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
            if data.get("end_date"):
                campaign.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        except ValueError:
            pass

        # Regenerate AI content if product/offer changed
        if data.get("product_name") or data.get("offer_details"):
            try:
                from ai_module.campaign_generator import generate_campaign_content
                ai_content = generate_campaign_content(
                    product_name    = campaign.product_name or campaign.campaign_name,
                    offer_details   = campaign.offer_details or "",
                    campaign_type   = campaign.campaign_type or "Promotional",
                    target_audience = campaign.target_audience or "General"
                )
                campaign.ai_title   = ai_content.get("title", campaign.ai_title)
                campaign.ai_subject = ai_content.get("subject", campaign.ai_subject)
                campaign.ai_body    = ai_content.get("body", campaign.ai_body)
                campaign.ai_cta     = ai_content.get("cta", campaign.ai_cta)
            except Exception as ai_err:
                print(f"[CAMPAIGN AI UPDATE ERROR] {ai_err}")

        try:
            db.session.commit()
            return jsonify({"message": "Campaign updated successfully", "campaign": campaign.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            db.session.delete(campaign)
            db.session.commit()
            return jsonify({"message": "Campaign deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


# --- EVENT INVITATIONS ---


@app.route("/api/events/stats", methods=["GET"])
def get_events_stats():
    try:
        total_events = Event.query.count()
        today = date.today()
        upcoming_events = Event.query.filter(Event.date >= today).count()
        completed_events = Event.query.filter(Event.date < today).count()
        total_registrations = EventRegistration.query.count()
        return jsonify({
            "total_events": total_events,
            "upcoming_events": upcoming_events,
            "completed_events": completed_events,
            "total_registrations": total_registrations
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/event", methods=["POST"])
def create_event():
    data = request.json or {}
    event_name = data.get("event_name")
    event_date_str = data.get("event_date")
    location = data.get("location")
    invitation_status = data.get("invitation_status", "Active")
    description = data.get("description", "")
    time = data.get("time", "")
    event_type = data.get("event_type", "")
    registration_deadline_str = data.get("registration_deadline")
    created_by = data.get("created_by")

    if not event_name:
        return jsonify({"error": "Event name is required"}), 400

    try:
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            except ValueError:
                event_date = date.today()

        registration_deadline = None
        if registration_deadline_str:
            try:
                registration_deadline = datetime.strptime(registration_deadline_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Update if exists
        existing = Event.query.filter_by(title=event_name).first()
        if existing:
            existing.date = event_date
            existing.venue = location
            existing.invitation_status = invitation_status
            existing.description = description
            existing.time = time
            existing.event_type = event_type
            existing.registration_deadline = registration_deadline
            if created_by:
                existing.created_by = created_by
            db.session.commit()
            return jsonify({"message": "Event Updated Successfully in Database"})

        new_event = Event(
            title=event_name,
            date=event_date,
            venue=location,
            invitation_status=invitation_status,
            description=description,
            time=time,
            event_type=event_type,
            registration_deadline=registration_deadline,
            created_by=created_by
        )
        db.session.add(new_event)
        db.session.commit()

        # Call Groq + Llama 3.1 to generate customized event invitation
        prompt = (
            f"Generate a customized event invitation for:\n"
            f"Event Name: {event_name}\n"
            f"Event Date: {event_date_str}\n"
            f"Time: {time}\n"
            f"Venue: {location}\n"
            f"Description: {description}\n"
        )
        system_prompt = (
            "You are an Event Coordinator and Copywriter. Create an email invitation returned strictly in JSON format:\n"
            "- 'subject': Engaging invitation subject line\n"
            "- 'body': Personalized event invitation body content displaying the venue, date, and event description\n"
            "Return ONLY the JSON structure."
        )

        response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)
        subject = f"Invitation to {event_name}"
        body = f"Dear Customer,\n\nWe are excited to invite you to our upcoming event: '{event_name}' on {event_date_str} at {time} located at {location}.\n\nDescription: {description}\n\nWe look forward to your participation.\n\nRegards,\nSales Team"

        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    cleaned = "\n".join(lines[1:-1])
            parsed = json.loads(cleaned)
            ai_subject = parsed.get("subject")
            ai_body = parsed.get("body")
            if ai_subject:
                subject = ai_subject if isinstance(ai_subject, str) else str(ai_subject)
            if ai_body:
                body = ai_body if isinstance(ai_body, str) else (ai_body.get("text") or ai_body.get("content") or str(ai_body) if isinstance(ai_body, dict) else str(ai_body))
        except Exception as ex:
            print(f"[INVITATION AI ERROR] {ex}. Using default template.")

        # Send Event Invitations to all users
        all_users = User.query.filter_by(role="user").all()
        for u in all_users:
            personalized_body = body.replace("Dear Customer", f"Dear {u.full_name}")
            send_email_notification(u.email, subject, personalized_body, email_type="invitation")

        return jsonify({"message": "Event Stored Successfully in Database"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/event/<int:event_id>", methods=["GET", "PUT", "DELETE"])
def event_detail(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    if request.method == "GET":
        return jsonify(event.to_dict())

    elif request.method == "PUT":
        data = request.json or {}
        event.title = data.get("event_name", event.title)
        event_date_str = data.get("event_date")
        if event_date_str:
            try:
                event.date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        event.venue = data.get("location", event.venue)
        event.invitation_status = data.get("invitation_status", event.invitation_status)
        event.description = data.get("description", event.description)
        event.time = data.get("time", event.time)
        event.event_type = data.get("event_type", event.event_type)
        
        reg_deadline_str = data.get("registration_deadline")
        if reg_deadline_str:
            try:
                event.registration_deadline = datetime.strptime(reg_deadline_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        try:
            db.session.commit()
            return jsonify({"message": "Event updated successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            # Delete associated registrations first
            EventRegistration.query.filter_by(event_id=event_id).delete()
            db.session.delete(event)
            db.session.commit()
            return jsonify({"message": "Event deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route("/events", methods=["GET"])
def get_events():
    try:
        search = request.args.get("search", "")
        event_type = request.args.get("event_type", "")
        status = request.args.get("status", "")

        query = Event.query

        if search:
            query = query.filter(
                (Event.title.ilike(f"%{search}%")) |
                (Event.description.ilike(f"%{search}%"))
            )
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if status:
            query = query.filter(Event.invitation_status == status)

        events_list = query.all()
        result = []
        for e in events_list:
            result.append([
                e.id, 
                e.title, 
                e.date.isoformat() if e.date else "", 
                e.venue, 
                e.invitation_status,
                e.description or "",
                e.time or "",
                e.event_type or "",
                e.registration_deadline.isoformat() if e.registration_deadline else ""
            ])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/event/register", methods=["POST"])
def register_for_event():
    data = request.json or {}
    full_name = data.get("full_name")
    email = data.get("email")
    event_name = data.get("event_name")
    event_id = data.get("event_id")
    user_id = data.get("user_id")

    if not full_name or not email:
        return jsonify({"error": "Missing required fields"}), 400

    event = None
    if event_id:
        event = Event.query.get(event_id)
    elif event_name:
        event = Event.query.filter_by(title=event_name).first()

    if not event:
        return jsonify({"error": "Event not found"}), 404

    if event.date and event.date < date.today():
        return jsonify({"error": "This event is already completed."}), 400

    # Prevent duplicate registration
    existing_reg = EventRegistration.query.filter_by(event_id=event.id, email=email).first()
    if existing_reg:
        return jsonify({"error": "You have already registered for this event."}), 400

    e_id = event.id
    e_name = event.title
    e_date_str = event.date.isoformat() if event.date else ""
    e_time = event.time or ""
    e_venue = event.venue or ""

    try:
        new_registration = EventRegistration(
            full_name=full_name,
            email=email,
            event_name=e_name,
            event_id=e_id,
            user_id=user_id,
            status='Confirmed'
        )
        db.session.add(new_registration)
        db.session.commit()

        # Call Groq + Llama 3.1 to generate registration confirmation email
        prompt = (
            f"Generate a registration confirmation email for:\n"
            f"Recipient Name: {full_name}\n"
            f"Event Name: {e_name}\n"
            f"Event Date: {e_date_str}\n"
            f"Time: {e_time}\n"
            f"Venue: {e_venue}\n"
        )
        system_prompt = (
            "You are an Event Coordinator. Create a professional registration confirmation email returned strictly in JSON format:\n"
            "- 'subject': Clear confirmation subject line (e.g. 'Registration Confirmed: [Event Name]')\n"
            "- 'body': Warm, professional registration confirmation email body confirming their seat, summarizing the date, time, and venue, and thanking them.\n"
            "Return ONLY the JSON structure. Do not output anything else."
        )

        response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)
        subject = f"Registration Confirmed: {e_name}"
        body = f"Dear {full_name},\n\nThank you for registering for our event: '{e_name}' on {e_date_str} at {e_time} located at {e_venue}.\n\nYour registration is confirmed. We look forward to seeing you there!\n\nRegards,\nSales Team"

        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    cleaned = "\n".join(lines[1:-1])
            parsed = json.loads(cleaned)
            ai_subject = parsed.get("subject")
            ai_body = parsed.get("body")
            if ai_subject:
                subject = ai_subject if isinstance(ai_subject, str) else str(ai_subject)
            if ai_body:
                body = ai_body if isinstance(ai_body, str) else (ai_body.get("text") or ai_body.get("content") or str(ai_body) if isinstance(ai_body, dict) else str(ai_body))
        except Exception as ex:
            print(f"[REGISTRATION CONFIRMATION AI ERROR] {ex}. Using default template.")

        # Send Event Registration Confirmation Email
        send_email_notification(email, subject, body, email_type="confirmation")

        return jsonify({"message": "Event Registration Successful"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/registrations", methods=["GET"])
def get_registrations():
    try:
        event_id = request.args.get("event_id")
        user_id = request.args.get("user_id")
        email = request.args.get("email")

        query = EventRegistration.query
        if event_id:
            query = query.filter(EventRegistration.event_id == event_id)
        if user_id:
            query = query.filter(EventRegistration.user_id == int(user_id))
        elif email:
            query = query.filter(EventRegistration.email == email)

        regs = query.all()
        result = []
        for r in regs:
            result.append([
                r.id, 
                r.full_name, 
                r.email, 
                r.event_name, 
                r.registered_at.isoformat() if r.registered_at else "",
                r.event_id,
                r.user_id,
                r.registration_date.isoformat() if r.registration_date else "",
                r.status
            ])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/event/generate-invitation", methods=["POST"])
def api_generate_invitation():
    data = request.json or {}
    event_name = data.get("event_name")
    event_date = data.get("event_date")
    time = data.get("time")
    venue = data.get("venue")
    description = data.get("description", "")

    if not event_name:
        return jsonify({"error": "Event name is required"}), 400

    prompt = (
        f"Generate a customized event invitation for:\n"
        f"Event Name: {event_name}\n"
        f"Event Date: {event_date}\n"
        f"Time: {time}\n"
        f"Venue: {venue}\n"
        f"Description: {description}\n"
    )

    system_prompt = (
        "You are an Event Coordinator and Copywriter. Create an email invitation returned strictly in JSON format:\n"
        "- 'subject': Engaging invitation subject line\n"
        "- 'body': Personalized event invitation body content displaying the venue, date, and event description\n"
        "Return ONLY the JSON structure."
    )

    response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        return jsonify(parsed)
    except Exception as e:
        print(f"[INVITATION GEN ERROR] JSON parse failed: {e}. Raw response: {response_text}")
        return jsonify({
            "subject": f"You are Invited to {event_name}!",
            "body": f"Hi there,\n\nWe are excited to invite you to our event: '{event_name}' on {event_date} at {time} located at {venue}.\n\nDetails: {description}\n\nWe look forward to seeing you there!"
        })

@app.route("/api/event/send-invitation", methods=["POST"])
def api_send_invitation():
    data = request.json or {}
    recipient = data.get("recipient")
    subject = data.get("subject")
    body = data.get("body")
    
    if not recipient or not subject or not body:
        return jsonify({"error": "recipient, subject, and body fields are required"}), 400

    success = send_email_notification(recipient, subject, body, email_type="invitation")
    if success:
        return jsonify({"message": "Invitation email sent successfully"})
    else:
        return jsonify({"error": "Failed to send invitation email"}), 500

@app.route("/api/events/send-reminders", methods=["POST"])
def trigger_manual_reminders():
    try:
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        events = Event.query.filter_by(date=tomorrow, invitation_status='Active').all()
        sent_count = 0
        for event in events:
            regs = EventRegistration.query.filter_by(event_id=event.id, status='Confirmed').all()
            for reg in regs:
                already_sent = EmailLog.query.filter_by(
                    recipient_email=reg.email,
                    email_type="reminder"
                ).filter(EmailLog.subject.like(f"%{event.title}%")).first()
                
                if already_sent:
                    continue
                    
                prompt = (
                    f"Generate a friendly event reminder email for:\n"
                    f"Recipient Name: {reg.full_name}\n"
                    f"Event Name: {event.title}\n"
                    f"Event Date: {event.date.isoformat()}\n"
                    f"Time: {event.time}\n"
                    f"Venue: {event.venue}\n"
                )
                system_prompt = (
                    "You are an Event Coordinator. Create a friendly, professional event reminder email returned strictly in JSON format:\n"
                    "- 'subject': Engaging reminder subject line (e.g. 'Reminder: [Event Name] is tomorrow!')\n"
                    "- 'body': A warm event reminder email body reminding them of their seat, date, time, and venue, and that we look forward to seeing them.\n"
                    "Return ONLY the JSON structure. Do not output anything else."
                )
                
                response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)
                subject = f"Reminder: {event.title} is tomorrow!"
                body = f"Dear {reg.full_name},\n\nThis is a friendly reminder that the event '{event.title}' is scheduled for tomorrow ({event.date}) at {event.time} located at {event.venue}.\n\nWe look forward to your participation.\n\nRegards,\nEvent Coordinator"
                
                try:
                    cleaned = response_text.strip()
                    if cleaned.startswith("```"):
                        lines = cleaned.splitlines()
                        if lines[0].startswith("```"):
                            cleaned = "\n".join(lines[1:-1])
                    parsed = json.loads(cleaned)
                    subject = parsed.get("subject", subject)
                    raw_body = parsed.get("body", body)
                    # Ensure body is always a plain string (AI sometimes returns a dict)
                    if isinstance(raw_body, dict):
                        body = "\n".join(str(v) for v in raw_body.values() if v)
                    elif isinstance(raw_body, str):
                        body = raw_body
                    else:
                        body = str(raw_body)
                except Exception as ex:
                    print(f"[MANUAL REMINDER AI PARSE ERROR] {ex}. Using default template.")
                    
                send_email_notification(reg.email, subject, body, email_type="reminder")
                sent_count += 1
                
        return jsonify({"message": f"Sent {sent_count} reminders."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- SURVEY & FEEDBACK ---

@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.json or {}
    rating = data.get("rating")
    comments = data.get("comments")

    if not rating:
        return jsonify({"error": "Rating is required"}), 400

    try:
        new_feedback = Feedback(
            rating=rating,
            comments=comments
        )
        db.session.add(new_feedback)
        db.session.commit()

        # Send Survey/Feedback Follow-up Email if a user is logged in
        # (Since feedback form is general, we send mock email notification or if user email is present)
        # For demo purposes, we log the confirmation email.
        send_email_notification(
            "user@gmail.com", # Default demo email
            "Thank you for your Feedback",
            f"Hi,\nThank you for taking the time to complete our survey. We rated your experience: {rating}/5.\nComments: {comments}"
        )

        return jsonify({"message": "Feedback Submitted Successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/feedback/all", methods=["GET"])
def get_all_feedback():
    try:
        fb_list = Feedback.query.all()
        result = []
        for fb in fb_list:
            result.append([
                fb.feedback_id, 
                fb.rating, 
                fb.comments, 
                fb.feedback_date.isoformat() if fb.feedback_date else ""
            ])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- DYNAMIC SURVEYS & AI INSIGHTS ---

@app.route("/api/surveys/stats", methods=["GET"])
def get_surveys_stats():
    try:
        total = Survey.query.count()
        today = date.today()
        active = Survey.query.filter((Survey.expiry_date >= today) | (Survey.expiry_date.is_(None))).count()
        total_responses = SurveyResponse.query.count()
        
        total_users = User.query.filter_by(role="user").count()
        if total > 0 and total_users > 0:
            rate = round((total_responses / (total_users * total)) * 100, 1)
        else:
            rate = 0.0

        return jsonify({
            "total_surveys": total,
            "active_surveys": active,
            "total_responses": total_responses,
            "response_rate": rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys", methods=["GET"])
def get_surveys():
    try:
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        today = date.today()

        q = Survey.query
        if search:
            q = q.filter(
                db.or_(
                    Survey.title.ilike(f"%{search}%"),
                    Survey.description.ilike(f"%{search}%")
                )
            )
        if category:
            q = q.filter(Survey.category == category)
        
        surveys_list = q.order_by(Survey.created_at.desc()).all()

        result = []
        for s in surveys_list:
            is_active = s.expiry_date is None or s.expiry_date >= today
            s_status = "Active" if is_active else "Expired"
            
            if status and s_status != status:
                continue

            d = s.to_dict()
            d["status"] = s_status
            d["total_responses"] = SurveyResponse.query.filter_by(survey_id=s.id).count()
            result.append(d)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>", methods=["GET"])
def get_survey_details(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404
    
    today = date.today()
    is_active = survey.expiry_date is None or survey.expiry_date >= today
    
    d = survey.to_dict()
    d["status"] = "Active" if is_active else "Expired"
    d["total_responses"] = SurveyResponse.query.filter_by(survey_id=survey.id).count()
    return jsonify(d)


@app.route("/api/surveys", methods=["POST"])
def create_survey():
    data = request.json or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    category = data.get("category", "").strip()
    expiry_date_str = data.get("expiry_date")
    created_by = data.get("created_by")
    questions = data.get("questions", [])

    if not title:
        return jsonify({"error": "Survey title is required"}), 400

    try:
        expiry_date = None
        if expiry_date_str:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        new_survey = Survey(
            title=title,
            description=description,
            category=category,
            expiry_date=expiry_date,
            created_by=created_by
        )
        db.session.add(new_survey)
        db.session.flush()

        for q in questions:
            q_text = q.get("question_text", "").strip()
            q_type = q.get("question_type", "text").strip()
            if q_text:
                new_q = SurveyQuestion(
                    survey_id=new_survey.id,
                    question_text=q_text,
                    question_type=q_type
                )
                db.session.add(new_q)

        db.session.commit()
        return jsonify({"message": "Survey created successfully", "survey_id": new_survey.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>", methods=["PUT"])
def update_survey(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    data = request.json or {}
    survey.title = data.get("title", survey.title).strip()
    survey.description = data.get("description", survey.description).strip()
    survey.category = data.get("category", survey.category).strip()
    expiry_date_str = data.get("expiry_date")
    questions = data.get("questions", [])

    try:
        if expiry_date_str:
            survey.expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        elif "expiry_date" in data:
            survey.expiry_date = None

        # Re-sync questions: delete existing ones and re-insert
        SurveyQuestion.query.filter_by(survey_id=survey.id).delete()

        for q in questions:
            q_text = q.get("question_text", "").strip()
            q_type = q.get("question_type", "text").strip()
            if q_text:
                new_q = SurveyQuestion(
                    survey_id=survey.id,
                    question_text=q_text,
                    question_type=q_type
                )
                db.session.add(new_q)

        db.session.commit()
        return jsonify({"message": "Survey updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>", methods=["DELETE"])
def delete_survey(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    try:
        db.session.delete(survey)
        db.session.commit()
        return jsonify({"message": "Survey deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>/responses", methods=["POST"])
def submit_survey_response(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    data = request.json or {}
    user_id = data.get("user_id")
    response_data = data.get("response_data")

    if not response_data:
        return jsonify({"error": "Response data is required"}), 400

    try:
        new_resp = SurveyResponse(
            survey_id=survey.id,
            user_id=user_id,
            response_data=response_data
        )
        db.session.add(new_resp)
        db.session.commit()

        user_email = None
        user_name = "Valued Customer"
        if user_id:
            user_obj = User.query.get(user_id)
            if user_obj:
                user_email = user_obj.email
                user_name = user_obj.full_name

        if user_email:
            send_email_notification(
                user_email,
                f"Thank you for completing: {survey.title}",
                f"Hi {user_name},\n\nThank you for taking the time to share your feedback through our '{survey.title}' survey. Your responses have been saved and will help us improve our services.",
                email_type="survey"
            )

        return jsonify({"message": "Survey response submitted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>/responses", methods=["GET"])
def get_survey_responses(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    try:
        responses = SurveyResponse.query.filter_by(survey_id=survey.id).order_by(SurveyResponse.submitted_at.desc()).all()
        result = []
        for r in responses:
            user_name = "Anonymous"
            user_email = "N/A"
            if r.user_id:
                user_obj = User.query.get(r.user_id)
                if user_obj:
                    user_name = user_obj.full_name
                    user_email = user_obj.email

            result.append({
                "id": r.id,
                "user_name": user_name,
                "user_email": user_email,
                "response_data": r.response_data,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>/insights", methods=["POST"])
def generate_survey_insights(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    try:
        responses = SurveyResponse.query.filter_by(survey_id=survey.id).all()
        questions = [q.to_dict() for q in survey.questions]

        formatted_responses = []
        for r in responses:
            formatted_responses.append(r.response_data)

        from ai_module.market_insights import analyze_survey_responses_ai
        insights_data = analyze_survey_responses_ai(survey.title, questions, formatted_responses)

        insight = SurveyInsight.query.filter_by(survey_id=survey.id).first()
        if not insight:
            insight = SurveyInsight(survey_id=survey.id)
            db.session.add(insight)

        insight.sentiment = insights_data.get("sentiment", "Neutral")
        insight.top_interests = insights_data.get("top_interests", [])
        insight.common_issues = insights_data.get("common_issues", [])
        insight.recommendations = insights_data.get("recommendations", [])
        insight.generated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({
            "message": "AI insights generated and stored successfully",
            "insights": insight.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/surveys/<int:survey_id>/insights", methods=["GET"])
def get_survey_insights(survey_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({"error": "Survey not found"}), 404

    try:
        insight = SurveyInsight.query.filter_by(survey_id=survey.id).first()
        if not insight:
            return jsonify({
                "survey_id": survey.id,
                "top_interests": [],
                "common_issues": [],
                "sentiment": "No data yet",
                "recommendations": ["No AI analysis generated yet. Click generate insights above."]
            })
        return jsonify(insight.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- LEAD MANAGEMENT ---

def calculate_lead_score_internal(product_interest, budget, purchase_timeline, customer_intent):
    score = 0
    
    # 1. Budget Score (Max 25 pts)
    try:
        if budget is not None:
            budget_val = int(budget)
            if budget_val >= 80000:
                score += 25
            elif budget_val >= 40000:
                score += 15
            elif budget_val > 0:
                score += 5
    except ValueError:
        pass
        
    # 2. Purchase Timeline Score (Max 25 pts)
    if purchase_timeline:
        timeline_lower = purchase_timeline.lower()
        if any(w in timeline_lower for w in ["week", "immediate", "now", "today", "1 week"]):
            score += 25
        elif any(w in timeline_lower for w in ["month", "soon", "1 month"]):
            score += 15
        elif any(w in timeline_lower for w in ["next month", "later", "future"]):
            score += 5
            
    # 3. Customer Intent Score (Max 25 pts)
    if customer_intent:
        intent_lower = customer_intent.lower()
        if "high" in intent_lower:
            score += 25
        elif "medium" in intent_lower or "moderate" in intent_lower:
            score += 15
        elif "low" in intent_lower:
            score += 5
            
    # 4. Product Interest Score (Max 25 pts)
    if product_interest:
        product_lower = product_interest.lower()
        if any(w in product_lower for w in ["laptop", "phone", "mouse", "keyboard", "device", "summit", "workshop"]):
            score += 25
        else:
            score += 10
            
    return score

def classify_lead_type_internal(score):
    if score >= 70:
        return "Hot Lead"
    elif score >= 40:
        return "Warm Lead"
    else:
        return "Cold Lead"

@app.route("/api/lead/calculate-score", methods=["POST"])
def calculate_lead_score_api():
    data = request.json or {}
    product_interest = data.get("product_interest")
    budget = data.get("budget")
    purchase_timeline = data.get("purchase_timeline")
    customer_intent = data.get("customer_intent")
    
    score = calculate_lead_score_internal(product_interest, budget, purchase_timeline, customer_intent)
    return jsonify({"score": score})

@app.route("/api/lead/classify", methods=["POST"])
def classify_lead_api():
    data = request.json or {}
    score = data.get("score")
    if score is None:
        return jsonify({"error": "Missing score field"}), 400
    try:
        score_val = int(score)
    except ValueError:
        return jsonify({"error": "Score must be an integer"}), 400
        
    category = classify_lead_type_internal(score_val)
    return jsonify({"category": category})

def process_lead_qualification_background(user_query, user_details):
    """
    Runs in a background thread to extract lead details from the user's query,
    computes scores, and saves or updates the lead record.
    """
    try:
        from ai_module.groq_client import generate_ai_response
        import json
        
        system_prompt = (
            "You are an AI Lead Qualification Agent. Your job is to extract lead profile information from customer conversations. "
            "Analyze the input and return strictly a JSON object with these keys:\n"
            "- 'product_interest': Product Interest (string, e.g. 'Gaming Laptop', or null if unspecified)\n"
            "- 'budget': Budget (integer, extract the number only, e.g. 80000, or null if unspecified)\n"
            "- 'purchase_timeline': Purchase Timeline (string, e.g. 'This Week', 'This Month', or null if unspecified)\n"
            "- 'customer_intent': Customer Intent (High, Medium, or Low, or null if unspecified)\n"
            "Do not calculate a lead score or include any extra text. Return ONLY the raw JSON object."
        )
        
        response_text = generate_ai_response(user_query, system_prompt=system_prompt, json_mode=True)
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1])
        parsed = json.loads(cleaned)
        
        product_interest = parsed.get("product_interest")
        budget = parsed.get("budget")
        purchase_timeline = parsed.get("purchase_timeline")
        customer_intent = parsed.get("customer_intent")
        
        if not any([product_interest, budget, purchase_timeline, customer_intent]):
            return
            
        budget_val = None
        if budget is not None:
            try:
                budget_val = int(budget)
            except ValueError:
                pass
        
        lead_score = calculate_lead_score_internal(product_interest, budget_val, purchase_timeline, customer_intent)
        lead_type = classify_lead_type_internal(lead_score)
        
        email = user_details.get("email")
        name = user_details.get("name", "AI Assistant User")
        phone = user_details.get("phone")
        user_id = user_details.get("user_id")
        
        if not email:
            return
            
        with app.app_context():
            user = None
            if user_id:
                user = User.query.get(user_id)
            elif email:
                user = User.query.filter_by(email=email).first()
            if user:
                user.last_activity_date = datetime.utcnow()
                if product_interest:
                    user.previous_interests = product_interest

            existing = Lead.query.filter_by(email=email).first()
            if existing:
                if name and name != "AI Assistant User":
                    existing.name = name
                if phone:
                    existing.phone = phone
                if product_interest:
                    existing.product_interest = product_interest
                if budget_val is not None:
                    existing.budget = budget_val
                if purchase_timeline:
                    existing.purchase_timeline = purchase_timeline
                if customer_intent:
                    existing.customer_intent = customer_intent
                
                merged_score = calculate_lead_score_internal(
                    existing.product_interest, 
                    existing.budget, 
                    existing.purchase_timeline, 
                    existing.customer_intent
                )
                existing.lead_score = merged_score
                existing.lead_type = classify_lead_type_internal(merged_score)
                if user_id:
                    existing.user_id = user_id
                db.session.commit()
                print(f"[BACKGROUND LEAD QUALIFICATION] Updated lead: {email} with score {merged_score}")
            else:
                new_lead = Lead(
                    name=name,
                    email=email,
                    phone=phone,
                    user_id=user_id,
                    product_interest=product_interest,
                    budget=budget_val,
                    purchase_timeline=purchase_timeline,
                    customer_intent=customer_intent,
                    lead_score=lead_score,
                    lead_type=lead_type,
                    lead_status="New"
                )
                db.session.add(new_lead)
                db.session.commit()
                print(f"[BACKGROUND LEAD QUALIFICATION] Created new lead: {email} with score {lead_score}")
    except Exception as e:
        print(f"[BACKGROUND LEAD QUALIFICATION ERROR] {e}")

@app.route("/api/leads", methods=["POST"])
@app.route("/lead", methods=["POST"])
def create_lead():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    company = data.get("company")
    lead_status = data.get("lead_status", "New")
    
    user_id = data.get("user_id")
    product_interest = data.get("product_interest")
    budget = data.get("budget")
    purchase_timeline = data.get("purchase_timeline")
    customer_intent = data.get("customer_intent")
    
    if not name:
        return jsonify({"error": "Name is required"}), 400

    try:
        budget_val = None
        if budget is not None:
            try:
                budget_val = int(budget)
            except ValueError:
                pass

        lead_score = calculate_lead_score_internal(product_interest, budget_val, purchase_timeline, customer_intent)
        lead_type = classify_lead_type_internal(lead_score)

        existing = Lead.query.filter_by(email=email).first() if email else None
        if existing:
            existing.name = name
            if phone:
                existing.phone = phone
            if company:
                existing.company = company
            existing.lead_status = lead_status
            if user_id:
                existing.user_id = user_id
            if product_interest:
                existing.product_interest = product_interest
            if budget_val is not None:
                existing.budget = budget_val
            if purchase_timeline:
                existing.purchase_timeline = purchase_timeline
            if customer_intent:
                existing.customer_intent = customer_intent
            existing.lead_score = lead_score
            existing.lead_type = lead_type
            db.session.commit()
            return jsonify({"message": "Lead Updated Successfully", "lead": existing.to_dict()})

        new_lead = Lead(
            name=name,
            email=email,
            phone=phone,
            company=company,
            lead_status=lead_status,
            user_id=user_id,
            product_interest=product_interest,
            budget=budget_val,
            purchase_timeline=purchase_timeline,
            customer_intent=customer_intent,
            lead_score=lead_score,
            lead_type=lead_type
        )
        db.session.add(new_lead)
        db.session.commit()
        return jsonify({"message": "Lead Added Successfully", "lead": new_lead.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/lead/<int:lead_id>", methods=["PUT", "DELETE"])
def lead_detail(lead_id):
    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    if request.method == "PUT":
        data = request.json or {}
        lead.name = data.get("name", lead.name)
        lead.email = data.get("email", lead.email)
        lead.phone = data.get("phone", lead.phone)
        lead.company = data.get("company", lead.company)
        lead.lead_status = data.get("lead_status", lead.lead_status)
        lead.product_interest = data.get("product_interest", lead.product_interest)
        lead.budget = data.get("budget", lead.budget)
        lead.purchase_timeline = data.get("purchase_timeline", lead.purchase_timeline)
        lead.customer_intent = data.get("customer_intent", lead.customer_intent)
        
        # Recompute score/type
        lead.lead_score = calculate_lead_score_internal(
            lead.product_interest, 
            lead.budget, 
            lead.purchase_timeline, 
            lead.customer_intent
        )
        lead.lead_type = classify_lead_type_internal(lead.lead_score)
        
        try:
            db.session.commit()
            return jsonify({"message": "Lead updated successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            db.session.delete(lead)
            db.session.commit()
            return jsonify({"message": "Lead deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route("/leads", methods=["GET"])
def get_leads():
    try:
        status_filter = request.args.get("status")
        search_query = request.args.get("search")
        category_filter = request.args.get("category")
        sort_by = request.args.get("sort")

        query = Lead.query
        
        if status_filter:
            query = query.filter_by(lead_status=status_filter)
            
        if search_query:
            query = query.filter(
                (Lead.name.ilike(f"%{search_query}%")) | 
                (Lead.email.ilike(f"%{search_query}%")) | 
                (Lead.product_interest.ilike(f"%{search_query}%"))
            )
            
        if category_filter:
            category_db = f"{category_filter} Lead" if "lead" not in category_filter.lower() else category_filter
            query = query.filter(Lead.lead_type.ilike(category_db))

        # Sorting logic
        if sort_by == "score_desc":
            query = query.order_by(Lead.lead_score.desc())
        elif sort_by == "score_asc":
            query = query.order_by(Lead.lead_score.asc())
        elif sort_by == "date_desc":
            query = query.order_by(Lead.created_at.desc())
        elif sort_by == "date_asc":
            query = query.order_by(Lead.created_at.asc())
        else:
            query = query.order_by(Lead.created_at.desc())

        leads_list = query.all()
        result = []
        for l in leads_list:
            result.append([
                l.lead_id, 
                l.name, 
                l.email, 
                l.phone, 
                l.company, 
                l.lead_status,
                l.user_id,
                l.product_interest,
                l.budget,
                l.purchase_timeline,
                l.customer_intent,
                l.lead_score,
                l.lead_type,
                l.created_at.isoformat() if l.created_at else ""
            ])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- CUSTOMER RE-ENGAGEMENT ---

@app.route("/reengagement/inactive", methods=["GET"])
def get_inactive_users():
    try:
        # Returns all users that might be inactive.
        # Since this is a demo, we return users with simulated inactive durations.
        users_list = User.query.filter_by(role="user").all()
        result = []
        for u in users_list:
            result.append([
                u.user_id,
                u.full_name,
                u.email,
                "30+ Days",
                "Medium Risk"
            ])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reengagement/campaign", methods=["POST"])
def trigger_reengagement():
    data = request.json or {}
    user_email = data.get("email")
    user_name = data.get("name", "Valued Customer")

    if not user_email:
        return jsonify({"error": "Email is required"}), 400

    # SMTP re-engagement message trigger (AI template placeholders will go here later)
    subject = "We miss you at Salesbot!"
    body = f"Hi {user_name},\nIt has been a while since you logged into Salesbot. We have updated our services with AI features. Log in now and check them out!"
    
    success = send_email_notification(user_email, subject, body)
    if success:
        return jsonify({"message": f"Re-engagement Campaign Triggered successfully for {user_name}"})
    else:
        return jsonify({"error": "Failed to send email notification"}), 500

# --- REPORTS & ANALYTICS ---

@app.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    try:
        total_users = User.query.count()
        total_leads = Lead.query.count()
        total_campaigns = Campaign.query.count()
        total_registrations = EventRegistration.query.count()
        
        # Lead classification counts
        hot_leads = Lead.query.filter(Lead.lead_type.ilike("Hot Lead")).count()
        warm_leads = Lead.query.filter(Lead.lead_type.ilike("Warm Lead")).count()
        cold_leads = Lead.query.filter(Lead.lead_type.ilike("Cold Lead")).count()

        return jsonify({
            "users": total_users,
            "leads": total_leads,
            "campaigns": total_campaigns,
            "registrations": total_registrations,
            "hot_leads": hot_leads,
            "warm_leads": warm_leads,
            "cold_leads": cold_leads
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- USER MANAGEMENT ---

@app.route("/allusers", methods=["GET"])
def get_all_users():
    try:
        users_list = User.query.all()
        # Return format matching front-end list requirements
        result = []
        for u in users_list:
            result.append([
                u.user_id, 
                u.full_name, 
                u.email, 
                u.role,
                u.phone or ""
            ])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/user/<int:user_id>", methods=["PUT", "DELETE"])
def user_detail(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == "PUT":
        data = request.json or {}
        user.full_name = data.get("full_name", user.full_name)
        user.email = data.get("email", user.email)
        user.role = data.get("role", user.role)
        user.phone = data.get("phone", user.phone)
        try:
            db.session.commit()
            return jsonify({"message": "User updated successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    elif request.method == "DELETE":
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({"message": "User deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

# --- CONVERSATION LOGS & PERSISTENCE ---

@app.route("/api/conversations/history", methods=["GET"])
def get_conversation_history():
    user_id = request.args.get("user_id")
    email = request.args.get("email")
    from models import Conversation
    
    query = Conversation.query
    if user_id:
        query = query.filter_by(user_id=int(user_id))
    elif email:
        user = User.query.filter_by(email=email).first()
        if user:
            query = query.filter_by(user_id=user.user_id)
        else:
            return jsonify([])
    else:
        return jsonify({"error": "Missing user_id or email parameter"}), 400
        
    convs = query.order_by(Conversation.timestamp.asc()).all()
    return jsonify([c.to_dict() for c in convs])

@app.route("/api/conversations/logs", methods=["GET"])
def get_conversation_logs():
    try:
        from models import Conversation
        convs = Conversation.query.order_by(Conversation.timestamp.desc()).all()
        result = []
        for c in convs:
            user_info = {"name": "Guest User", "email": "N/A"}
            if c.user_id:
                user = User.query.get(c.user_id)
                if user:
                    user_info = {"name": user.full_name, "email": user.email}
            result.append({
                "id": c.id,
                "user_id": c.user_id,
                "user_name": user_info["name"],
                "user_email": user_info["email"],
                "user_message": c.user_message,
                "ai_response": c.ai_response,
                "timestamp": c.timestamp.isoformat() if c.timestamp else ""
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversations/stats", methods=["GET"])
def get_conversation_stats():
    try:
        from models import Conversation
        total_conversations = Conversation.query.count()
        
        # Unique users count
        unique_user_ids = db.session.query(Conversation.user_id).distinct().all()
        unique_users = len([u for u in unique_user_ids if u[0] is not None])
        
        # Keyword counts for FAQs
        all_messages = Conversation.query.all()
        keyword_counts = {
            "Gaming Laptop Inquiry": 0,
            "Offer & Discount Inquiry": 0,
            "Event & Registration Inquiry": 0,
            "General Price Comparison": 0
        }
        for c in all_messages:
            msg = (c.user_message or "").lower()
            if "gaming" in msg or "laptop" in msg:
                keyword_counts["Gaming Laptop Inquiry"] += 1
            if "offer" in msg or "discount" in msg or "campaign" in msg:
                keyword_counts["Offer & Discount Inquiry"] += 1
            if "event" in msg or "summit" in msg or "registration" in msg or "invitation" in msg:
                keyword_counts["Event & Registration Inquiry"] += 1
            if "price" in msg or "cost" in msg or "compare" in msg:
                keyword_counts["General Price Comparison"] += 1
                
        sorted_faqs = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        faqs_list = [{"topic": f[0], "count": f[1]} for f in sorted_faqs]
        
        return jsonify({
            "total_conversations": total_conversations,
            "unique_users": unique_users,
            "faqs": faqs_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- CUSTOMER RE-ENGAGEMENT CAMPAIGNS ---

@app.route("/api/reengagement/inactive", methods=["GET"])
def get_inactive_users_api():
    try:
        from datetime import datetime, timedelta
        from models import User
        
        # Get all users with role 'user'
        users = User.query.filter_by(role="user").all()
        inactive_users = []
        
        now = datetime.utcnow()
        threshold = now - timedelta(days=30)
        
        for u in users:
            is_inactive = False
            last_active_str = "Never"
            days_inactive = 0
            
            if u.last_activity_date is None:
                # For demo/out-of-the-box, we treat users without recorded activity as inactive
                is_inactive = True
                last_active_str = "35 Days Ago"
                days_inactive = 35
            elif u.last_activity_date < threshold:
                is_inactive = True
                days_inactive = (now - u.last_activity_date).days
                last_active_str = f"{days_inactive} Days Ago"
                
            if is_inactive:
                inactive_users.append({
                    "user_id": u.user_id,
                    "full_name": u.full_name,
                    "email": u.email,
                    "phone": u.phone or "",
                    "last_active": last_active_str,
                    "days_inactive": days_inactive,
                    "previous_interests": u.previous_interests or "General Interests",
                    "risk_level": "High Risk" if days_inactive > 45 else "Medium Risk"
                })
                
        return jsonify(inactive_users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reengagement/history", methods=["GET"])
def get_reengagement_history_api():
    try:
        from models import ReengagementCampaign
        campaigns = ReengagementCampaign.query.order_by(ReengagementCampaign.sent_at.desc()).all()
        return jsonify([c.to_dict() for c in campaigns])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reengagement/stats", methods=["GET"])
def get_reengagement_stats_api():
    try:
        from models import User, ReengagementCampaign
        from datetime import datetime, timedelta
        
        # Total Inactive Users
        users = User.query.filter_by(role="user").all()
        now = datetime.utcnow()
        threshold = now - timedelta(days=30)
        inactive_count = 0
        for u in users:
            if u.last_activity_date is None or u.last_activity_date < threshold:
                inactive_count += 1
                
        # Re-engagement Emails Sent
        sent_count = ReengagementCampaign.query.count()
        
        # Re-engaged Users (campaigns where reengaged=True)
        reengaged_count = db.session.query(ReengagementCampaign.user_id).filter_by(reengaged=True).distinct().count()
        
        # Conversion Rate
        conversion_rate = 0.0
        if sent_count > 0:
            conversion_rate = round((reengaged_count / sent_count) * 100.0, 1)
            
        return jsonify({
            "total_inactive": inactive_count,
            "emails_sent": sent_count,
            "reengaged_users": reengaged_count,
            "conversion_rate": conversion_rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reengagement/trigger", methods=["POST"])
def trigger_reengagement_campaign_api():
    data = request.json or {}
    user_id = data.get("user_id")
    email = data.get("email")
    
    from models import User, ReengagementCampaign
    user = None
    if user_id:
        user = User.query.get(int(user_id))
    elif email:
        user = User.query.filter_by(email=email).first()
        
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    try:
        customer_name = user.full_name
        customer_email = user.email
        previous_interests = user.previous_interests or "General AI Features"
        
        from ai_module.groq_client import generate_ai_response
        import json
        
        prompt = (
            f"Generate a re-engagement follow-up message for:\n"
            f"Customer Name: {customer_name}\n"
            f"Previous Interest: {previous_interests}\n"
            f"Last Interaction: 30+ Days Ago\n"
        )
        
        system_prompt = (
            "You are an AI Customer Re-engagement Agent. "
            "Create a personalized follow-up email/reminder layout returned strictly in JSON format:\n"
            "- 'subject': High-open-rate subject line re-engaging the user\n"
            "- 'body': A warm, personalized re-engagement follow-up email/message referencing their previous interest, offering an exclusive discount/offer, and inviting them back.\n"
            "Return ONLY the JSON structure."
        )
        
        response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)
        
        subject = f"We Miss You, {customer_name}!"
        body = f"Hi {customer_name},\n\nWe noticed you were interested in {previous_interests} and wanted to check in. Here is a special 15% discount for you!"
        
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    cleaned = "\n".join(lines[1:-1])
            parsed = json.loads(cleaned)
            subject = parsed.get("subject", subject)
            body_val = parsed.get("body", body)
            if isinstance(body_val, dict):
                body_parts = []
                for k, v in body_val.items():
                    if isinstance(v, str):
                        body_parts.append(v)
                body = "\n\n".join(body_parts) if body_parts else str(body_val)
            elif isinstance(body_val, str):
                body = body_val
            else:
                body = str(body_val)
        except Exception as ex:
            print(f"[REENGAGEMENT TRIGGER AI PARSE ERROR] {ex}")
            
        # Send email
        email_status = "Sent"
        success = send_email_notification(customer_email, subject, body)
        if not success:
            email_status = "Failed"
            
        # Log campaign
        new_camp = ReengagementCampaign(
            user_id=user.user_id,
            customer_name=customer_name,
            customer_email=customer_email,
            subject=subject,
            body=body,
            status=email_status
        )
        db.session.add(new_camp)
        
        # Update user's last activity date to prevent automatic spamming immediately
        user.last_activity_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": f"Re-engagement campaign triggered successfully for {customer_name}",
            "campaign": new_camp.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def run_automatic_reengagement_loop():
    import time
    from datetime import datetime, timedelta
    
    # Give server time to boot
    time.sleep(10)
    
    while True:
        try:
            with app.app_context():
                from models import User, ReengagementCampaign
                
                now = datetime.utcnow()
                inactive_threshold = now - timedelta(days=30)
                spam_threshold = now - timedelta(days=30)
                
                users = User.query.filter_by(role="user").all()
                for u in users:
                    # Check if inactive
                    is_inactive = (u.last_activity_date is None or u.last_activity_date < inactive_threshold)
                    if not is_inactive:
                        continue
                        
                    # Check if they already received a campaign within the spam threshold
                    recent_campaign = ReengagementCampaign.query.filter(
                        ReengagementCampaign.user_id == u.user_id,
                        ReengagementCampaign.sent_at >= spam_threshold
                    ).first()
                    
                    if recent_campaign:
                        continue
                        
                    print(f"[AUTO REENGAGEMENT] Triggering campaign for inactive user: {u.email}")
                    
                    customer_name = u.full_name
                    customer_email = u.email
                    previous_interests = u.previous_interests or "General AI Features"
                    
                    from ai_module.groq_client import generate_ai_response
                    import json
                    
                    prompt = (
                        f"Generate a re-engagement follow-up message for:\n"
                        f"Customer Name: {customer_name}\n"
                        f"Previous Interest: {previous_interests}\n"
                        f"Last Interaction: 30+ Days Ago\n"
                    )
                    
                    system_prompt = (
                        "You are an AI Customer Re-engagement Agent. "
                        "Create a personalized follow-up email/reminder layout returned strictly in JSON format:\n"
                        "- 'subject': High-open-rate subject line re-engaging the user\n"
                        "- 'body': A warm, personalized re-engagement follow-up email/message referencing their previous interest, offering an exclusive discount/offer, and inviting them back.\n"
                        "Return ONLY the JSON structure."
                    )
                    
                    response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)
                    
                    subject = f"We Miss You, {customer_name}!"
                    body = f"Hi {customer_name},\n\nWe noticed you were interested in {previous_interests} and wanted to check in. Here is a special 15% discount for you!"
                    
                    try:
                        cleaned = response_text.strip()
                        if cleaned.startswith("```"):
                            lines = cleaned.splitlines()
                            if lines[0].startswith("```"):
                                cleaned = "\n".join(lines[1:-1])
                        parsed = json.loads(cleaned)
                        subject = parsed.get("subject", subject)
                        body_val = parsed.get("body", body)
                        if isinstance(body_val, dict):
                            body_parts = []
                            for k, v in body_val.items():
                                if isinstance(v, str):
                                    body_parts.append(v)
                            body = "\n\n".join(body_parts) if body_parts else str(body_val)
                        elif isinstance(body_val, str):
                            body = body_val
                        else:
                            body = str(body_val)
                    except Exception as ex:
                        print(f"[AUTO REENGAGEMENT AI PARSE ERROR] {ex}")
                        
                    # Send email
                    email_status = "Sent"
                    success = send_email_notification(customer_email, subject, body)
                    if not success:
                        email_status = "Failed"
                        
                    # Log campaign
                    new_camp = ReengagementCampaign(
                        user_id=u.user_id,
                        customer_name=customer_name,
                        customer_email=customer_email,
                        subject=subject,
                        body=body,
                        status=email_status
                    )
                    db.session.add(new_camp)
                    
                    # Update activity timestamp
                    u.last_activity_date = datetime.utcnow()
                    
                    db.session.commit()
                    print(f"[AUTO REENGAGEMENT] Successfully sent and logged campaign for {u.email}")
                    
        except Exception as e:
            print(f"[AUTO REENGAGEMENT ERROR] {e}")
            
        time.sleep(60)

# Start background thread for automatic campaigns
import threading
auto_reengage_thread = threading.Thread(target=run_automatic_reengagement_loop)
auto_reengage_thread.daemon = True
auto_reengage_thread.start()

def run_automatic_reminders_loop():
    import time
    from datetime import date, timedelta
    
    # Give server time to boot
    time.sleep(15)
    
    while True:
        try:
            with app.app_context():
                from models import Event, EventRegistration, EmailLog
                
                tomorrow = date.today() + timedelta(days=1)
                # Find active events happening tomorrow
                events = Event.query.filter_by(date=tomorrow, invitation_status='Active').all()
                
                for event in events:
                    # Find all confirmed registrations for this event
                    regs = EventRegistration.query.filter_by(event_id=event.id, status='Confirmed').all()
                    for reg in regs:
                        # Check if reminder already sent to this email for this event
                        already_sent = EmailLog.query.filter_by(
                            recipient_email=reg.email,
                            email_type="reminder"
                        ).filter(EmailLog.subject.like(f"%{event.title}%")).first()
                        
                        if already_sent:
                            continue
                            
                        print(f"[AUTO REMINDER] Triggering reminder for event '{event.title}' to {reg.email}")
                        
                        prompt = (
                            f"Generate a friendly event reminder email for:\n"
                            f"Recipient Name: {reg.full_name}\n"
                            f"Event Name: {event.title}\n"
                            f"Event Date: {event.date.isoformat()}\n"
                            f"Time: {event.time}\n"
                            f"Venue: {event.venue}\n"
                        )
                        system_prompt = (
                            "You are an Event Coordinator. Create a friendly, professional event reminder email returned strictly in JSON format:\n"
                            "- 'subject': Engaging reminder subject line (e.g. 'Reminder: [Event Name] is tomorrow!')\n"
                            "- 'body': A warm event reminder email body reminding them of their seat, date, time, and venue, and that we look forward to seeing them.\n"
                            "Return ONLY the JSON structure. Do not output anything else."
                        )
                        
                        response_text = generate_ai_response(prompt, system_prompt=system_prompt, json_mode=True)
                        subject = f"Reminder: {event.title} is tomorrow!"
                        body = f"Dear {reg.full_name},\n\nThis is a friendly reminder that the event '{event.title}' is scheduled for tomorrow ({event.date}) at {event.time} located at {event.venue}.\n\nWe look forward to your participation.\n\nRegards,\nEvent Coordinator"
                        
                        try:
                            cleaned = response_text.strip()
                            if cleaned.startswith("```"):
                                lines = cleaned.splitlines()
                                if lines[0].startswith("```"):
                                    cleaned = "\n".join(lines[1:-1])
                            parsed = json.loads(cleaned)
                            subject = parsed.get("subject", subject)
                            body = parsed.get("body", body)
                        except Exception as ex:
                            print(f"[AUTO REMINDER AI PARSE ERROR] {ex}. Using default template.")
                            
                        send_email_notification(reg.email, subject, body, email_type="reminder")
                        
        except Exception as e:
            print(f"[AUTO REMINDER ERROR] {e}")
            
        time.sleep(60)

# Start background thread for automatic reminders
reminder_thread = threading.Thread(target=run_automatic_reminders_loop)
reminder_thread.daemon = True
reminder_thread.start()


# Run Flask Application
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)