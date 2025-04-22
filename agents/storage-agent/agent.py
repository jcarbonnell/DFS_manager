# a storage agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
import hashlib
import requests
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

def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("Storage-agent started")

    # Check messages
    messages = env.list_messages()
    env.add_system_log(f"Messages: {messages}")
    if not messages or "process file" not in messages[-1]["content"].lower():
        env.add_system_log("No 'process file' command: prompting user")
        env.add_reply("Type 'process file' to store the .mp3 file.")
        env.request_user_input()
        return

    # Get file from thread (passed by upload-agent or uploaded manually)
    files = env.list_files_from_thread()
    env.add_system_log(f"Files in thread: {files}")
    if not files:
        env.add_reply("No file found in thread.")
        env.request_user_input()
        return

    file_obj = files[0]
    if not file_obj.filename.lower().endswith(".mp3"):
        env.add_reply("File must be an .mp3.")
        env.request_user_input()
        return

    env.add_system_log(f"Processing file: {file_obj.filename}")
    file_data = env.read_file(file_obj.filename)
    filename = file_obj.filename

    # Calculate file hash
    file_hash = hashlib.sha256(file_data).hexdigest()
    env.add_system_log(f"File hash: {file_hash}")

    # Upload to IPFS
    try:
        ipfs_hash = upload_to_ipfs(file_data, filename, env)
        env.add_system_log(f"IPFS CID: {ipfs_hash}")
    except Exception as e:
        env.add_reply(f"IPFS upload failed: {str(e)}")
        env.request_user_input()
        return

    # NEAR setup
    user_id = env.signer_account_id or "devbot.near"
    private_key = env.env_vars.get("NEAR_PRIVATE_KEY")
    if not private_key:
        env.add_reply("Missing NEAR_PRIVATE_KEY")
        env.request_user_input()
        return
    try:
        near = env.set_near(user_id, private_key)
        env.add_system_log(f"NEAR initialized: {user_id}")
    except Exception as e:
        env.add_reply(f"NEAR setup failed: {str(e)}")
        env.request_user_input()
        return

    # record transaction on NEAR
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
    env.request_user_input()

run(env)