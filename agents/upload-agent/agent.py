# an upload agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
import os
import sys

def get_file_from_directory(env, directory=".", extension=".mp3"):
    """Verify the first .mp3 file exists in the agent's directory without reading it."""
    env.add_system_log(f"get_file_from_directory: starting in {directory}")
    try:
        files = os.listdir(directory)
        env.add_system_log(f"get_file_from_directory: found files {files}")
        for file in files:
            env.add_system_log(f"get_file_from_directory: checking file {file}")
            if file.lower().endswith(extension):
                file_path = os.path.join(directory, file)
                env.add_system_log(f"get_file_from_directory: found {file_path}")
                return file, None  # Return filename only, no data
        env.add_system_log(f"get_file_from_directory: no {extension} file found")
        env.add_reply(f"No {extension} file found in agent folder.")
        return None, None
    except Exception as e:
        env.add_system_log(f"get_file_from_directory: error - {str(e)}")
        env.add_reply(f"Error accessing directory {directory}: {str(e)}")
        return None, None

def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log(f"Upload-agent started: Python {sys.version}, CWD {os.getcwd()}")
    env.add_system_log(f"Environment variables: {env.env_vars}")

    messages = env.list_messages()
    env.add_system_log(f"Messages received: {messages}")

    if not messages:
        env.add_system_log("No messages: prompting user")
        env.add_reply("Type 'upload file' to process test.mp3.")
        env.request_user_input()
        return

    last_message = messages[-1]["content"].strip().lower()
    env.add_system_log(f"Processing last message: '{last_message}'")

    if "upload file" in last_message:
        env.add_system_log("Received 'upload file': verifying file")
        # Verify test.mp3 exists, like storage-agent
        directories = [
            ".",  # Current working directory
            os.path.dirname(__file__),  # Script directory
            "/app"  # Common Hub runtime root
        ]
        filename, _ = None, None
        for directory in directories:
            env.add_system_log(f"Trying directory: {directory}")
            filename, _ = get_file_from_directory(env, directory)
            if filename:
                break
        if not filename:
            env.add_system_log("File verification failed")
            env.request_user_input()
            return
        env.add_system_log(f"Verified {filename}: invoking storage-agent")
        try:
            storage_agent_id = "devbot.near/storage-agent/latest"
            query = f"process file {filename}"
            thread_mode = "FORK"  # New thread to avoid state conflicts
            result = env.run_agent(storage_agent_id, query=query, thread_mode=thread_mode)
            env.add_system_log(f"Storage-agent invoked successfully, thread ID: {result}")
            env.add_reply(f"File {filename} sent to storage-agent for processing. Thread: {result}")
        except Exception as e:
            env.add_system_log(f"Storage-agent invocation failed: {str(e)}")
            env.add_reply(f"Failed to invoke storage-agent: {str(e)}")
        env.request_user_input()
        return

    env.add_system_log(f"Unrecognized message '{last_message}': prompting user")
    env.add_reply("Please type 'upload file' to process test.mp3.")
    env.request_user_input()

run(env)