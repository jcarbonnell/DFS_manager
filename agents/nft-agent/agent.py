# an NFT agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
import json

async def mint_token(env, user_id):
    """Mint an NFT on 1000fans.testnet."""
    try:
        private_key = env.env_vars.get("NEAR_PRIVATE_KEY") # user's key from login
        if not private_key:
            raise Exception("Missing NEAR_PRIVATE_KEY")

        near = env.set_near(user_id, private_key, rpc_addr="https://rpc.testnet.near.org")
        token_metadata = {
            "title": f"1000fans Access Token",
            "description": "Grants access to 1000fans platform",
            "copies": 1
        }
        MINT_STORAGE_COST = 6370000000000000000000 # 0.00637 NEAR
        result = await near.call(
            contract_id="1000fans.testnet",
            method_name="nft_mint",
            args={
                "token_owner_id": user_id,
                "token_metadata": token_metadata
            },
            gas=30000000000000,
            amount=MINT_STORAGE_COST,
            max_retries=3
        )
        env.add_system_log(f"Mint result: {result}")
        if "SuccessValue" in result.status:
            token = result.result  # Token object
            token_id = token["token_id"]
            env.add_reply(f"Token {token_id} minted for {user_id}.")
            return token_id
        raise Exception("Minting failed")
    except Exception as e:
        env.add_system_log(f"Mint error: {str(e)}")
        env.add_reply(f"Failed to mint token: {str(e)}")
        return None

async def transfer_token(env, user_id, receiver_id, token_id):
    """Transfer an NFT on 1000fans.testnet."""
    try:
        private_key = env.env_vars.get("ADMIN_PRIVATE_KEY")
        if not private_key:
            raise Exception("Missing ADMIN_PRIVATE_KEY")

        near = env.set_near(user_id, private_key, rpc_addr="https://rpc.testnet.near.org")
        result = await near.call(
            contract_id="1000fans.testnet",
            method_name="nft_transfer",
            args={
                "receiver_id": receiver_id,
                "token_id": token_id,
                "approval_id": None,
                "memo": "Transferred via 1000fans console"
            },
            gas=30000000000000,
            amount=1,  # 1 yoctoNEAR
            max_retries=3
        )
        env.add_system_log(f"Transfer result: {result}")
        if "SuccessValue" in result.status:
            env.add_reply(f"Token {token_id} transferred to {receiver_id}.")
            return True
        raise Exception("Transfer failed")
    except Exception as e:
        env.add_system_log(f"Transfer error: {str(e)}")
        env.add_reply(f"Failed to transfer token: {str(e)}")
        return False

async def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("NFT-agent started")

    messages = env.list_messages()
    if not messages:
        env.add_reply("Please say 'mint token' or 'transfer token <receiver_id> <token_id>'.")
        env.request_user_input()
        return

    user_query = messages[-1]["content"].strip().lower()
    env.add_system_log(f"User query: {user_query}")

    user_id = env.signer_account_id
    if not user_id:
        env.add_reply("Please connect your NEAR wallet first.")
        env.request_user_input()
        return

    if "mint token" in user_query:
        token_id = await mint_token(env, user_id)
        if token_id:
            # Update auth status
            auth_status = {
                "user_id": user_id,
                "authorized": True,
                "token_id": token_id
            }
            env.write_file("auth_status.json", json.dumps(auth_status).encode())
        env.request_user_input()
        return

    if "transfer token" in user_query:
        parts = user_query.split("transfer token")
        if len(parts) < 2 or len(parts[1].split()) < 2:
            env.add_reply("Please specify: 'transfer token <receiver_id> <token_id>'.")
            env.request_user_input()
            return
        receiver_id, token_id = parts[1].strip().split()[:2]
        await transfer_token(env, user_id, receiver_id, token_id)
        env.request_user_input()
        return

    env.add_reply("Please say 'mint token' or 'transfer token <receiver_id> <token_id>'.")
    env.request_user_input()