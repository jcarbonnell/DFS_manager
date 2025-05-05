from nearai.agents.environment import Environment
import asyncio

async def test_vector_store():
    env = Environment()
    results = await env.query_vector_store("vs_11cea753bef04e71bb3ea2ed", "create wallet")
    print(results)
asyncio.run(test_vector_store())