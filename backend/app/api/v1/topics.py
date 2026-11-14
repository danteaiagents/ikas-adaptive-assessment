"""
Topics API — GET /topics, GET /topics/:id
"""

from flask import request
from app.api.v1 import bp, api_response
from app.repositories.graph_repo import get_all_topics, get_subject_topics


@bp.route('/topics', methods=['GET'])
def list_topics():
    """
    List all topics with concept and question counts.

    Optional query param:
      ?subject_id=s-ai   — filter to a specific subject

    Returns:
      [{id, name, description, subject_id, subject_name, concept_count, question_count}]
    """
    subject_id = request.args.get('subject_id')
    if subject_id:
        topics = get_subject_topics(subject_id)
        for t in topics:
            t['subject_id'] = subject_id
    else:
        topics = get_all_topics()

    return api_response(True, data=topics)
