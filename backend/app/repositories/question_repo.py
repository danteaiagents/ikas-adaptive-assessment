"""
Question Repository — Neo4j queries for questions, prerequisites, and resources.

All Cypher queries align with the schema defined in:
  knowledge-graph/schema/constraints.cypher
  knowledge-graph/schema/seed_data.cypher

Schema relationships:
  (:Topic)-[:CONTAINS]->(:Concept)-[:CONTAINS]->(:Question)
  (:Question)-[:IS_PREREQUISITE_FOR]->(:Question)
  (:Concept)-[:LINKED_RESOURCE]->(:Resource)
"""

import json
from typing import Dict, Any, List, Optional
from app.extensions import get_neo4j_session


def _clean_cypher_json(s: str) -> str:
    """Clean Cypher escaping artifacts from stored JSON strings."""
    if not s:
        return '[]'
    return (s.replace("\\\u2019", "'")
             .replace("\\\u2018", "'")
             .replace("\\'", "'")
             .replace("\u2019", "'")
             .replace("\u2018", "'"))


def get_question(question_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single question with its concept, options, and resources."""
    query = '''
    MATCH (c:Concept)-[:CONTAINS]->(q:Question {id: $question_id})
    OPTIONAL MATCH (c)-[:LINKED_RESOURCE]->(r:Resource)
    WITH q, c, collect(DISTINCT {id: r.id, url: r.url, title: r.title, type: r.type, level: r.level}) AS resources
    OPTIONAL MATCH (prereq_c:Concept)-[:CONTAINS]->(prereq:Question)-[:IS_PREREQUISITE_FOR]->(q)
    WITH q, c, resources,
         collect(DISTINCT {
           id: prereq.id,
           stem: prereq.stem,
           concept_id: prereq_c.id,
           concept_name: prereq_c.name,
           level: prereq.level
         }) AS prerequisites
    RETURN q.id AS id, q.stem AS stem, q.level AS level,
           q.question_type AS question_type,
           q.options AS options_json, q.correct_answers AS correct_answers_json,
           q.explanation AS explanation,
           q.difficulty AS b, q.discrimination AS a, q.guessing AS c,
           q.time_estimate_seconds AS time_estimate_seconds,
           c.id AS concept_id, c.name AS concept_name,
           resources, prerequisites
    '''
    with get_neo4j_session() as session:
        result = session.run(query, question_id=question_id)
        record = result.single()
        if not record:
            return None

        data = dict(record)
        # Parse JSON string fields
        data['options'] = _parse_options(data.pop('options_json', '[]'))
        data['correct_answers'] = json.loads(_clean_cypher_json(data.pop('correct_answers_json', '[]')))
        # Filter out null resources
        data['resources'] = [r for r in data.get('resources', []) if r.get('id')]
        # Filter out null prerequisite entries (OPTIONAL MATCH returns {id: null} when no prereqs)
        data['prerequisites'] = [p for p in data.get('prerequisites', []) if p.get('id')]
        return data



def get_questions_by_topic(topic_id: str) -> List[Dict[str, Any]]:
    """Fetch all questions for a given topic."""
    query = '''
    MATCH (t:Topic {id: $topic_id})-[:CONTAINS]->(c:Concept)-[:CONTAINS]->(q:Question)
    RETURN q.id AS id, q.stem AS stem, q.level AS level,
           q.difficulty AS b, q.discrimination AS a, q.guessing AS c,
           q.options AS options_json, q.correct_answers AS correct_answers_json,
           c.id AS concept_id, c.name AS concept_name
    '''
    with get_neo4j_session() as session:
        result = session.run(query, topic_id=topic_id)
        questions = []
        for record in result:
            data = dict(record)
            data['options'] = _parse_options(data.pop('options_json', '[]'))
            data['correct_answers'] = json.loads(_clean_cypher_json(data.pop('correct_answers_json', '[]')))
            questions.append(data)
        return questions


def get_candidate_questions(topic_id: str, answered_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch unanswered questions with IRT parameters for adaptive selection."""
    query = '''
    MATCH (t:Topic {id: $topic_id})-[:CONTAINS]->(c:Concept)-[:CONTAINS]->(q:Question)
    WHERE NOT q.id IN $answered_ids
    RETURN q.id AS id, q.stem AS stem, q.level AS level,
           q.difficulty AS b, q.discrimination AS a, q.guessing AS c,
           c.id AS concept_id
    '''
    with get_neo4j_session() as session:
        result = session.run(query, topic_id=topic_id, answered_ids=list(answered_ids))
        return [dict(r) for r in result]


def get_prerequisites(question_id: str) -> List[str]:
    """Get IDs of all prerequisite questions for a given question."""
    query = '''
    MATCH (prereq:Question)-[:IS_PREREQUISITE_FOR]->(q:Question {id: $question_id})
    RETURN prereq.id AS prereq_id
    '''
    with get_neo4j_session() as session:
        result = session.run(query, question_id=question_id)
        return [r['prereq_id'] for r in result]


def get_resources_for_concept(concept_id: str) -> List[Dict[str, Any]]:
    """Get learning resources linked to a concept."""
    query = '''
    MATCH (c:Concept {id: $concept_id})-[:LINKED_RESOURCE]->(r:Resource)
    RETURN r.id AS id, r.url AS url, r.title AS title, r.type AS type, r.level AS level
    '''
    with get_neo4j_session() as session:
        result = session.run(query, concept_id=concept_id)
        return [dict(r) for r in result]


def get_topics_for_subject(subject_id: str) -> List[Dict[str, Any]]:
    """Get all topics under a subject."""
    query = '''
    MATCH (s:Subject {id: $subject_id})-[:CONTAINS]->(t:Topic)
    RETURN t.id AS id, t.name AS name
    ORDER BY t.name
    '''
    with get_neo4j_session() as session:
        result = session.run(query, subject_id=subject_id)
        return [dict(r) for r in result]


def get_subjects() -> List[Dict[str, Any]]:
    """Get all subjects."""
    query = '''
    MATCH (s:Subject)
    RETURN s.id AS id, s.name AS name
    ORDER BY s.name
    '''
    with get_neo4j_session() as session:
        result = session.run(query)
        return [dict(r) for r in result]


def _parse_options(options_json: str) -> List[Dict[str, str]]:
    """Parse options JSON string into list of {id, text} dicts.
    
    Handles edge cases from Cypher escaping:
    - \\' (backslash-apostrophe) → just apostrophe
    - Unicode curly quotes → straight quotes
    """
    try:
        if not options_json or not isinstance(options_json, str):
            return []
        cleaned = _clean_cypher_json(options_json)
        raw = json.loads(cleaned)
        if isinstance(raw, list):
            return [
                {'id': f'opt_{i}', 'text': opt} if isinstance(opt, str) else opt
                for i, opt in enumerate(raw)
            ]
        return []
    except (json.JSONDecodeError, TypeError):
        return []
