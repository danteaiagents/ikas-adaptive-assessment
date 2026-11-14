import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ikas')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Neo4j
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
    NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')
    NEO4J_MAX_POOL_SIZE = int(os.getenv('NEO4J_MAX_POOL_SIZE', 50))

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # LLM — default: Anthropic Claude
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'anthropic')
    LLM_MODEL = os.getenv('LLM_MODEL', 'claude-sonnet-4-20250514')
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', '')

    # OCI Object Storage (used for image uploads in Sprint 3)
    OCI_NAMESPACE = os.getenv('OCI_NAMESPACE', '')
    OCI_BUCKET_NAME = os.getenv('OCI_BUCKET_NAME', 'ikas-uploads')
    OCI_REGION = os.getenv('OCI_REGION', 'us-ashburn-1')
    OCI_COMPARTMENT_ID = os.getenv('OCI_COMPARTMENT_ID', '')
    # OCI auth: instance_principal (on OCI VM) or api_key (local dev)
    OCI_AUTH_TYPE = os.getenv('OCI_AUTH_TYPE', 'api_key')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # ── Adaptive Engine Tuning ───────────────────────────────────────────────
    # Multi-objective weights (must sum to 1.0).
    # Calibrate these after collecting real response data (~1,000+ sessions).
    #
    # ALPHA: Fisher Information weight — primary psychometric driver (CAT standard)
    # BETA:  Graph Entropy weight — how much unlocking downstream questions matters
    # GAMMA: Prerequisite Readiness weight — pedagogical gate, avoids gaps
    # DELTA: Level Progression weight — scaffolding Repeat→Summary→Intuitive→Apply
    ENGINE_WEIGHT_ALPHA = float(os.getenv('ENGINE_WEIGHT_ALPHA', '0.35'))  # Fisher Info
    ENGINE_WEIGHT_BETA  = float(os.getenv('ENGINE_WEIGHT_BETA',  '0.25'))  # Graph Entropy
    ENGINE_WEIGHT_GAMMA = float(os.getenv('ENGINE_WEIGHT_GAMMA', '0.20'))  # Prereq Readiness
    ENGINE_WEIGHT_DELTA = float(os.getenv('ENGINE_WEIGHT_DELTA', '0.20'))  # Level Progression

    # BKT (Bayesian Knowledge Tracing) parameters.
    # P_TRANSIT: probability of learning from a single correct answer (low = conservative)
    # P_GUESS:   probability of guessing correctly without knowledge
    # P_SLIP:    probability of answering incorrectly despite knowing the material
    BKT_P_TRANSIT = float(os.getenv('BKT_P_TRANSIT', '0.10'))
    BKT_P_GUESS   = float(os.getenv('BKT_P_GUESS',   '0.20'))
    BKT_P_SLIP    = float(os.getenv('BKT_P_SLIP',    '0.10'))

    # Mastery threshold: p_mastery must exceed this to advance to the next level.
    # 0.70 = conservative (good for competitive exam prep)
    # 0.60 = moderate (faster progression, more exploratory)
    # 0.50 = aggressive (treat 50/50 as "mastered", not recommended)
    ENGINE_MASTERY_THRESHOLD = float(os.getenv('ENGINE_MASTERY_THRESHOLD', '0.70'))
