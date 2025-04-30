# a manager agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
import json

MODEL = "llama-v3p1-70b-instruct"
VECTOR_STORE_ID = "vs_9a5a801af080432d8413dc91"

def check_auth_status(env):
    """Check if user is authorized via auth_status.json."""
    try:
        files = env.list_files_from_thread()
        auth_file = next((f for f in files if f.filename == "auth_status.json"), None)
        if auth_file:
            auth_data = json.loads(env.read_file(auth_file.filename).decode())
            env.add_system_log(f"Auth status: {auth_data}")
            return auth_data.get("authorized", False)
        return False
    except Exception as e:
        env.add_system_log(f"Error checking auth status: {str(e)}")
        return False

async def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("Manager-agent started")

    messages = env.list_messages()
    if not messages:
        env.add_reply("Hello! I can help you create a wallet, connect your wallet, mint a token, transfer a token, upload files, or extract metadata. Say 'create wallet', 'connect wallet', 'mint token', 'transfer token <receiver_id> <token_id>', 'upload a file', or 'extract metadata <filename>'.")
        env.request_user_input()
        return

    user_query = messages[-1]["content"].strip().lower()
    env.add_system_log(f"User query: {user_query}")

    # Validate file uploads
    if "upload file" in user_query:
        files = env.list_files_from_thread()
        if not files:
            env.add_reply("Please upload an .mp3 or .mp4 file to the thread first.")
            env.request_user_input()
            return

        # Check total file size (50 MB = 50,000,000 bytes)
        total_size = 0
        for file in files:
            if not file.filename.lower().endswith((".mp3", ".mp4")):
                env.add_reply("Files must be .mp3 or .mp4.")
                env.request_user_input()
                return
            try:
                # Note: Requires NEAR AI's env.get_file_size API
                file_size = env.get_file_size(file.filename)
                total_size += file_size
            except AttributeError:
                env.add_system_log("env.get_file_size not available, skipping size check")
                break  # Fallback if API is unsupported
        if total_size > 50_000_000:
            env.add_reply("Total file size must not exceed 50 MB.")
            env.request_user_input()
            return

    # Query vector store
    try:
        env.add_system_log(f"Querying vector store with ID: {VECTOR_STORE_ID}")
        vector_results = await env.query_vector_store(VECTOR_STORE_ID, user_query)
        env.add_system_log(f"Vector store results: {vector_results}")
        if not vector_results:
            env.add_reply("Sorry, I didn't understand your request. Try 'create wallet', 'connect wallet', 'mint token', 'transfer token <receiver_id> <token_id>', 'upload a file', or 'extract metadata <filename>'.")
            env.request_user_input()
            return

        top_result = vector_results[0]["chunk_text"]
        env.add_system_log(f"Top result: {top_result}")
        agent_data = json.loads(top_result)
        target_agent = agent_data["agent_id"]
        env.add_system_log(f"Selected agent: {target_agent}")
    except Exception as e:
        env.add_system_log(f"Vector store query failed: {str(e)}")
        env.add_reply(f"Error processing your request: {str(e)}. Please try again.")
        env.request_user_input()
        return

    # Check authorization for non-auth/NFT tasks
    if not any(agent in target_agent for agent in ["auth-agent", "nft-agent"]) and not check_auth_status(env):
        env.add_system_log("User not authorized, routing to auth-agent")
        target_agent = "devbot.near/auth-agent/latest"
        query = "check access"
    else:
        query = (
            "upload file" if "upload-agent" in target_agent else
            "process file" if "storage-agent" in target_agent else
            user_query if "feature-extraction-agent" in target_agent else
            user_query
        )
        env.add_system_log(f"Prepared query for {target_agent}: {query}")

    # Route to agent
    try:
        result = await env.run_agent(target_agent, query=query, thread_mode="FORK")
        env.add_system_log(f"Agent {target_agent} invoked, thread ID: {result}")
        env.add_reply(f"Your request has been sent to {target_agent.split('/')[-2]}. Check thread {result} for next steps.")
    except Exception as e:
        env.add_system_log(f"Agent invocation failed: {str(e)}")
        env.add_reply(f"Failed to process your request: {str(e)}")
        env.request_user_input()