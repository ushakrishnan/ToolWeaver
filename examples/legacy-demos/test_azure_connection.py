"""
Quick test to verify Azure OpenAI connection with Azure AD authentication
"""
import asyncio
from orchestrator.planner import LargePlanner


async def test_connection():
    print("Initializing LargePlanner with Azure OpenAI...")
    
    # Use async context manager for automatic cleanup
    async with LargePlanner(provider="azure-openai") as planner:
        print(f"✓ Planner initialized")
        print(f"  Provider: {planner.provider}")
        print(f"  Model: {planner.model}")
        
        print("\nGenerating test plan...")
        try:
            plan = await planner.generate_plan(
                "Process a receipt and calculate the total with tax",
                context={"image_url": "https://raw.githubusercontent.com/microsoft/VisualStudioCode-MachineLearning/main/sample-images/receipt-sample.jpg"}
            )
            
            print("✓ Connection successful!")
            print(f"\nGenerated plan with {len(plan.get('steps', []))} steps:")
            for i, step in enumerate(plan.get('steps', []), 1):
                print(f"  {i}. {step.get('tool')} - {step.get('id')}")
            
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
