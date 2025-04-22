from nearai.agents.environment import Environment
import json

MODEL = "llama-v3p1-70b-instruct"
VECTOR_STORE_ID = ""

def run(env: Environment):
    env.env_vars["DEBUG"] = "true"
    env.add_system_log("Manager-agent started")

    # Get user query
    messages = env.list_messages()
    if not messages:
        env.add_reply("Hello! I can help you upload or store audio files. What would you like to do? (e.g., 'upload a file', 'store a file')")
        env.request_user_input()
        return

    user_query = messages[-1]["content"].strip()
    env.add_system_log(f"User query: {user_query}")

    # Query vector store for agent routing
    try:
        vector_results = env.query_vector_store(VECTOR_STORE_ID, user_query)
        if not vector_results:
            env.add_reply("Sorry, I didn't understand your request. Try saying 'upload a file' or 'store a file'.")
            env.request_user_input()
            return

        # Parse top result
        top_result = vector_results[0]["chunk_text"]
        agent_data = json.loads(top_result)
        target_agent = agent_data["agent_id"]
        env.add_system_log(f"Routing to agent: {target_agent}")
    except Exception as e:
        env.add_system_log(f"Vector store query failed: {str(e)}")
        env.add_reply("Error processing your request. Please try again.")
        env.request_user_input()
        return

    # Prepare query for target agent
    query = "upload file" if "upload-agent" in target_agent else "process file"
    env.add_system_log(f"Prepared query for {target_agent}: {query}")

    # Route to agent
    try:
        result = env.run_agent(target_agent, query=query, thread_mode="FORK")
        env.add_system_log(f"Agent {target_agent} invoked, thread ID: {result}")
        env.add_reply(f"Your request has been sent to the appropriate agent. Thread: {result}")
    except Exception as e:
        env.add_system_log(f"Agent invocation failed: {str(e)}")
        env.add_reply(f"Failed to process your request: {str(e)}")
        env.request_user_input()

run(env)