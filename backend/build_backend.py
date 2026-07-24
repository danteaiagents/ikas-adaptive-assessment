import os
import textwrap

BASE_DIR = '/Users/dantepilla/Documents/Antigravity/IKAS/backend'

FILES = {
    'requirements.txt': """\
Flask==3.0.3
psycopg2-binary==2.9.9
SQLAlchemy==2.0.30
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.6.0
Flask-Cors==4.0.1
pydantic==2.7.1
neo4j==5.20.0
gunicorn==22.0.0
python-dotenv==1.0.1
pytest==8.2.0
scipy==1.13.0
""",
    'Dockerfile': """\
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
""",
    'wsgi.py': """\
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
""",
    'app/__init__.py': """\
from flask import Flask
from .config import Config
from .extensions import db, jwt, cors, init_neo4j

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    with app.app_context():
        init_neo4j(app)
        db.create_all()

    from .api.v1 import bp as v1_bp
    app.register_blueprint(v1_bp, url_prefix='/api/v1')

    return app
""",
    'app/config.py': """\
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('PG_URI') or 'postgresql://postgres:postgres@localhost:5432/ikas'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    NEO4J_URI = os.environ.get('NEO4J_URI') or 'bolt://localhost:7687'
    NEO4J_USER = os.environ.get('NEO4J_USER') or 'neo4j'
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD') or 'password'
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER') or 'gemini'
    LLM_MODEL = os.environ.get('LLM_MODEL') or 'gemini-2.5-flash'
    LLM_API_KEY = os.environ.get('LLM_API_KEY') or ''
""",
    'app/extensions.py': """\
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from neo4j import GraphDatabase

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

neo4j_driver = None

def init_neo4j(app):
    global neo4j_driver
    uri = app.config['NEO4J_URI']
    user = app.config['NEO4J_USER']
    password = app.config['NEO4J_PASSWORD']
    neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
""",
    'app/models/__init__.py': "",
    'app/models/db_models.py': """\
from app.extensions import db
import uuid
from datetime import datetime, timezone

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='student')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class TestSession(db.Model):
    __tablename__ = 'test_sessions'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    session_id = db.Column(db.String(36), db.ForeignKey('test_sessions.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.String(100), nullable=False)
    question_level = db.Column(db.String(20), nullable=False)
    user_answer = db.Column(db.JSON, nullable=False)
    is_correct = db.Column(db.Boolean)
    partial_score = db.Column(db.Float)
    grading_details = db.Column(db.JSON)
    time_taken_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
""",
    'app/models/dtos.py': """\
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SessionStart(BaseModel):
    subject: str
    preset: str = 'Standard Assessment'

class AnswerSubmit(BaseModel):
    session_id: str
    question_id: str
    selected_options: List[str]
    time_taken_seconds: int
""",
    'app/repositories/__init__.py': "",
    'app/repositories/user_repo.py': """\
from app.models.db_models import User, TestSession, Response
from app.extensions import db

class UserRepository:
    @staticmethod
    def get_by_email(email: str):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create_user(email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        return user
""",
    'app/repositories/question_repo.py': """\
from app.extensions import neo4j_driver

class QuestionRepository:
    @staticmethod
    def get_question(question_id: str):
        query = "MATCH (q:Question {id: $qid}) RETURN q"
        with neo4j_driver.session() as session:
            result = session.run(query, qid=question_id)
            record = result.single()
            return dict(record['q']) if record else None

    @staticmethod
    def get_candidate_questions(subject: str, level: str):
        query = \"\"\"
        MATCH (s:Subject {name: $subject})-[:CONTAINS]->(t:Topic)-[:CONTAINS]->(c:Concept)-[:HAS_QUESTION]->(q:Question {level: $level})
        RETURN q
        \"\"\"
        with neo4j_driver.session() as session:
            result = session.run(query, subject=subject, level=level)
            return [dict(record['q']) for record in result]
""",
    'app/repositories/graph_repo.py': """\
from app.extensions import neo4j_driver

class GraphRepository:
    @staticmethod
    def update_edge_probability(q1_id: str, q2_id: str, new_prob: float):
        query = \"\"\"
        MATCH (q1:Question {id: $q1_id})-[r:IS_PREREQUISITE_FOR]->(q2:Question {id: $q2_id})
        SET r.probability = $new_prob
        \"\"\"
        with neo4j_driver.session() as session:
            session.run(query, q1_id=q1_id, q2_id=q2_id, new_prob=new_prob)
""",
    'app/services/__init__.py': "",
    'app/services/llm_provider.py': """\
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str, **kwargs) -> str: pass

class GeminiProvider(LLMProvider):
    def generate(self, prompt: str, system_prompt: str, **kwargs) -> str:
        return "Gemini Response"
""",
    'app/utils/__init__.py': "",
    'app/utils/math_utils.py': """\
import numpy as np

def irt_probability(theta: float, a: float, b: float, c: float) -> float:
    return c + (1 - c) / (1 + np.exp(-a * (theta - b)))

def fisher_information(theta: float, a: float, b: float, c: float) -> float:
    p = irt_probability(theta, a, b, c)
    if p >= 1.0 or p <= 0.0: return 0.0
    return (a ** 2) * ((1 - p) / p) * (((p - c) / (1 - c)) ** 2)
""",
    'app/services/adaptive_engine.py': """\
from app.utils.math_utils import fisher_information

class AdaptiveEngine:
    def __init__(self):
        self.theta = 0.0

    def select_next_question(self, candidates: list, answered_ids: list):
        best_q = None
        best_score = -1
        for q in candidates:
            if q['id'] in answered_ids: continue
            a = q.get('a', 1.0)
            b = q.get('b', 0.0)
            c = q.get('c', 0.25)
            score = fisher_information(self.theta, a, b, c)
            if score > best_score:
                best_score = score
                best_q = q
        return best_q
""",
    'app/services/grading_service.py': """\
class GradingService:
    @staticmethod
    def grade_mcq(selected: list, correct: list) -> float:
        # Simple partial credit:
        if not correct: return 0.0
        correct_selected = set(selected).intersection(set(correct))
        incorrect_selected = set(selected) - set(correct)
        
        score = len(correct_selected) / len(correct) - (len(incorrect_selected) * 0.5)
        return max(0.0, score)
""",
    'app/services/session_service.py': """\
from app.models.db_models import TestSession, Response
from app.extensions import db

class SessionService:
    @staticmethod
    def start_session(user_id: str, subject: str):
        session = TestSession(user_id=user_id, subject=subject)
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def record_response(session_id: str, user_id: str, qid: str, qlevel: str, answer: list, score: float):
        resp = Response(
            session_id=session_id, user_id=user_id, question_id=qid, question_level=qlevel,
            user_answer=answer, is_correct=score == 1.0, partial_score=score,
            time_taken_seconds=0
        )
        db.session.add(resp)
        db.session.commit()
""",
    'app/services/report_service.py': """\
from app.models.db_models import Response

class ReportService:
    @staticmethod
    def generate_report(session_id: str):
        responses = Response.query.filter_by(session_id=session_id).all()
        total = len(responses)
        correct = sum(1 for r in responses if r.is_correct)
        return {"total_questions": total, "correct_answers": correct}
""",
    'app/api/__init__.py': "",
    'app/api/v1/__init__.py': """\
from flask import Blueprint

bp = Blueprint('v1', __name__)

from . import auth, tests, questions, reports
""",
    'app/api/v1/auth.py': """\
from flask import request, jsonify
from . import bp
from app.models.dtos import UserRegister, UserLogin
from app.repositories.user_repo import UserRepository
from flask_jwt_extended import create_access_token
import pydantic

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = UserRegister(**request.json)
    except pydantic.ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    
    # Hash password in real app
    user = UserRepository.create_user(data.email, data.password)
    return jsonify({"success": True, "data": {"id": user.id}}), 201

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = UserLogin(**request.json)
    except pydantic.ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
        
    user = UserRepository.get_by_email(data.email)
    if not user or user.password_hash != data.password:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
        
    token = create_access_token(identity=user.id)
    return jsonify({"success": True, "data": {"access_token": token}})
""",
    'app/api/v1/tests.py': """\
from flask import request, jsonify
from . import bp
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.session_service import SessionService

@bp.route('/start', methods=['POST'])
@jwt_required()
def start_test():
    user_id = get_jwt_identity()
    session = SessionService.start_session(user_id, request.json.get('subject'))
    return jsonify({"success": True, "data": {"session_id": session.id}})
""",
    'app/api/v1/questions.py': """\
from flask import jsonify
from . import bp

@bp.route('/questions', methods=['GET'])
def get_questions():
    return jsonify({"success": True, "data": []})
""",
    'app/api/v1/reports.py': """\
from flask import jsonify
from . import bp
from app.services.report_service import ReportService

@bp.route('/reports/<session_id>', methods=['GET'])
def get_report(session_id):
    report = ReportService.generate_report(session_id)
    return jsonify({"success": True, "data": report})
""",
    'tests/__init__.py': "",
    'tests/test_api.py': """\
def test_sample():
    assert True
"""
}

for path, content in FILES.items():
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)
print("Generated all files successfully.")
