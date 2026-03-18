from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(64))  # "ai_specialist" or "comp_chem_specialist"
    current_level = db.Column(db.String(32), default="Apprentice")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    progress = db.relationship('Progress', backref='user', lazy=True)

class Competency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(2), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    modules = db.relationship('Module', backref='competency', lazy=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competency_id = db.Column(db.Integer, db.ForeignKey('competency.id'), nullable=False)
    key = db.Column(db.String(5), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

    progresses = db.relationship('Progress', backref='module', lazy=True)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    status = db.Column(db.String(32), default='incomplete')  # incomplete, completed
    quiz_passed = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    learning_level = db.Column(db.String(32))  # remember, understand, apply, analyze, evaluate, create
    quiz_in_progress = db.Column(db.Boolean, default=False)
    current_quiz_question = db.Column(db.Text)
    quiz_answer = db.Column(db.String(8))
    current_skill = db.Column(db.String(32))
    last_wrong_attempt = db.Column(db.Integer, default=0)
    awaiting_quiz_confirmation = db.Column(db.Boolean, default=False)
    extra_expl_count = db.Column(db.Integer, default=0)
    quiz_type = db.Column(db.String(10), default='mcq')  # 'mcq' or 'text'



    __table_args__ = (
        db.UniqueConstraint('user_id', 'module_id', name='unique_user_module'),
    )
