"""
Tests for orchestrator.workers module

Tests worker functions: receipt_ocr_worker, line_item_parser_worker, expense_categorizer_worker
"""

import pytest
import os
from orchestrator.dispatch.workers import (
    receipt_ocr_worker,
    line_item_parser_worker,
    expense_categorizer_worker,
    _mock_ocr
)


class TestReceiptOCRWorker:
    """Tests for receipt_ocr_worker function"""
    
    @pytest.mark.asyncio
    async def test_mock_ocr_mode(self, monkeypatch):
        """Test OCR in mock mode"""
        monkeypatch.setenv("OCR_MODE", "mock")
        
        payload = {"image_uri": "https://example.com/receipt.jpg"}
        result = await receipt_ocr_worker(payload)
        
        assert "text" in result
        assert "confidence" in result
        assert "MOCK RECEIPT DATA" in result["text"]
        assert result["confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_mock_ocr_contains_receipt_data(self, monkeypatch):
        """Test that mock OCR returns realistic receipt data"""
        monkeypatch.setenv("OCR_MODE", "mock")
        
        payload = {"image_uri": "https://example.com/test.jpg"}
        result = await receipt_ocr_worker(payload)
        
        text = result["text"]
        assert "Coffee" in text
        assert "Bagel" in text
        assert "TOTAL" in text
        assert "3.50" in text
    
    @pytest.mark.asyncio
    async def test_mock_ocr_includes_image_uri(self, monkeypatch):
        """Test that mock OCR includes the image URI in response"""
        monkeypatch.setenv("OCR_MODE", "mock")
        
        image_uri = "https://example.com/my-receipt.jpg"
        payload = {"image_uri": image_uri}
        result = await receipt_ocr_worker(payload)
        
        assert image_uri in result["text"]
    
    @pytest.mark.asyncio
    async def test_azure_fallback_without_endpoint(self, monkeypatch):
        """Test that Azure mode falls back to mock when endpoint not configured"""
        monkeypatch.setenv("OCR_MODE", "azure")
        monkeypatch.delenv("AZURE_CV_ENDPOINT", raising=False)
        
        payload = {"image_uri": "https://example.com/receipt.jpg"}
        result = await receipt_ocr_worker(payload)
        
        # Should fall back to mock mode
        assert "MOCK RECEIPT DATA" in result["text"]
    
    def test_mock_ocr_direct_call(self):
        """Test _mock_ocr function directly"""
        image_uri = "https://example.com/test.jpg"
        result = _mock_ocr(image_uri)
        
        assert "text" in result
        assert "confidence" in result
        assert result["confidence"] == 0.98
        assert image_uri in result["text"]
        assert "Coffee Shop Receipt" in result["text"]


class TestLineItemParserWorker:
    """Tests for line_item_parser_worker function"""
    
    @pytest.mark.asyncio
    async def test_parse_coffee_and_bagel(self, monkeypatch):
        """Test parsing simple receipt text"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {
            "ocr_text": "Coffee Shop\n1x Coffee 3.50\n2x Bagel 5.00\nTotal: 8.50"
        }
        result = await line_item_parser_worker(payload)
        
        assert "items" in result
        items = result["items"]
        assert len(items) >= 1  # At least one item parsed
        
        # Check that coffee and bagel are found
        descriptions = [item["description"] for item in items]
        assert any("Coffee" in desc for desc in descriptions)
    
    @pytest.mark.asyncio
    async def test_parse_with_text_field(self, monkeypatch):
        """Test parsing when using 'text' field instead of 'ocr_text'"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {
            "text": "Coffee 3.50\nBagel 2.50"
        }
        result = await line_item_parser_worker(payload)
        
        assert "items" in result
        assert len(result["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_parse_empty_text(self, monkeypatch):
        """Test parsing with empty text"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {"ocr_text": ""}
        result = await line_item_parser_worker(payload)
        
        assert "items" in result
        assert isinstance(result["items"], list)
    
    @pytest.mark.asyncio
    async def test_parse_dict_input(self, monkeypatch):
        """Test parsing when ocr_text is a dict (from step reference)"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {
            "ocr_text": {
                "text": "Coffee 3.50\nBagel 5.00"
            }
        }
        result = await line_item_parser_worker(payload)
        
        assert "items" in result
    
    @pytest.mark.asyncio
    async def test_parse_skips_total_lines(self, monkeypatch):
        """Test that TOTAL lines are skipped"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {
            "ocr_text": "Coffee 3.50\nTOTAL: 3.50"
        }
        result = await line_item_parser_worker(payload)
        
        # Should have coffee but not a "total" item
        items = result["items"]
        descriptions = [item["description"].lower() for item in items]
        assert not any("total" in desc for desc in descriptions)
    
    @pytest.mark.asyncio
    async def test_parsed_items_structure(self, monkeypatch):
        """Test that parsed items have correct structure"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {
            "ocr_text": "Coffee 3.50"
        }
        result = await line_item_parser_worker(payload)
        
        if result["items"]:
            item = result["items"][0]
            assert "description" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert "total" in item


