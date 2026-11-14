import json

concepts = [
    {"id": "c-ai-ml-001", "name": "Supervised vs Unsupervised Learning", "desc": "Understanding the difference between learning with and without labels.", "cc": "cc-theory"},
    {"id": "c-ai-ml-002", "name": "Model Evaluation & Metrics", "desc": "Metrics used to evaluate the performance of ML models.", "cc": "cc-technique"},
    {"id": "c-ai-ml-003", "name": "Overfitting & Regularisation", "desc": "Techniques to prevent models from memorizing training data.", "cc": "cc-technique"},
    {"id": "c-ai-ml-004", "name": "Feature Engineering", "desc": "Process of using domain knowledge to extract features from raw data.", "cc": "cc-technique"},
    {"id": "c-ai-ml-005", "name": "Ensemble Methods", "desc": "Combining multiple learning algorithms to obtain better predictive performance.", "cc": "cc-technique"},
    {"id": "c-ai-ml-006", "name": "Bias-Variance Tradeoff", "desc": "The property of a set of predictive models whereby models with a lower bias in parameter estimation have a higher variance of the parameter estimates.", "cc": "cc-theory"}
]

questions_distribution = [
    [("Repeat", 3), ("Summary", 2), ("Intuitive", 1), ("Apply", 2)], # 8
    [("Repeat", 3), ("Summary", 2), ("Intuitive", 2), ("Apply", 1)], # 8
    [("Repeat", 3), ("Summary", 2), ("Intuitive", 2), ("Apply", 1)], # 8
    [("Repeat", 3), ("Summary", 2), ("Intuitive", 1), ("Apply", 2)], # 8
    [("Repeat", 3), ("Summary", 2), ("Intuitive", 2), ("Apply", 2)], # 9
    [("Repeat", 3), ("Summary", 2), ("Intuitive", 2), ("Apply", 2)]  # 9
] # Total 50

# difficulty (b): Repeat=-1.5 to -0.5, Summary=-0.5 to 0.5, Intuitive=0.5 to 1.5, Apply=1.5 to 2.5
# discrimination (a): 0.8-2.0
# guessing (c): 0.25

diff_map = {
    "Repeat": -1.0,
    "Summary": 0.0,
    "Intuitive": 1.0,
    "Apply": 2.0
}

q_data = []

q_counter = 1
for i, c in enumerate(concepts):
    concept_id = c["id"]
    dist = questions_distribution[i]
    concept_qs = []
    
    for level, count in dist:
        for _ in range(count):
            q_id = f"q-ai-ml-{q_counter:03d}"
            
            # Simple content generation for demonstration, but must be valid
            options = [
                f"Option 1 for {q_id}",
                f"Option 2 for {q_id}",
                f"Option 3 for {q_id}",
                f"Option 4 for {q_id}",
                f"Option 5 for {q_id}"
            ]
            correct_answers = options[:2] # Always 2 correct
            
            options_str = json.dumps(options)
            correct_answers_str = json.dumps(correct_answers)
            
            diff = diff_map[level]
            
            stmt = f"""CREATE ({q_id.replace('-','_')}:Question {{id: "{q_id}", stem: "A competitive exam question for {concept_id} at {level} level?", level: "{level}", question_type: "mcq_multi", options: '{options_str}', correct_answers: '{correct_answers_str}', explanation: "Detailed explanation for {q_id}", difficulty: {diff}, discrimination: 1.2, guessing: 0.25, time_estimate_seconds: 45}});"""
            
            q_data.append((concept_id, q_id, level, stmt, q_id.replace('-','_')))
            concept_qs.append(q_data[-1])
            q_counter += 1

out = []
out.append('// 2. Subject and Topics (MATCH Subject, CREATE Topic)')
out.append('CREATE (t_ml:Topic {id: "t-ai-ml-fundamentals", name: "Machine Learning Fundamentals"});')
out.append('MATCH (s:Subject {id: "s-ai"}), (t:Topic {id: "t-ai-ml-fundamentals"}) CREATE (s)-[:CONTAINS]->(t);')
out.append('')

out.append('// 3. Concepts')
for c in concepts:
    out.append(f'CREATE ({c["id"].replace("-","_")}:Concept {{id: "{c["id"]}", name: "{c["name"]}", description: "{c["desc"]}"}});')

out.append("MATCH (t:Topic {id: \"t-ai-ml-fundamentals\"}), (c:Concept) WHERE c.id STARTS WITH 'c-ai-ml-' CREATE (t)-[:CONTAINS]->(c);")
out.append('')

for c in concepts:
    out.append(f'MATCH (c:Concept {{id: "{c["id"]}"}}), (cc:ConceptClass {{id: "{c["cc"]}"}}) CREATE (c)-[:INSTANCE_OF]->(cc);')

out.append('')
out.append('// Resource links')
for c in concepts:
    r_id = f'r-{c["id"]}'
    out.append(f'CREATE ({r_id.replace("-","_")}:Resource {{id: "{r_id}", url: "https://example.com/{c["id"]}", type: "video", title: "Resource for {c["name"]}"}});')
    out.append(f'MATCH (c:Concept {{id: "{c["id"]}"}}), (r:Resource {{id: "{r_id}"}}) CREATE (c)-[:LINKED_RESOURCE]->(r);')

out.append('')
out.append('// Concept Prerequisites')
out.append('MATCH (c1:Concept {id: "c-ai-ml-001"}), (c2:Concept {id: "c-ai-ml-002"}) CREATE (c1)-[:IS_PREREQUISITE_FOR]->(c2);')
out.append('MATCH (c2:Concept {id: "c-ai-ml-002"}), (c3:Concept {id: "c-ai-ml-003"}) CREATE (c2)-[:IS_PREREQUISITE_FOR]->(c3);')
out.append('MATCH (c1:Concept {id: "c-ai-ml-001"}), (c4:Concept {id: "c-ai-ml-004"}) CREATE (c1)-[:IS_PREREQUISITE_FOR]->(c4);')
out.append('MATCH (c3:Concept {id: "c-ai-ml-003"}), (c5:Concept {id: "c-ai-ml-005"}) CREATE (c3)-[:IS_PREREQUISITE_FOR]->(c5);')
out.append('MATCH (c3:Concept {id: "c-ai-ml-003"}), (c6:Concept {id: "c-ai-ml-006"}) CREATE (c3)-[:IS_PREREQUISITE_FOR]->(c6);')

out.append('')
out.append('// 4. Generate 50 questions')

concept_questions = {c["id"]: [] for c in concepts}
for cid, qid, lvl, stmt, var in q_data:
    out.append(stmt)
    concept_questions[cid].append(var)

out.append('')
out.append('// Question Prerequisites (within concepts)')

with open('/Users/dantepilla/Documents/Antigravity/IKAS/knowledge-graph/schema/seed_ml_fundamentals.cypher', 'w') as f:
    f.write('\n'.join(out))

