import requests
import json
import time

url_session = "http://localhost:8000/api/sessions"
url_chat = "http://localhost:8000/api/chat"

print("Creating session...")
res = requests.post(url_session)
session_data = res.json()
session_id = session_data["session_id"]
print(f"Session ID: {session_id}")

print("Sending chat 1...")
res = requests.post(url_chat, json={"session_id": session_id, "message": "I want to write a LinkedIn post about AI evaluation methods and best practices."})
print(json.dumps(res.json(), indent=2))

print("Sending chat 2...")
res = requests.post(url_chat, json={"session_id": session_id, "message": "Target audience is AI engineers. Tone should be professional, focus on model interpretability."})
print(json.dumps(res.json(), indent=2))

print("Sending chat 3...")
res = requests.post(url_chat, json={"session_id": session_id, "message": "My primary goal is establishing thought leadership. I lean towards professional, engaging, expert-level discussion with practical takeaways."})
print(json.dumps(res.json(), indent=2))
