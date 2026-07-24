from flask import request
from flask_jwt_extended import jwt_required
from app.api.v1 import bp, api_response
from app.repositories.question_repo import get_question, get_questions_by_topic

@bp.route('/questions/<question_id>', methods=['GET'])
@jwt_required()
def read_question(question_id):
    q = get_question(question_id)
    if not q:
        return api_response(False, error="Not found", status=404)
    return api_response(True, data=q)

@bp.route('/topics/<topic_id>/questions', methods=['GET'])
@jwt_required()
def read_topic_questions(topic_id):
    qs = get_questions_by_topic(topic_id)
    return api_response(True, data=qs)