class TestExpenseCategorizerWorker:
    """Tests for expense_categorizer_worker function"""
    
    @pytest.mark.asyncio
    async def test_categorize_coffee_items(self, monkeypatch):
        """Test categorizing coffee items"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        items = [
            {"description": "Coffee", "quantity": 1, "total": 3.5}
        ]
        payload = {"items": items}
        result = await expense_categorizer_worker(payload)
        
        assert "categorized" in result
        assert len(result["categorized"]) == 1
        
        # Coffee should be categorized as beverage
        categorized_item = result["categorized"][0]
        assert "category" in categorized_item
        assert categorized_item["category"] == "beverage"
    
    @pytest.mark.asyncio
    async def test_categorize_bagel_items(self, monkeypatch):
        """Test categorizing bagel items"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        items = [
            {"description": "Bagel", "quantity": 2, "total": 5.0}
        ]
        payload = {"items": items}
        result = await expense_categorizer_worker(payload)
        
        assert "categorized" in result
        categorized_item = result["categorized"][0]
        assert categorized_item["category"] == "food"
    
    @pytest.mark.asyncio
    async def test_categorize_multiple_items(self, monkeypatch):
        """Test categorizing multiple items"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        items = [
            {"description": "Coffee", "quantity": 1, "total": 3.5},
            {"description": "Bagel", "quantity": 2, "total": 5.0}
        ]
        payload = {"items": items}
        result = await expense_categorizer_worker(payload)
        
        assert len(result["categorized"]) == 2
        
        # Check categories are assigned
        categories = [item["category"] for item in result["categorized"]]
        assert "beverage" in categories
        assert "food" in categories
    
    @pytest.mark.asyncio
    async def test_categorize_empty_items(self, monkeypatch):
        """Test categorizing with empty items list"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {"items": []}
        result = await expense_categorizer_worker(payload)
        
        assert "categorized" in result
        assert result["categorized"] == []
    
    @pytest.mark.asyncio
    async def test_categorize_dict_input(self, monkeypatch):
        """Test categorizing when items is nested in dict (from step reference)"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        payload = {
            "items": {
                "items": [
                    {"description": "Coffee", "quantity": 1, "total": 3.5}
                ]
            }
        }
        result = await expense_categorizer_worker(payload)
        
        assert "categorized" in result
    
    @pytest.mark.asyncio
    async def test_categorized_items_retain_original_fields(self, monkeypatch):
        """Test that categorized items retain original fields"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        items = [
            {"description": "Coffee", "quantity": 1, "unit_price": 3.5, "total": 3.5}
        ]
        payload = {"items": items}
        result = await expense_categorizer_worker(payload)
        
        categorized_item = result["categorized"][0]
        assert categorized_item["description"] == "Coffee"
        assert categorized_item["quantity"] == 1
        assert categorized_item["total"] == 3.5
        assert "category" in categorized_item
    
    @pytest.mark.asyncio
    async def test_default_category(self, monkeypatch):
        """Test default category for unknown items"""
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        items = [
            {"description": "Unknown Item", "quantity": 1, "total": 10.0}
        ]
        payload = {"items": items}
        result = await expense_categorizer_worker(payload)
        
        categorized_item = result["categorized"][0]
        # Should have some category (default to food)
        assert categorized_item["category"] in ["food", "beverage"]


class TestWorkerIntegration:
    """Integration tests for worker pipeline"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock_mode(self, monkeypatch):
        """Test full OCR -> Parse -> Categorize pipeline in mock mode"""
        monkeypatch.setenv("OCR_MODE", "mock")
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        # Step 1: OCR
        ocr_result = await receipt_ocr_worker({"image_uri": "https://example.com/receipt.jpg"})
        assert "text" in ocr_result
        
        # Step 2: Parse
        parse_result = await line_item_parser_worker({"ocr_text": ocr_result["text"]})
        assert "items" in parse_result
        
        # Step 3: Categorize
        if parse_result["items"]:
            categorize_result = await expense_categorizer_worker({"items": parse_result["items"]})
            assert "categorized" in categorize_result
    
    @pytest.mark.asyncio
    async def test_pipeline_with_dict_references(self, monkeypatch):
        """Test pipeline with dict-based step references"""
        monkeypatch.setenv("OCR_MODE", "mock")
        monkeypatch.setenv("USE_SMALL_MODEL", "false")
        
        # Step 1: OCR
        ocr_result = await receipt_ocr_worker({"image_uri": "https://example.com/receipt.jpg"})
        
        # Step 2: Parse with dict reference
        parse_result = await line_item_parser_worker({"ocr_text": ocr_result})
        
        # Step 3: Categorize with dict reference
        if parse_result["items"]:
            categorize_result = await expense_categorizer_worker({"items": parse_result})
            assert "categorized" in categorize_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
