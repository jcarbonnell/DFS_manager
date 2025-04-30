# an authentication agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
from py_near.account import Account
from py_near import KeyPair
from base58 import b58encode
import json

async def create_wallet(env):
    """Generate a new NEAR wallet and create a sub-account on testnet matching the minted token ID."""
    try:
        # Generate key pair
        key_pair = KeyPair.generate_random_key_pair()
        public_key = key_pair.public_key
        private_key = key_pair.secret_key

        # mint token via nft-agent
        nft_agent_id = "devbot.near/nft-agent/latest"
        mint_query = "mint token"
        mint_result = await env.run_agent(nft_agent_id, query=mint_query, thread_mode="FORK")
        env.add_system_log(f"NFT-agent invoked for mint, thread ID: {mint_result}")

        # Fetch token_id from auth_status.json (updated by nft-agent)
        files = env.list_files_from_thread()
        auth_file = next((f for f in files if f.filename == "auth_status.json"), None)
        if not auth_file:
            raise Exception("No auth_status.json found after minting")

        auth_data = json.loads(env.read_file(auth_file.filename).decode())
        token_id = auth_data.get("token_id")
        if not token_id:
            raise Exception("No token_id found after minting")

        # Create sub-account with token_id
        account_id = f"{token_id}.1000fans.testnet"
        admin_account_id = env.env_vars.get("ADMIN_ACCOUNT_ID")
        admin_private_key = env.env_vars.get("ADMIN_PRIVATE_KEY")
        if not (admin_account_id and admin_private_key):
            raise Exception("Missing ADMIN_ACCOUNT_ID or ADMIN_PRIVATE_KEY")

        admin_acc = Account(admin_account_id, admin_private_key, rpc_addr="https://rpc.testnet.near.org")
        await admin_acc.startup()

        # Create account with initial balance (0.1 NEAR)
        initial_balance = 100000000000000000000000  # 0.1 NEAR in yoctoNEAR
        result = await admin_acc.create_account(
            account_id=account_id,
            public_key=public_key,
            initial_balance=initial_balance
        )
        env.add_system_log(f"Create account result: {result}")

        if "SuccessValue" not in result.status:
            raise Exception("Failed to create account")

        credentials = {
            "account_id": account_id,
            "public_key": public_key,
            "private_key": private_key,
            "token_id": token_id
        }
        env.write_file("wallet_credentials.json", json.dumps(credentials).encode())
        env.add_reply(f"Wallet created successfully! Account ID: {account_id}. Credentials saved in thread.")
        return account_id
    except Exception as e:
        env.add_system_log(f"Wallet creation failed: {str(e)}")
        env.add_reply(f"Error creating wallet: {str(e)}")
        return None

async def check_token_ownership(env, user_id):
    """Check if user owns an NFT on 1000fans.testnet."""
    try:
        near = env.set_near(rpc_addr="https://rpc.testnet.near.org")
        result = await near.view(
            contract_id="1000fans.testnet",
            method_name="nft_tokens_for_owner",
            args={
                "account_id": user_id,
                "from_index": None,
                "limit": 1
            },
            max_retries=3
        )
        env.add_system_log(f"Token ownership result: {result}")
        is_authorized = len(result.result) > 0
        token_id = result.result[0]["token_id"] if is_authorized else None
        return is_authorized, token_id
    except Exception as e:
        env.add_system_log(f"Token ownership check failed: {str(e)}")
        return False, None

async def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("Auth-agent started")

    # Get user query
    messages = env.list_messages()
    if not messages:
        env.add_reply("Please say 'create wallet', 'connect wallet', or 'check access' to proceed.")
        env.request_user_input()
        return

    user_query = messages[-1]["content"].strip().lower()
    env.add_system_log(f"User query: {user_query}")

    # Handle commands
    if "create wallet" in user_query:
        account_id = await create_wallet(env)
        if account_id:
            # Check token ownership after creation
            is_authorized, token_id = await check_token_ownership(env, account_id)
            auth_status = {
                "user_id": account_id,
                "authorized": is_authorized,
                "token_id": token_id
            }
            env.write_file("auth_status.json", json.dumps(auth_status).encode())
            if is_authorized:
                env.add_reply(f"Wallet {account_id} created and authorized with token {token_id}.")
            else:
                env.add_reply(f"Wallet {account_id} created but no token found. Mint a token to gain access.")
        env.request_user_input()
        return

    if "connect wallet" in user_query or "check access" in user_query:
        # Check wallet connection
        user_id = env.signer_account_id
        if not user_id:
            env.add_system_log("No wallet connected")
            env.add_reply("No NEAR wallet connected. Please log in with your NEAR wallet or create a new wallet by writing 'create wallet'.")
            env.request_user_input()
            return

        env.add_system_log(f"Wallet connected: {user_id}")

        # Check token ownership
        is_authorized, token_id = await check_token_ownership(env, user_id)
        auth_status = {
            "user_id": user_id,
            "authorized": is_authorized,
            "token_id": token_id
        }
        env.write_file("auth_status.json", json.dumps(auth_status).encode())
        if is_authorized:
            env.add_reply(f"Access granted! Wallet {user_id} holds token {token_id}.")
        else:
            env.add_reply(f"Access denied. Wallet {user_id} does not hold a token. Mint a token by writing 'mint token' to gain access.")
        env.request_user_input()
        return

    env.add_reply("Please say 'create wallet', 'connect wallet', or 'check access' to proceed.")
    env.request_user_input()