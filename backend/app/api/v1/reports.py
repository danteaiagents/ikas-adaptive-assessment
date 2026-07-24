from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import bp, api_response
from app.services.report_service import generate_session_report, get_user_progress

@bp.route('/sessions/<session_id>/report', methods=['GET'])
@jwt_required()
def get_session_report(session_id):
    try:
        report = generate_session_report(session_id)
        return api_response(True, data=report)
    except Exception as e:
        return api_response(False, error=str(e), status=404)

@bp.route('/progress', methods=['GET'])
@jwt_required()
def user_progress():
    user_id = get_jwt_identity()
    topic_id = request.args.get('topic_id')
    if not topic_id:
        return api_response(False, error="topic_id required", status=400)
    
    progress = get_user_progress(user_id, topic_id)
    return api_response(True, data=progress)
