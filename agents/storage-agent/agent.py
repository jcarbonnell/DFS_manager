from nearai.agents.environment import Environment
import os
import requests
import hashlib
import asyncio

def upload_to_ipfs(file_data, filename, env):
    """Upload file to IPFS via Pinata."""
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": env.env_vars["IPFS_API_KEY"],
        "pinata_secret_api_key": env.env_vars["IPFS_API_SECRET"]
    }
    files = {"file": (filename, file_data)}
    try:
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            ipfs_hash = response.json()["IpfsHash"]
            env.add_system_log(f"IPFS success: {ipfs_hash}")
            return ipfs_hash
        raise Exception(f"IPFS upload failed: {response.text}")
    except Exception as e:
        env.add_system_log(f"IPFS error: {str(e)}")
        raise

def get_file_from_directory(env, directory=".", extension=".mp3"):
    """Find the first .mp3 file in the agent's directory."""
    for file in os.listdir(directory):
        if file.lower().endswith(extension):
            file_path = os.path.join(directory, file)
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                env.add_system_log(f"Loaded {file}")
                return file, file_data
            except Exception as e:
                env.add_reply(f"Failed to load {file}: {str(e)}")
                return None, None
    env.add_reply(f"No {extension} file found.")
    return None, None

def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("Agent started")

    messages = env.list_messages()
    env.add_system_log(f"Messages: {messages}")
    if not messages or "process file" not in messages[-1]["content"].lower():
        env.add_reply("Type 'process file' to start.")
        env.request_user_input()
        return

    filename, file_data = get_file_from_directory(env)
    if not filename or not file_data:
        env.add_reply("No file loaded.")
        return

    file_hash = hashlib.sha256(file_data).hexdigest()
    env.add_system_log(f"File hash: {file_hash}")

    try:
        ipfs_hash = upload_to_ipfs(file_data, filename, env)
        env.add_system_log(f"IPFS CID: {ipfs_hash}")
    except Exception as e:
        env.add_reply(f"IPFS upload failed: {str(e)}")
        return

    user_id = env.signer_account_id or "devbot.near"
    private_key = env.env_vars.get("NEAR_PRIVATE_KEY")
    if not private_key:
        env.add_reply("Missing NEAR_PRIVATE_KEY")
        return
    try:
        near = env.set_near(user_id, private_key)
        env.add_system_log(f"NEAR initialized: {user_id}")
    except Exception as e:
        env.add_reply(f"NEAR setup failed: {str(e)}")
        return

    group_id = env.env_vars.get("GROUP_ID", "theosis")
    args = {
        "group_id": group_id,
        "user_id": user_id,
        "file_hash": file_hash,
        "ipfs_hash": ipfs_hash
    }
    try:
        # Call NEAR synchronously, handle coroutine if returned
        result = near.call(
            contract_id=env.env_vars["CONTRACT_ID"],
            method_name="record_transaction",
            args=args,
            gas=30000000000000,
            amount=1
        )
        env.add_system_log(f"NEAR raw result type: {type(result)}")
        env.add_system_log(f"NEAR raw result: {result}")
        if asyncio.iscoroutine(result):
            # Run in current event loop if possible
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(result)
            env.add_system_log(f"NEAR resolved result: {result}")
        if hasattr(result, "status") and "SuccessValue" in result.status:
            trans_id = result.transaction.hash
            env.add_reply(f"Success! File {filename} uploaded to IPFS: {ipfs_hash}, Transaction ID: {trans_id}")
        else:
            env.add_reply(f"Transaction failed: {result}")
    except Exception as e:
        env.add_reply(f"NEAR call failed: {str(e)}")

run(env)