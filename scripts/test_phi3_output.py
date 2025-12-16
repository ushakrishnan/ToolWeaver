import asyncio
import sys
from orchestrator.small_model_worker import SmallModelWorker

async def test():
    worker = SmallModelWorker(backend="ollama", model_name="phi3")
    
    system = """You are a receipt line item parser. Output ONLY a valid JSON array.

RULES:
1. Output ONLY a JSON array - no explanations
2. Skip totals, subtotals, tax
3. Format: [{"description": "Coffee", "quantity": 1, "unit_price": 3.50, "total": 3.50}]"""
    
    prompt = """Receipt:
1x Coffee 3.50
2x Bagel 5.00

JSON array:"""
    
    response = await worker.generate(prompt, system, max_tokens=512, temperature=0.01)
    print("=" * 80)
    print("PHI3 RAW OUTPUT:")
    print("=" * 80)
    print(response)
    print("=" * 80)

asyncio.run(test())
