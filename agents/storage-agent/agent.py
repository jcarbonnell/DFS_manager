# a storage agent part of the DFS manager
from nearai.agents.environment import Environment
import hashlib
import requests
from cryptography.fernet import Fernet
import base64
import os

def encrypt_file(file_data, key):
    """Encrypt file data with a symmetric key."""
    # ensure key is 32 bytes and base64-encoded for Fernet
    key_bytes = key.encode()
    if len(key_bytes) != 32:
        raise ValueError("GROUP_KEY must be 32 bytes for Fernet encryption")
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    fernet = Fernet(fernet_key)
    return fernet.encrypt(file_data)

def upload_to_ipfs(file_data, filename, env):
    """Upload encrypted file to IPFS via Pinata."""
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": env.env_vars["IPFS_API_KEY"],
        "pinata_secret_api_key": env.env_vars["IPFS_API_SECRET"]
    }
    files = {"file": (filename, file_data)}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()["IpfsHash"]
    else:
        raise Exception(f"Failed to upload to IPFS: {response.text}")

def get_file_from_directory(env, directory=".", extension=".mp3"):
    """Find the first .mp3 file in the agent's directory."""
    for file in os.listdir(directory):
        if file.lower().endswith(extension):
            file_path = os.path.join(directory, file)
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                env.add_system_log(f"Found and loaded file: {file}")
                return file, file_data
            except Exception as e:
                env.add_system_log(f"Error loading {file}: {str(e)}")
                env.add_reply(f"Failed to load {file}: {str(e)}")
                return None, None
    env.add_system_log(f"No {extension} file found in agent directory.")
    env.add_reply(f"No {extension} file found in agent directory.")
    return None, None

def run(env: Environment):
    # Enable logging if not already set
    if "DEBUG" not in env.env_vars:
        env.env_vars["DEBUG"] = "true"

    # Check messages to trigger processing
    messages = env.list_messages()
    env.add_system_log(f"Messages in thread: {messages}")
    if not messages or "process file" not in messages[-1]["content"].lower():
        env.add_reply("Please type 'process file' to start processing.")
        env.request_user_input()
        return

    # Initialize NEAR connection
    user_id = env.signer_account_id or "devbot.near"
    private_key = env.env_vars.get("NEAR_PRIVATE_KEY")
    if not private_key:
        env.add_reply("NEAR_PRIVATE_KEY not set in environment variables. Cannot interact with blockchain.")
        return
    
    try:
        near = env.set_near(user_id, private_key)
        env.add_system_log(f"NEAR initialized for account: {user_id}")
    except Exception as e:
        env.add_reply(f"Failed to initialize NEAR connection: {str(e)}")
        return
    
    # Look for an .mp3 file in the agent's directory
    filename, file_data = get_file_from_directory(env)
    if not filename or not file_data:
        return

    # encrypt the file
    try:
        group_key = env.env_vars["GROUP_KEY"]
        encrypted_data = encrypt_file(file_data, group_key)
        env.add_system_log(f"File encrypted successfully.")
    except Exception as e:
        env.add_reply(f"Failed to encrypt file: {str(e)}")
        return

    # calculate file hash of original data
    file_hash = hashlib.sha256(file_data).hexdigest()

    # upload encrypted file to IPFS
    try:
        ipfs_hash = upload_to_ipfs(encrypted_data, filename, env)
        env.add_system_log(f"Uploaded file to IPFS: {ipfs_hash}")
    except Exception as e:
        env.add_reply(f"Failed to upload file to IPFS: {str(e)}")
        return
    
    # record transaction on NEAR smart contract
    group_id = env.env_vars.get("GROUP_ID", "theosis")  # Configurable with default
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
            gas=30000000000000, # 30 Tgas
            amount=1 # 1 yoctoNEAR for payable method
        )
        if "SuccessValue" in result.status:
            trans_id = result.transaction.hash # use tx hash from blockchain
            env.add_reply(f"File {filename} uploaded to IPFS: {ipfs_hash}. Transaction ID: {trans_id}")
            env.write_file(f"{filename}.processed", b"done")  # Mark as processed
        else:
            env.add_reply(f"Transaction failed: {result.status}")
    except Exception as e:
        env.add_reply(f"Failed to record transaction on NEAR: {str(e)}")

run(env)