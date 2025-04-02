from nearai.agents.environment import Environment


def run(env: Environment):
    # Your agent code here
    prompt = {"role": "system", "content": "Encrypt files, upload to IPFS, and store the CID in a NEAR smart contract."}
    result = env.completion([prompt] + env.list_messages())
    env.add_reply(result)
    env.request_user_input()

run(env)