# An AI agent managing decentralized data storage tasks for any near app.
from nearai.agents.environment import Environment

def run(env: Environment):
    prompt = '''You are an expert in data architecture, with a solid background experience in building solutions for decentralized storage with optimization for fast retrieval. You will help me manage the backend tasks of my app 1000fans.'''
    messages = {"role": "system", "content": prompt}

    result = env.completion([messages] + env.list_messages())
    env.add_reply(result)
    env.request_user_input()

run(env)