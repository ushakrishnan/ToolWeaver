"""
Planner Demo - Generate and execute plans from natural language.

This demo uses a large model (GPT-4o or Claude) to generate execution plans
from natural language requests, then executes them with the hybrid orchestrator.
"""

import asyncio
import json
import sys

from orchestrator.hybrid_dispatcher import get_registered_functions
from orchestrator.orchestrator import execute_plan, final_synthesis
from orchestrator.planner import LargePlanner


async def main():
    """Main entry point for planner demo."""

    print("\n" + "="*60)
    print("TWO-MODEL ORCHESTRATION DEMO")
    print("="*60)
    print("\nArchitecture:")
    print("  🧠 Large Model (GPT-4o/Claude) → Generates execution plans")
    print("  🤖 Small Models (Phi-3/Llama) → Executes specific tasks")
    print("  [*]  Hybrid Orchestrator → Manages execution with DAG")
    print("\n" + "="*60)

    # Get user request
    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        print("\nEnter your request (or press Enter for example):")
        user_request = input("> ").strip()

        if not user_request:
            user_request = "Process this Walmart receipt and categorize all the items by type"
            print(f"\nUsing example request: {user_request}")

    print(f"\n📝 User Request: {user_request}\n")

    # Optional context (image URL, etc.)
    context = {
        "image_url": "https://images.sampletemplates.com/wp-content/uploads/2018/04/Detailed-Grocery-Payment-Receipt-Samples.jpg"
    }

    # Initialize planner
    try:
        print("🧠 Initializing large model planner...")
        provider_choice = input("Choose provider (openai/azure-openai/anthropic/gemini) or press Enter to use .env [from .env]: ").strip().lower()
        provider = provider_choice if provider_choice else None  # None = use env variable
        planner = LargePlanner(provider=provider)
        print(f"✓ Using {planner.provider} with model {planner.model}\n")
    except Exception as e:
        print(f"\n[X] Failed to initialize planner: {e}")
        print("\nMake sure you have:")
        print("  1. Installed dependencies: pip install openai")
        print("  2. Set provider in .env: PLANNER_PROVIDER=azure-openai")
        print("  3. Set credentials in .env:")
        print("     - Azure OpenAI: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT")
        print("     - OpenAI: OPENAI_API_KEY")
        print("     - Anthropic: ANTHROPIC_API_KEY")
        print("     - Gemini: GOOGLE_API_KEY")
        return

    # Generate plan
    try:
        print("🔄 Generating execution plan...")
        plan = await planner.generate_plan(user_request, context=context)

        print("\n" + "="*60)
        print("GENERATED EXECUTION PLAN")
        print("="*60)
        print(json.dumps(plan, indent=2))
        print("="*60 + "\n")

        # Show plan summary
        print(f"Plan ID: {plan.get('request_id')}")
        print(f"Total steps: {len(plan.get('steps', []))}")

        # Show registered functions
        registered = get_registered_functions()
        print(f"Available functions: {', '.join(registered.keys()) if registered else 'none'}")

        # Ask for confirmation
        proceed = input("\n▶️  Execute this plan? (y/n) [y]: ").strip().lower()
        if proceed and proceed != 'y':
            print("Execution cancelled.")
            return

    except Exception as e:
        print(f"\n[X] Plan generation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Execute plan
    try:
        print("\n" + "="*60)
        print("EXECUTING PLAN")
        print("="*60 + "\n")

        context = await execute_plan(plan)
        synth = await final_synthesis(plan, context)

        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60 + "\n")
        print(synth['synthesis'])
        print("\n" + "="*60)

        # Show step outputs summary
        print("\n📊 Step Outputs Summary:")
        for step_id, output in context['step_outputs'].items():
            print(f"  • {step_id}: {type(output).__name__}")
            if isinstance(output, dict):
                keys = list(output.keys())[:3]
                print(f"    Keys: {', '.join(keys)}{'...' if len(output) > 3 else ''}")

        print("\n[OK] Execution completed successfully!")

    except Exception as e:
        print(f"\n[X] Plan execution failed: {e}")
        import traceback
        traceback.print_exc()

        # Try to refine plan based on error
        retry = input("\n🔄 Try to refine plan based on error? (y/n) [n]: ").strip().lower()
        if retry == 'y':
            try:
                print("\n🧠 Refining plan...")
                refined_plan = await planner.refine_plan(
                    plan,
                    feedback=f"Execution failed with error: {str(e)}"
                )

                print("\n" + "="*60)
                print("REFINED PLAN")
                print("="*60)
                print(json.dumps(refined_plan, indent=2))
                print("="*60 + "\n")

                # Execute refined plan
                context = await execute_plan(refined_plan)
                synth = await final_synthesis(refined_plan, context)

                print("\n" + "="*60)
                print("FINAL RESULTS (Refined Plan)")
                print("="*60 + "\n")
                print(synth['synthesis'])
                print("\n" + "="*60)
                print("\n[OK] Refined plan executed successfully!")

            except Exception as e2:
                print(f"\n[X] Refined plan also failed: {e2}")


if __name__ == '__main__':
    asyncio.run(main())
