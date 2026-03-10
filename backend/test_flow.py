from swarm_flow import ViralFlow
import asyncio

async def test_flow():
    try:
        flow = ViralFlow()
        flow.state.mode = "commando"
        flow.state.run_type = "matin"
        # Dummy config
        flow.state.agent_config = {}
        print("Kicking off test flow...")
        result = await flow.kickoff_async() # Flows are usually async in newer crewai versions
        print(f"Result: {result}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_flow())
