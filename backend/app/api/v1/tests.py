"""
Test Session API — POST /sessions, GET /next, POST /answer, POST /complete, GET /presets
"""

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError
from app.api.v1 import bp, api_response
from app.models.dtos import SessionStart, AnswerSubmit, QuestionOut, OptionOut
from app.services.session_service import (
    start_session,
    get_next_question,
    submit_answer,
    end_session,
    get_presets,
)


@bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """Start a new adaptive test session."""
    try:
        user_id = get_jwt_identity()
        data = SessionStart(**request.json)
        session = start_session(
            user_id=user_id,
            topic_id=data.topic_id,
            preset=data.preset,
            total_questions=data.total_questions,
            time_limit_minutes=data.time_limit_minutes,
        )
        return api_response(True, data={
            'session_id': session.id,
            'total_questions': session.total_questions,
            'time_limit_minutes': session.time_limit_minutes,
            'preset': session.preset,
        }, status=201)
    except ValidationError as e:
        return api_response(False, error=e.errors(), status=400)
    except Exception as e:
        return api_response(False, error=str(e), status=500)


@bp.route('/sessions/<session_id>/next', methods=['GET'])
@jwt_required()
def next_question(session_id):
    """Get the next adaptively selected question."""
    try:
        q = get_next_question(session_id)
        if not q:
            return api_response(True, data={'complete': True, 'message': 'No more questions'})

        # Format for frontend
        options = [
            OptionOut(id=opt.get('id', f'opt_{i}'), text=opt.get('text', str(opt)))
            if isinstance(opt, dict) else OptionOut(id=f'opt_{i}', text=str(opt))
            for i, opt in enumerate(q.get('options', []))
        ]
        q_out = QuestionOut(
            id=q['id'],
            stem=q['stem'],
            level=q.get('level', 'Repeat'),
            options=options,
            concept_id=q.get('concept_id', ''),
            concept_name=q.get('concept_name', ''),
            prerequisites=q.get('prerequisites', []),
            resources=q.get('resources', []),
        )
        return api_response(True, data=q_out.model_dump())
    except ValueError as e:
        return api_response(False, error=str(e), status=404)
    except Exception as e:
        return api_response(False, error=str(e), status=500)


@bp.route('/sessions/<session_id>/answer', methods=['POST'])
@jwt_required()
def answer_question(session_id):
    """Submit an answer, get grading result and engine state update."""
    try:
        data = AnswerSubmit(**request.json)
        grading_result, engine_update = submit_answer(
            session_id=session_id,
            question_id=data.question_id,
            selected_options=data.selected_options,
            time_taken_seconds=data.time_taken_seconds,
        )
        return api_response(True, data={
            'is_correct': grading_result.is_correct,
            'partial_score': grading_result.partial_score,
            'grading_details': grading_result.grading_details,
            'theta': engine_update.get('theta'),
            'theta_se': engine_update.get('theta_se'),
            'concept_mastery': engine_update.get('concept_mastery'),
        })
    except ValidationError as e:
        return api_response(False, error=e.errors(), status=400)
    except ValueError as e:
        return api_response(False, error=str(e), status=404)
    except Exception as e:
        return api_response(False, error=str(e), status=500)


@bp.route('/sessions/<session_id>/complete', methods=['POST'])
@jwt_required()
def complete_session(session_id):
    """End a test session and get final results."""
    session, engine_state = end_session(session_id)
    if not session:
        return api_response(False, error='Session not found', status=404)
    
    # Build per-level mastery breakdown from engine state
    level_breakdown = {}
    concept_mastery = {}
    if engine_state and engine_state.get('concept_mastery'):
        mastery_data = engine_state['concept_mastery']
        level_scores = {}  # {level: [scores]}
        for key, state in mastery_data.items():
            level = state.get('level', 'Repeat')
            p_mastery = state.get('p_mastery', 0.5)
            concept_id = state.get('concept_id', '')
            
            if level not in level_scores:
                level_scores[level] = []
            level_scores[level].append(p_mastery)
            
            # Per-concept per-level mastery
            if concept_id not in concept_mastery:
                concept_mastery[concept_id] = {}
            concept_mastery[concept_id][level] = {
                'p_mastery': round(p_mastery, 4),
                'n_attempts': state.get('n_attempts', 0),
                'n_correct': state.get('n_correct', 0),
            }
        
        for level, scores in level_scores.items():
            level_breakdown[level] = round(sum(scores) / len(scores), 4) if scores else 0.0
    
    return api_response(True, data={
        'status': 'completed',
        'final_theta': session.final_theta,
        'theta_se': session.theta_se,
        'n_responses': engine_state.get('n_responses', 0) if engine_state else 0,
        'level_breakdown': level_breakdown,
        'concept_mastery': concept_mastery,
    })


@bp.route('/presets', methods=['GET'])
def list_presets():
    """List available test presets."""
    return api_response(True, data=get_presets())
