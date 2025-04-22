# an upload agent part of the DFS manager team of agents
from nearai.agents.environment import Environment
import os

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
    env.add_system_log("Upload-agent started: initializing")

    # Check messages
    messages = env.list_messages()
    env.add_system_log(f"Messages received: {messages}")

    if not messages:
        env.add_system_log("No messages found: prompting user")
        env.add_reply("Type 'upload file' to start.")
        env.request_user_input()
        return

    last_message = messages[-1]["content"].strip().lower()
    env.add_system_log(f"Processing last message: '{last_message}'")

    # Handle "upload file"
    if last_message == "upload file":
        env.add_system_log("Received 'upload file': verifying file")
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
            env.add_reply("No .mp3 file found. Type 'upload file' to start.")
            env.request_user_input()
            return

        env.add_system_log("Received 'upload file': prompting for confirmation")
        env.add_reply(f"Ready to process file {filename}. Send to storage? (Type 'yes' or 'no') [filename:{filename}]")
        env.request_user_input()
        return

    # Handle confirmation
    if last_message in ["yes", "no"]:
        env.add_system_log(f"Received confirmation: {last_message}")

        # Extract filename from previous message
        filename = None
        for msg in reversed(messages):
            if "filename:" in msg["content"]:
                try:
                    filename = msg["content"].split("filename:")[1].split("]")[0]
                    env.add_system_log(f"Retrieved filename: {filename}")
                    break
                except IndexError:
                    env.add_system_log("Failed to parse filename from message")
                    break
        if not filename:
            env.add_system_log("No verified file found in message history")
            env.add_reply("No file verified. Type 'upload file' to start.")
            env.request_user_input()
            return

        if last_message == "no":
            env.add_system_log("User chose 'no': cancelling")
            env.add_reply("Operation cancelled. Type 'upload file' to start again.")
            env.request_user_input()
            return

        # Proceed to storage-agent (yes)
        env.add_system_log("Attempting to invoke storage-agent")
        try:
            storage_agent_id = "devbot.near/storage-agent/latest"
            query = "process file"
            thread_mode = "FORK"
            result = env.run_agent(storage_agent_id, query=query, thread_mode=thread_mode)
            env.add_system_log(f"Storage-agent invoked successfully, thread ID: {result}")
            env.add_reply(f"File {filename} sent to storage-agent. Thread: {result}")
        except Exception as e:
            env.add_system_log(f"Storage-agent invocation failed: {str(e)}")
            env.add_reply(f"Failed to invoke storage-agent: {str(e)}")
        env.request_user_input()
        return

    # Unexpected input
    env.add_system_log("Unexpected message: prompting user")
    env.add_reply("Please type 'upload file' to start, or 'yes'/'no' to confirm.")
    env.request_user_input()

run(env)