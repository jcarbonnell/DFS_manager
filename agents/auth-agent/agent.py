from nearai.agents.environment import Environment
import json

def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("Auth-agent started")

    # Get user query
    messages = env.list_messages()
    if not messages:
        env.add_reply("Please connect your NEAR wallet or say 'check access' to verify token ownership.")
        env.request_user_input()
        return

    user_query = messages[-1]["content"].strip().lower()
    env.add_system_log(f"User query: {user_query}")

    # Handle authentication commands
    if "connect wallet" in user_query or "check access" in user_query:
        # Check wallet connection
        user_id = env.signer_account_id
        if not user_id:
            env.add_system_log("No wallet connected")
            env.add_reply("No NEAR wallet connected. Please log in with your NEAR wallet in the NEAR AI Hub or 1000fans app.")
            env.request_user_input()
            return

        env.add_system_log(f"Wallet connected: {user_id}")

        # Check token ownership
        try:
            # Use 1000fans.testnet for NFT check, fallback to devbot.near
            contract_id = env.env_vars.get("NFT_CONTRACT_ID", env.env_vars["CONTRACT_ID"])
            method_name = "nft_tokens_for_owner" if contract_id == "1000fans.testnet" else "check_token_ownership"
            args = (
                {"account_id": user_id, "from_index": None, "limit": 1}
                if method_name == "nft_tokens_for_owner"
                else {"account_id": user_id}
            )
            result = env.near.call(
                contract_id=contract_id,
                method_name=method_name,
                args=args
            )
            env.add_system_log(f"Token ownership result: {result}")
            is_authorized = (
                len(result.result) > 0 if method_name == "nft_tokens_for_owner" else result.result
            )
            auth_status = {
                "user_id": user_id,
                "authorized": is_authorized,
                "token_id": result.result[0]["token_id"] if is_authorized and method_name == "nft_tokens_for_owner" else None
            }
            env.write_file("auth_status.json", json.dumps(auth_status).encode())
            if is_authorized:
                env.add_reply(f"Access granted! Wallet {user_id} holds a valid token. You can now upload or store files.")
            else:
                env.add_reply(f"Access denied. Wallet {user_id} does not hold a valid token.")
        except Exception as e:
            env.add_system_log(f"Token ownership check failed: {str(e)}")
            env.add_reply(f"Error verifying token ownership: {str(e)}")
            env.request_user_input()
            return
    else:
        env.add_reply("Please say 'connect wallet' or 'check access' to verify your authorization.")
        env.request_user_input()

run(env)