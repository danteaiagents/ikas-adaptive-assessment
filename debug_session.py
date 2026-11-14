"""Debug script: run a full test session and trace every question."""
import requests
import json

BASE = "http://localhost:5001/api/v1"

# Login
r = requests.post(f"{BASE}/login", json={"email": "smoke@ikas.dev", "password": "SmokeTest123!"})
token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Start session
r = requests.post(f"{BASE}/sessions", json={"topic_id": "t-ai-llm", "preset": "quick"}, headers=headers)
sess = r.json()["data"]
sid = sess["session_id"]
print(f"Session: {sid}")
print(f"Preset: {sess['preset']}, Max Questions: {sess['total_questions']}")
print()

for i in range(1, 15):
    r = requests.get(f"{BASE}/sessions/{sid}/next", headers=headers)
    data = r.json()["data"]
    
    if data.get("complete"):
        print(f"Q{i}: SESSION COMPLETE — {data.get('message', '')}")
        break
    
    qid = data["id"]
    concept = data.get("concept_name", "?")
    level = data.get("level", "?")
    n_opts = len(data.get("options", []))
    
    print(f"Q{i}: {qid} ({concept} / {level}) — {n_opts} options")
    
    # Submit answer: always select first 3 options
    ans_resp = requests.post(f"{BASE}/sessions/{sid}/answer", json={
        "question_id": qid,
        "selected_options": ["opt_0", "opt_1", "opt_2"],
        "time_taken_seconds": 20,
    }, headers=headers)
    
    if ans_resp.status_code != 200:
        print(f"  ERROR: {ans_resp.status_code} — {ans_resp.text[:200]}")
        break
    
    ans_data = ans_resp.json()["data"]
    print(f"  → correct={ans_data['is_correct']}, score={ans_data['partial_score']:.2f}, "
          f"θ={ans_data['theta']:.3f}, SE={ans_data['theta_se']:.3f}")

print("\nDone.")
