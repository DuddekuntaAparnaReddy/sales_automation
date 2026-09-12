from database.db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(30), nullable=False, default='user')
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity_date = db.Column(db.DateTime)
    previous_interests = db.Column(db.String(255))

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'previous_interests': self.previous_interests
        }

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15))
    company = db.Column(db.String(100))
    lead_status = db.Column(db.String(30), default='New')
    assigned_to = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer)
    product_interest = db.Column(db.String(100))
    budget = db.Column(db.Integer)
    purchase_timeline = db.Column(db.String(100))
    customer_intent = db.Column(db.String(30))
    lead_score = db.Column(db.Integer, default=0)
    lead_type = db.Column(db.String(20), default='Cold')

    @property
    def lead_id(self):
        return self.id

    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'lead_status': self.lead_status,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'product_interest': self.product_interest,
            'budget': self.budget,
            'purchase_timeline': self.purchase_timeline,
            'customer_intent': self.customer_intent,
            'lead_score': self.lead_score,
            'lead_type': self.lead_type
        }

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    campaign_id    = db.Column(db.Integer, primary_key=True)
    campaign_name  = db.Column(db.String(100), nullable=False)
    campaign_type  = db.Column(db.String(50))
    budget         = db.Column(db.Numeric(12, 2))
    product_name   = db.Column(db.String(150))
    offer_details  = db.Column(db.Text)
    target_audience= db.Column(db.String(100))
    start_date     = db.Column(db.Date)
    end_date       = db.Column(db.Date)
    status         = db.Column(db.String(30), default='Active')
    created_by     = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    ai_title       = db.Column(db.String(255))
    ai_subject     = db.Column(db.String(255))
    ai_body        = db.Column(db.Text)
    ai_cta         = db.Column(db.String(100))

    def to_dict(self):
        return {
            'campaign_id':    self.campaign_id,
            'campaign_name':  self.campaign_name,
            'campaign_type':  self.campaign_type,
            'budget':         float(self.budget) if self.budget else 0.0,
            'product_name':   self.product_name,
            'offer_details':  self.offer_details,
            'target_audience':self.target_audience,
            'start_date':     self.start_date.isoformat() if self.start_date else None,
            'end_date':       self.end_date.isoformat() if self.end_date else None,
            'status':         self.status or 'Active',
            'created_by':     self.created_by,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
            'ai_title':       self.ai_title,
            'ai_subject':     self.ai_subject,
            'ai_body':        self.ai_body,
            'ai_cta':         self.ai_cta,
        }

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    date = db.Column(db.Date)
    venue = db.Column(db.String(150))
    invitation_status = db.Column(db.String(30), default='Active')
    description = db.Column(db.Text)
    time = db.Column(db.String(30))
    event_type = db.Column(db.String(50))
    registration_deadline = db.Column(db.Date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def event_id(self):
        return self.id

    @property
    def event_name(self):
        return self.title

    @property
    def event_date(self):
        return self.date

    @property
    def location(self):
        return self.venue

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.id,
            'title': self.title,
            'event_name': self.title,
            'date': self.date.isoformat() if self.date else None,
            'event_date': self.date.isoformat() if self.date else None,
            'venue': self.venue,
            'location': self.venue,
            'invitation_status': self.invitation_status,
            'description': self.description,
            'time': self.time,
            'event_type': self.event_type,
            'registration_deadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    event_name = db.Column(db.String(100))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default='Confirmed')

    @property
    def registration_id(self):
        return self.id

    def to_dict(self):
        return {
            'id': self.id,
            'registration_id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'event_name': self.event_name,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'status': self.status
        }

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    id              = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(100), nullable=False)
    subject         = db.Column(db.String(255), nullable=False)
    body            = db.Column(db.Text, nullable=False)
    email_type      = db.Column(db.String(50), nullable=False)
    sent_at         = db.Column(db.DateTime, default=datetime.utcnow)
    status          = db.Column(db.String(20), nullable=False)
    campaign_id     = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id', ondelete='SET NULL'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'body': self.body,
            'email_type': self.email_type,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'campaign_id': self.campaign_id
        }


class Feedback(db.Model):
    __tablename__ = 'feedback'
    feedback_id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    comments = db.Column(db.Text)
    feedback_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'feedback_id': self.feedback_id,
            'rating': self.rating,
            'comments': self.comments,
            'feedback_date': self.feedback_date.isoformat() if self.feedback_date else None
        }

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    user_message = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class ReengagementCampaign(db.Model):
    __tablename__ = 'reengagement_campaigns'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default='Sent')
    reengaged = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'subject': self.subject,
            'body': self.body,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status,
            'reengaged': self.reengaged
        }


class Survey(db.Model):
    __tablename__ = 'surveys'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category    = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    questions = db.relationship('SurveyQuestion', backref='survey', cascade='all, delete-orphan', lazy=True)
    responses = db.relationship('SurveyResponse', backref='survey', cascade='all, delete-orphan', lazy=True)
    insight   = db.relationship('SurveyInsight', backref='survey', uselist=False, cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'questions': [q.to_dict() for q in self.questions]
        }


class SurveyQuestion(db.Model):
    __tablename__ = 'survey_questions'
    id            = db.Column(db.Integer, primary_key=True)
    survey_id     = db.Column(db.Integer, db.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # 'text', 'rating', 'choice'

    def to_dict(self):
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'question_text': self.question_text,
            'question_type': self.question_type
        }


class SurveyResponse(db.Model):
    __tablename__ = 'survey_responses'
    id            = db.Column(db.Integer, primary_key=True)
    survey_id     = db.Column(db.Integer, db.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    response_data = db.Column(db.JSON, nullable=False)  # dict/json representing user answers
    submitted_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'user_id': self.user_id,
            'response_data': self.response_data,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }


class SurveyInsight(db.Model):
    __tablename__ = 'survey_insights'
    id              = db.Column(db.Integer, primary_key=True)
    survey_id       = db.Column(db.Integer, db.ForeignKey('surveys.id', ondelete='CASCADE'), unique=True, nullable=False)
    top_interests   = db.Column(db.JSON)
    common_issues   = db.Column(db.JSON)
    sentiment       = db.Column(db.String(50))
    recommendations = db.Column(db.JSON)
    generated_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'top_interests': self.top_interests or [],
            'common_issues': self.common_issues or [],
            'sentiment': self.sentiment or "Neutral",
            'recommendations': self.recommendations or [],
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }
