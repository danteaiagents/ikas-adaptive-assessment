from flask import Blueprint, jsonify
from datetime import datetime, timezone

bp = Blueprint('api_v1', __name__)

def api_response(success: bool, data=None, error=None, status=200):
    response = {
        "success": success,
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}
    }
    return jsonify(response), status

from app.api.v1 import auth, tests, reports, questions, topics
