"""
Test script for the three improvements:
1. Better Phi3 JSON prompts with retry logic
2. JSON repair function
3. Real Azure Computer Vision integration
"""

import asyncio
import sys
import os

async def test_azure_cv():
    """Test Azure Computer Vision with real endpoint"""
    print("\n" + "="*60)
    print("Testing Azure Computer Vision Integration")
    print("="*60 + "\n")
    
    try:
        from orchestrator.workers import receipt_ocr_worker
        
        payload = {
            "image_uri": "https://images.sampletemplates.com/wp-content/uploads/2018/04/Detailed-Grocery-Payment-Receipt-Samples.jpg"
        }
        
        result = await receipt_ocr_worker(payload)
        print(f"✅ OCR Result:")
        print(f"   Text length: {len(result['text'])} characters")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Preview: {result['text'][:200]}...")
        return True
    except Exception as e:
        print(f"❌ Azure CV test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_phi3_parsing():
    """Test Phi3 with improved prompts and retry logic"""
    print("\n" + "="*60)
    print("Testing Phi3 Small Model with Improved Prompts")
    print("="*60 + "\n")
    
    try:
        from orchestrator.small_model_worker import SmallModelWorker
        
        worker = SmallModelWorker(backend="ollama", model_name="phi3")
        
        # Test with simple OCR text
        simple_text = """Coffee Shop Receipt
1x Coffee 3.50
2x Bagel 5.00
Subtotal: 8.50
Tax: 0.68
TOTAL: 9.18"""
        
        print("Parsing line items...")
        items = await worker.parse_line_items(simple_text)
        
        if items:
            print(f"✅ Successfully parsed {len(items)} items:")
            for item in items:
                print(f"   - {item['description']}: ${item['total']}")
            
            # Test categorization
            print("\nCategorizing items...")
            categorized = await worker.categorize_items(items)
            print(f"✅ Successfully categorized {len(categorized)} items:")
            for item in categorized:
                cat = item.get('category', 'unknown')
                print(f"   - {item['description']}: {cat}")
            
            return True
        else:
            print("❌ No items parsed - Phi3 still having JSON issues")
            return False
            
    except Exception as e:
        print(f"❌ Phi3 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING THREE IMPROVEMENTS")
    print("="*80)
    print("1. Better Phi3 prompts with retry logic")
    print("2. JSON repair function")
    print("3. Real Azure Computer Vision")
    print("="*80)
    
    results = {}
    
    # Test 1 & 2: Phi3 with improved prompts
    results['phi3'] = await test_phi3_parsing()
    
    # Test 3: Azure CV
    results['azure_cv'] = await test_azure_cv()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Phi3 JSON Parsing (with retry): {'✅ PASS' if results['phi3'] else '❌ FAIL'}")
    print(f"Azure Computer Vision:           {'✅ PASS' if results['azure_cv'] else '❌ FAIL'}")
    print("="*80 + "\n")
    
    if all(results.values()):
        print("🎉 All improvements working!")
        return 0
    else:
        print("⚠️  Some improvements need more work")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
