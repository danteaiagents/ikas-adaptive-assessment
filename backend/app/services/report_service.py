from app.models.db_models import TestSession, Response
from app.extensions import db
from typing import Dict, Any

def generate_session_report(session_id: str) -> Dict[str, Any]:
    session = db.session.get(TestSession, session_id)
    if not session:
        raise ValueError("Session not found")

    responses = Response.query.filter_by(session_id=session_id).all()
    total = len(responses)
    correct = sum(1 for r in responses if r.is_correct)
    score_sum = sum(r.partial_score for r in responses)

    # Basic stats
    report = {
        "session_id": session_id,
        "total_questions": total,
        "correct_count": correct,
        "score": score_sum,
        "theta": session.final_theta or 0.0,
        "theta_se": session.theta_se or 0.0,
        "level_breakdown": {},
        "concept_mastery": {},
        "recommendations": []
    }

    # Level breakdown
    for r in responses:
        lvl = str(r.question_level)
        if lvl not in report["level_breakdown"]:
            report["level_breakdown"][lvl] = {"total": 0, "correct": 0}
        report["level_breakdown"][lvl]["total"] += 1
        if r.is_correct:
            report["level_breakdown"][lvl]["correct"] += 1

    if session.final_theta is not None and session.final_theta < 0:
        report["recommendations"].append("Review foundational concepts before proceeding.")
    else:
        report["recommendations"].append("Great job! Ready for advanced topics.")

    return report

def get_user_progress(user_id: int, topic_id: str) -> Dict[str, Any]:
    sessions = TestSession.query.filter_by(user_id=user_id, topic_id=topic_id, status='completed').order_by(TestSession.completed_at).all()
    history = [{"session_id": s.id, "theta": s.final_theta, "date": s.completed_at.isoformat()} for s in sessions if s.final_theta is not None]
    return {"user_id": user_id, "topic_id": topic_id, "history": history}
