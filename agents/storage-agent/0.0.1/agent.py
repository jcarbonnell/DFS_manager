from nearai.agents.environment import Environment
import hashlib
import requests
from cryptography.fernet import Fernet

def encrypt_file(file_data, key):
    """Encrypt file data with a symmetric key."""
    # ensure key is a valid 32-byte fernet key
    fernet_key = key if len(key) == 32 else Fernet.generate_key() #use provided key or generate if invalid
    fernet = Fernet(fernet_key)
    return fernet.encrypt(file_data), fernet_key

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

def run(env: Environment):
    # check for files in the thread
    files = env.list_files_from_thread()
    env.add_system_log(f"Files in thread: {files}")
    if not files:
        env.add_reply("No files found to process.")
        return
    
    # process the first file (Adamant.mp3)
    file_obj = files[0]
    env.add_system_log(f"Processing file: {file_obj.filename}")
    file_data = env.read_file(file_obj.filename)
    filename = file_obj.filename

    # encrypt the file
    group_key = env.env_vars["GROUP_KEY"].encode() # convert hub-provided string to bytes
    encrypted_data, used_key = encrypt_file(file_data, group_key)

    # calculate file hash of original data
    file_hash = hashlib.sha256(file_data).hexdigest()

    # upload encrypted file to IPFS
    try:
        ipfs_hash = upload_to_ipfs(encrypted_data, filename, env)
    except Exception as e:
        env.add_reply(f"Failed to upload file to IPFS: {str(e)}")
        return
    
    # record transaction on NEAR smart contract
    group_id = "theosis" #hardcoded for now
    user_id = env.signer_account_id or "devbot.testnet"
    args = {
        "group_id": group_id,
        "user_id": user_id,
        "file_hash": file_hash,
        "ipfs_hash": ipfs_hash,
        "group_key": used_key.decode() # store the key used for encryption
    }
    try:
        result = env.near.call(
            contract_id=env.env_vars["CONTRACT_ID"],
            method_name="record_transaction",
            args=args,
            gas=30000000000000, # 30 Tgas
            amount=1 # 1 yoctoNEAR for payable method
        )
        # generate trans_id locally (mirrors contract logic)
        trans_id = hashlib.sha256(
            (group_id + user_id + file_hash + ipfs_hash + str(env.near.block_timestamp())).encode()
        ).hexdigest()
        env.add_reply(f"File uploaded to IPFS: {ipfs_hash}. Transaction ID: {trans_id}")
    except Exception as e:
        env.add_reply(f"Failed to record transaction on NEAR: {str(e)}")

run(env)