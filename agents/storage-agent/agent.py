# a storage agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
import hashlib
import requests
import asyncio
import os

def get_file_from_directory(env, directory=".", extension=".mp3"):
    """Fallback: Verify the first .mp3 file in the registry."""
    env.add_system_log(f"get_file_from_directory: starting in {directory}")
    try:
        files = os.listdir(directory)
        env.add_system_log(f"get_file_from_directory: found files {files}")
        for file in files:
            env.add_system_log(f"get_file_from_directory: checking file {file}")
            if file.lower().endswith(extension):
                file_path = os.path.join(directory, file)
                env.add_system_log(f"get_file_from_directory: found {file_path}")
                return file, file_path
        env.add_system_log(f"get_file_from_directory: no {extension} file found")
        return None, None
    except Exception as e:
        env.add_system_log(f"get_file_from_directory: error - {str(e)}")
        return None, None

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

    # Get query
    query = messages[-1]["content"].strip().lower() if messages else ""
    env.add_system_log(f"Query: {query}")

    # Get file from thread
    files = env.list_files_from_thread()
    env.add_system_log(f"Files in thread: {files}")

    # Use filename from query if provided
    filename = None
    if "process file" in query:
        parts = query.split("process file")
        if len(parts) > 1 and parts[1].strip():
            filename = parts[1].strip()
            env.add_system_log(f"Filename from query: {filename}")

    # Select file
    file_data = None
    if files:
        file_obj = next((f for f in files if f.filename == filename), files[0])
        if not file_obj.filename.lower().endswith(".mp3"):
            env.add_reply("File must be an .mp3.")
            env.request_user_input()
            return
        filename = file_obj.filename
        env.add_system_log(f"Processing thread file: {filename}")
        try:
            file_data = env.read_file(filename)
            env.add_system_log(f"File read successfully: {filename}, size: {len(file_data)} bytes")
        except Exception as e:
            env.add_system_log(f"Error reading thread file: {str(e)}")
            env.add_reply(f"Failed to read thread file: {str(e)}")
            env.request_user_input()
            return
    else:
        env.add_system_log("No files in thread, falling back to registry")
        # Fallback to registry
        directories = [".", os.path.dirname(__file__), "/app"]
        for directory in directories:
            filename, file_path = get_file_from_directory(env, directory)
            if filename:
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    env.add_system_log(f"Read registry file: {filename}, size: {len(file_data)} bytes")
                    break
                except Exception as e:
                    env.add_system_log(f"Error reading registry file: {str(e)}")
                    env.add_reply(f"Failed to read registry file: {str(e)}")
                    env.request_user_input()
                    return
        if not file_data:
            env.add_reply("No .mp3 file found in thread or registry.")
            env.request_user_input()
            return

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
        near = env.set_near(user_id, private_key, rpc_addr="https://rpc.mainnet.near.org")
        env.add_system_log(f"NEAR initialized: {user_id}")
    except Exception as e:
        env.add_reply(f"NEAR setup failed: {str(e)}")
        env.request_user_input()
        return

    # Record transaction on NEAR
    group_id = env.env_vars.get("GROUP_ID", "theosis")
    args = {
        "group_id": group_id,
        "user_id": user_id,
        "file_hash": file_hash,
        "ipfs_hash": ipfs_hash
    }
    try:
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