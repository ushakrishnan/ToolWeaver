"""Test if Azure CV actually works with real endpoint"""
import asyncio
import os
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

async def test():
    print(f"AZURE_CV_ENDPOINT: {os.getenv('AZURE_CV_ENDPOINT')}")
    print(f"OCR_MODE: {os.getenv('OCR_MODE')}")
    print(f"AZURE_USE_AD: {os.getenv('AZURE_USE_AD')}")
    
    # Force reimport
    import sys
    if 'orchestrator.workers' in sys.modules:
        del sys.modules['orchestrator.workers']
    
    from orchestrator.workers import receipt_ocr_worker, AZURE_CV_AVAILABLE
    
    print(f"\nAZURE_CV_AVAILABLE: {AZURE_CV_AVAILABLE}")
    
    if AZURE_CV_AVAILABLE:
        payload = {
            "image_uri": "https://images.sampletemplates.com/wp-content/uploads/2018/04/Detailed-Grocery-Payment-Receipt-Samples.jpg"
        }
        result = await receipt_ocr_worker(payload)
        print(f"\nOCR Result:")
        print(f"Text: {result['text'][:300]}...")
        print(f"Confidence: {result['confidence']}")
    else:
        print("\nAzure CV SDK not available")

asyncio.run(test())
