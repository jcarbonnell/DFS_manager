from nearai.agents.environment import Environment


def run(env: Environment):
    # Your agent code here
    prompt = {"role": "system", "content": "You are a storage agent. You receive files from users or another agent, encrypt them with a group key, upload them to IPFS, ans store the resulting CID on a NEAR smart contract."}
    result = env.completion([prompt] + env.list_messages())
    env.add_reply(result)
    env.request_user_input()

run(env)

