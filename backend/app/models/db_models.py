from datetime import datetime, timezone
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(120))
    role = db.Column(db.String(20), default='student')
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class TestSession(db.Model):
    __tablename__ = 'test_sessions'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    subject_id = db.Column(db.String(64), nullable=True)
    topic_id = db.Column(db.String(64), nullable=False)
    preset = db.Column(db.String(32), default='standard')
    total_questions = db.Column(db.Integer, default=25)
    time_limit_minutes = db.Column(db.Integer, default=45)
    status = db.Column(db.String(20), default='active')
    final_theta = db.Column(db.Float, nullable=True)
    theta_se = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    # ── Historical record columns ────────────────────────────────────────────
    # Per-concept × per-level BKT mastery snapshot at session completion.
    # Schema: {concept_id: {level: {p_mastery, n_attempts, n_correct}}}
    # Powers continuity analysis: "how did mastery of Concept X progress
    # across the student's sessions over time?"
    concept_mastery_snapshot = db.Column(JSONB, nullable=True)

    # Recommendations that were surfaced to the student at the end of this session.
    # Schema: [{id, title, url, type, concept_id, concept_name, target_level}]
    # Powers future effectiveness analysis: "did students who followed
    # recommendation R improve in the next session?"
    recommendations_snapshot = db.Column(JSONB, nullable=True)


class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('test_sessions.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    question_id = db.Column(db.String(64), nullable=False, index=True)
    question_level = db.Column(db.String(20), index=True)
    user_answer = db.Column(JSONB, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    partial_score = db.Column(db.Float, default=0.0)
    grading_details = db.Column(JSONB)
    time_taken_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
