import requests
import json
import os

auth = json.load(open(os.path.expanduser("~/.nearai/config.json")))["auth"]
headers = {"Authorization": f"Bearer {json.dumps(auth)}", "Content-Type": "multipart/form-data"}
files = {"file": open("/Users/juliencarbonnell/Desktop/VAD1KickHard001.wav", "rb")}
data = {"agent_id": "devbot.near/storage-agent/0.0.5", "new_message": "Process this file"}
response = requests.post("https://api.near.ai/v1/threads/runs", headers=headers, files=files, data=data)
thread_id = response.text.strip('"')
print(f"Thread ID: {thread_id}")