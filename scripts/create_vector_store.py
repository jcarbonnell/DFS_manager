import json
import openai
import nearai

# Load NEAR AI Hub configuration
config = nearai.config.load_config_file()
base_url = config.get("api_url", "https://api.near.ai/") + "v1"
auth = config["auth"]
client = openai.OpenAI(base_url=base_url, api_key=json.dumps(auth))

# Read agent descriptions
with open("agents_description.json", "r") as f:
    agents = json.load(f)

# Upload descriptions as files
file_ids = []
for agent in agents:
    file_content = json.dumps(agent).encode()
    uploaded_file = client.files.create(
        file=(f"{agent['agent_id'].split('/')[-2]}.json", file_content, "application/json"),
        purpose="assistants"
    )
    file_ids.append(uploaded_file.id)

# Create vector store
vs = client.vector_stores.create(
    name="dfs-manager-agents",
    file_ids=file_ids
)
print(f"Vector store created: {vs.id}")