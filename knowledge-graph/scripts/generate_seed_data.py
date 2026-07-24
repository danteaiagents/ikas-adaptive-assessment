import json
import random
import uuid

def generate_cypher():
    cypher = []
    
    # 1. Concept Classes
    classes = ["Technique", "Tool", "Theory", "Framework", "Architecture", "Methodology"]
    for c in classes:
        cypher.append(f'CREATE (:ConceptClass {{id: "cc-{c.lower()}", uri: "ikas:{c}", label: "{c}"}});')
        
    # 2. Subject and Topics
    cypher.append('CREATE (s:Subject {id: "s-ai", name: "Artificial Intelligence"});')
    topics = [
        ("t-ai-llm", "LLMs & Prompting"),
        ("t-ai-agents", "AI Agents & Orchestration"),
        ("t-ai-tools", "AI Tools & Frameworks"),
        ("t-ai-rag", "RAG")
    ]
    for tid, tname in topics:
        cypher.append(f'CREATE (t:Topic {{id: "{tid}", name: "{tname}"}});')
        cypher.append(f'MATCH (s:Subject {{id: "s-ai"}}), (t:Topic {{id: "{tid}"}}) CREATE (s)-[:CONTAINS]->(t);')

    # 3. Concepts for LLMs & Prompting (we need questions for this topic)
    concepts = [
        ("c-ai-llm-001", "What is an LLM", "Understanding the basics of Large Language Models.", "Theory"),
        ("c-ai-llm-002", "Tokenization", "How text is converted into tokens for processing.", "Technique"),
        ("c-ai-llm-003", "Prompt Engineering", "Techniques for crafting effective prompts.", "Technique"),
        ("c-ai-llm-004", "Few-shot / Zero-shot Learning", "Guiding models with examples.", "Technique"),
        ("c-ai-llm-005", "Temperature & Sampling", "Controlling randomness and output diversity.", "Technique"),
        ("c-ai-llm-006", "Context Windows", "Understanding the limits of input text size.", "Architecture")
    ]
    
    for cid, cname, cdesc, cclass in concepts:
        cypher.append(f'CREATE (c:Concept {{id: "{cid}", name: "{cname}", description: "{cdesc}"}});')
        cypher.append(f'MATCH (t:Topic {{id: "t-ai-llm"}}), (c:Concept {{id: "{cid}"}}) CREATE (t)-[:CONTAINS]->(c);')
        cypher.append(f'MATCH (c:Concept {{id: "{cid}"}}), (cc:ConceptClass {{id: "cc-{cclass.lower()}"}}) CREATE (c)-[:INSTANCE_OF]->(cc);')
        
        # Resource link
        rid = f"r-{cid}"
        cypher.append(f'CREATE (r:Resource {{id: "{rid}", url: "https://www.youtube.com/watch?v=zjkBMFhNj_g", type: "video", title: "Introduction to {cname}"}});')
        cypher.append(f'MATCH (c:Concept {{id: "{cid}"}}), (r:Resource {{id: "{rid}"}}) CREATE (c)-[:LINKED_RESOURCE]->(r);')

    # 4. Generate 50 questions across 4 levels for these 6 concepts
    # Distribution: 15 Repeat, 15 Summary, 10 Intuitive, 10 Apply = 50 total
    
    levels = {
        "Repeat": {"count": 15, "diff": -1.0},
        "Summary": {"count": 15, "diff": 0.0},
        "Intuitive": {"count": 10, "diff": 1.0},
        "Apply": {"count": 10, "diff": 2.0}
    }
    
    questions = []
    q_counter = 1
    
    for level, params in levels.items():
        for _ in range(params["count"]):
            cid = random.choice(concepts)[0]
            qid = f"q-ai-llm-{q_counter:03d}"
            q_counter += 1
            
            stem = f"Sample {level} question for {cid}."
            options = ["Option A", "Option B", "Option C", "Option D", "Option E"]
            correct = ["Option A", "Option B"]
            explanation = "Explanation for this question."
            
            q_props = f"""id: "{qid}", stem: "{stem}", level: "{level}", question_type: "mcq_multi", options: {json.dumps(options)}, correct_answers: {json.dumps(correct)}, explanation: "{explanation}", difficulty: {params["diff"]}, discrimination: 1.0, guessing: 0.25, time_estimate_seconds: 60"""
            
            cypher.append(f"CREATE (q:Question {{{q_props}}});")
            cypher.append(f'MATCH (c:Concept {{id: "{cid}"}}), (q:Question {{id: "{qid}"}}) CREATE (c)-[:CONTAINS]->(q);')
            questions.append({"id": qid, "level": level, "concept": cid})

    # Create prerequisites (simple chain: Repeat -> Summary -> Intuitive -> Apply within same concept)
    for q in questions:
        if q["level"] in ["Summary", "Intuitive", "Apply"]:
            # Find a lower level question for the same concept
            lower_levels = []
            if q["level"] == "Summary": lower_levels = ["Repeat"]
            if q["level"] == "Intuitive": lower_levels = ["Summary", "Repeat"]
            if q["level"] == "Apply": lower_levels = ["Intuitive", "Summary"]
            
            prereqs = [pq for pq in questions if pq["concept"] == q["concept"] and pq["level"] in lower_levels]
            if prereqs:
                prereq = random.choice(prereqs)
                cypher.append(f'MATCH (q1:Question {{id: "{prereq["id"]}"}}), (q2:Question {{id: "{q["id"]}"}}) CREATE (q1)-[:IS_PREREQUISITE_FOR {{p_pass_given_pass: 0.8, p_pass_given_fail: 0.2}}]->(q2);')

    with open('/Users/dantepilla/Documents/Antigravity/IKAS/knowledge-graph/schema/seed_data.cypher', 'w') as f:
        f.write('\\n'.join(cypher))

if __name__ == "__main__":
    generate_cypher()
