# a manager agent part of the DFS manager team of agents
from nearai.agents.environment import Environment

def run(env: Environment):
    env.add_system_log("Manager-agent: Starting agent")
    env.env_vars["DEBUG"] = "true"

    try:
        # Fetch messages
        env.add_system_log("Manager-agent: Fetching messages")
        messages = env.list_messages()

        # Handle no messages
        if not messages:
            env.add_system_log("Manager-agent: No messages, sending welcome reply")
            env.add_reply(
                "Hi! 👋 Welcome to 1000fans! 1000fans is a private content platform used by Theosis to provide its fans with exclusive content.\n\n"
                "To access the artist's private music and videos, you must connect a crypto wallet. To connect your wallet, type 'connect wallet'.\n\n"
                "If you do not have a wallet yet and want to create one, type 'create wallet'.\n\n"
                "You can also access the artist's music on the usual media platforms by saying 'spotify' or 'youtube',\n\n"
                "and you can contact Theosis directly by saying 'contact'."
            )
            env.request_user_input()
            return

        # Get user query
        user_query = messages[-1]["content"].strip().lower()
        env.add_system_log(f"Manager-agent: User query: {user_query}")

        # Handle greetings explicitly
        greetings = ["hi", "hello", "hey", "hola"]
        if any(greeting in user_query for greeting in greetings):
            env.add_system_log("Manager-agent: Handling greeting")
            env.add_reply(
                "Hi! 👋 Welcome to 1000fans! 1000fans is a private content platform used by Theosis to provide its fans with exclusive content.\n\n"
                "You can access the artist's music on media platforms by saying 'spotify' or 'youtube', or contact the artist directly by saying 'contact'.\n\n"
                "To access the artist's private music and videos, you must connect a crypto wallet. To connect your wallet, type 'connect wallet'.\n\n"
                "If you do not have a wallet yet and want to create one, type 'create wallet'.\n\n"
                "Type 'list' to see all available commands.\n\n"
            )
            env.request_user_input()
            return

        # Handle static commands
        if "spotify" in user_query:
            env.add_system_log("Manager-agent: Handling spotify request")
            env.add_reply("Check out Theosis on Spotify: https://open.spotify.com/artist/1ljniIS7mEd0z1zOE6MEL0")
            env.request_user_input()
            return
        if "youtube" in user_query:
            env.add_system_log("Manager-agent: Handling youtube request")
            env.add_reply("Watch Theosis on YouTube: https://www.youtube.com/@TheosisRecords")
            env.request_user_input()
            return
        if "contact" in user_query:
            env.add_system_log("Manager-agent: Handling contact request")
            env.add_reply("Contact Theosis directly on WhatsApp +33617982358 or Twitter: @jcarbonnell")
            env.request_user_input()
            return
        if "list" in user_query:
            env.add_system_log("Manager-agent: Handling list request")
            env.add_reply(
                "Available commands:\n"
                "- 'spotify': Access Theosis music on Spotify.\n"
                "- 'youtube': Watch Theosis videos on YouTube.\n"
                "- 'contact': Get info to contact Theosis.\n"
                "- 'connect wallet': Connect your NEAR wallet to access exclusive content on 1000fans.\n"
                "- 'create wallet': Create a NEAR wallet if you don't have one yet.\n"
                "- 'mint token': Get your access token sent to your wallet.\n"
                "- 'transfer token': Transfer or sell your limited fans token.\n"
                "Type any command to proceed!"
            )
            env.request_user_input()
            return

        # Fallback to LLM completion for other inputs
        env.add_system_log("Manager-agent: Processing with LLM completion")
        prompt = {
            "role": "system",
            "content": (
                "You are in charge for interacting with users in a friendly human language and route tasks to dedicated agents from the DFS manager team of s."
            )
        }
        result = env.completion([prompt] + [{"role": "user", "content": user_query}])
        env.add_reply(result)
        env.request_user_input()

    except Exception as e:
        env.add_system_log(f"Manager-agent: Unexpected error: {str(e)}")
        env.add_reply(f"Error: {str(e)}")
        env.request_user_input()

run(env)