# An AI agent for extracting metadata from audio files and upload them on a DFS
import asyncio
import requests
from nearai.agents.environment import Environment

def run(env: Environment):
    prompt = {"role": "system", "content": "Analyse the user input and extract the metadata from the audio file."}
    result = env.completion([prompt] + env.list_messages())
    if "Audio file:" not in result:
        env.add_reply("Provide an audio file.")
        return

    #last_message = env.get_last_message()
    #env.add_reply(f"You said: {last_message['content']}")
    #last_message_text = last_message["content"]
    #if last_message_text != "Fund Me":
    #    return
    # target_account_id = "devbot.near"

    faucet_account = env.set_near("dfs_manager.devbot.near", env.env_vars["PRIVATE_ACCESS_KEY"])
    result = asyncio.run(faucet_account.call("dfs_manager.devbot.near", "fund", args={"account_id": target_account_id}))

    env.add_reply(f"You were funded! {result}")

try:
    run(env)
except Exception as e:
    env.add_reply(f"Something went wrong: {str(e)}")

env.request_user_input()