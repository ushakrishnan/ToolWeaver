"""
Tests for orchestrator.functions module

Tests utility functions like compute_tax, apply_discount, filter_items, etc.
"""

import pytest
from orchestrator._internal.dispatch.functions import (
    compute_tax,
    apply_discount,
    merge_items,
    filter_items_by_category,
    compute_item_statistics
)


class TestComputeTax:
    """Tests for compute_tax function"""
    
    def test_basic_tax_calculation(self):
        """Test basic tax calculation"""
        result = compute_tax(amount=100.0, tax_rate=0.07)
        assert result == 7.0
    
    def test_default_tax_rate(self):
        """Test with default tax rate"""
        result = compute_tax(amount=100.0)
        assert result == 7.0  # Default is 0.07
    
    def test_zero_amount(self):
        """Test with zero amount"""
        result = compute_tax(amount=0.0, tax_rate=0.07)
        assert result == 0.0
    
    def test_high_tax_rate(self):
        """Test with high tax rate"""
        result = compute_tax(amount=100.0, tax_rate=0.25)
        assert result == 25.0
    
    def test_rounding(self):
        """Test rounding to 2 decimal places"""
        result = compute_tax(amount=10.33, tax_rate=0.07)
        assert result == 0.72  # 10.33 * 0.07 = 0.7231 -> 0.72
    
    def test_negative_amount_raises_error(self):
        """Test that negative amount raises ValueError"""
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            compute_tax(amount=-100.0, tax_rate=0.07)
    
    def test_invalid_tax_rate_negative(self):
        """Test that negative tax rate raises ValueError"""
        with pytest.raises(ValueError, match="Tax rate must be between 0 and 1"):
            compute_tax(amount=100.0, tax_rate=-0.05)
    
    def test_invalid_tax_rate_over_one(self):
        """Test that tax rate > 1 raises ValueError"""
        with pytest.raises(ValueError, match="Tax rate must be between 0 and 1"):
            compute_tax(amount=100.0, tax_rate=1.5)


class TestApplyDiscount:
    """Tests for apply_discount function"""
    
    def test_basic_discount(self):
        """Test basic discount application"""
        result = apply_discount(amount=100.0, discount_percent=10.0)
        assert result == {
            "original": 100.0,
            "discount": 10.0,
            "final": 90.0
        }
    
    def test_no_discount(self):
        """Test with 0% discount"""
        result = apply_discount(amount=100.0, discount_percent=0.0)
        assert result == {
            "original": 100.0,
            "discount": 0.0,
            "final": 100.0
        }
    
    def test_full_discount(self):
        """Test with 100% discount"""
        result = apply_discount(amount=100.0, discount_percent=100.0)
        assert result == {
            "original": 100.0,
            "discount": 100.0,
            "final": 0.0
        }
    
    def test_fractional_discount(self):
        """Test with fractional discount percentage"""
        result = apply_discount(amount=100.0, discount_percent=15.5)
        assert result["discount"] == 15.5
        assert result["final"] == 84.5
    
    def test_rounding(self):
        """Test rounding to 2 decimal places"""
        result = apply_discount(amount=10.33, discount_percent=7.5)
        assert result["discount"] == 0.77  # 10.33 * 0.075 = 0.77475 -> 0.77
        assert result["final"] == 9.56
    
    def test_negative_amount_raises_error(self):
        """Test that negative amount raises ValueError"""
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            apply_discount(amount=-100.0, discount_percent=10.0)
    
    def test_negative_discount_raises_error(self):
        """Test that negative discount raises ValueError"""
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            apply_discount(amount=100.0, discount_percent=-5.0)
    
    def test_over_hundred_discount_raises_error(self):
        """Test that discount > 100 raises ValueError"""
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            apply_discount(amount=100.0, discount_percent=150.0)


class TestMergeItems:
    """Tests for merge_items function"""
    
    def test_basic_merge(self):
        """Test basic item merging"""
        items = [
            {"total": 10.0},
            {"total": 20.0},
            {"total": 30.0}
        ]
        result = merge_items(items)
        assert result == {
            "total_sum": 60.0,
            "count": 3,
            "avg_total": 20.0
        }
    
    def test_empty_list(self):
        """Test with empty list"""
        result = merge_items([])
        assert result == {
            "total_sum": 0.0,
            "count": 0,
            "avg_total": 0.0
        }
    
    def test_single_item(self):
        """Test with single item"""
        result = merge_items([{"total": 15.0}])
        assert result == {
            "total_sum": 15.0,
            "count": 1,
            "avg_total": 15.0
        }
    
    def test_items_without_total(self):
        """Test items without total field"""
        items = [
            {"description": "Item 1"},
            {"total": 10.0},
            {"description": "Item 3"}
        ]
        result = merge_items(items)
        assert result["total_sum"] == 10.0
        assert result["count"] == 3
    
    def test_rounding(self):
        """Test rounding to 2 decimal places"""
        items = [
            {"total": 10.333},
            {"total": 20.667}
        ]
        result = merge_items(items)
        assert result["total_sum"] == 31.0
        assert result["avg_total"] == 15.5
    
    def test_nested_dict_format(self):
        """Test with items nested in dict (from step reference)"""
        data = {
            "items": [
                {"total": 10.0},
                {"total": 20.0}
            ]
        }
        result = merge_items(data)
        assert result["total_sum"] == 30.0
        assert result["count"] == 2
    
    def test_invalid_input_raises_error(self):
        """Test that non-list input raises TypeError"""
        with pytest.raises(TypeError, match="Items must be a list"):
            merge_items("not a list")


class TestFilterItemsByCategory:
    """Tests for filter_items_by_category function"""
    
    def test_basic_filtering(self):
        """Test basic category filtering"""
        items = [
            {"name": "Coffee", "category": "food"},
            {"name": "Soda", "category": "drink"},
            {"name": "Bagel", "category": "food"}
        ]
        result = filter_items_by_category(items, "food")
        assert len(result) == 2
        assert all(item["category"] == "food" for item in result)
    
    def test_case_insensitive(self):
        """Test case-insensitive category matching"""
        items = [
            {"name": "Coffee", "category": "Food"},
            {"name": "Soda", "category": "DRINK"}
        ]
        result = filter_items_by_category(items, "food")
        assert len(result) == 1
        assert result[0]["name"] == "Coffee"
    
    def test_no_matches(self):
        """Test when no items match category"""
        items = [
            {"name": "Coffee", "category": "food"},
            {"name": "Soda", "category": "drink"}
        ]
        result = filter_items_by_category(items, "dessert")
        assert result == []
    
    def test_empty_list(self):
        """Test with empty list"""
        result = filter_items_by_category([], "food")
        assert result == []
    
    def test_items_without_category(self):
        """Test items without category field"""
        items = [
            {"name": "Item1", "category": "food"},
            {"name": "Item2"}  # No category
        ]
        result = filter_items_by_category(items, "food")
        assert len(result) == 1
    
    def test_nested_dict_format(self):
        """Test with items nested in dict"""
        data = {
            "items": [
                {"name": "Coffee", "category": "food"},
                {"name": "Soda", "category": "drink"}
            ]
        }
        result = filter_items_by_category(data, "food")
        assert len(result) == 1
    
    def test_categorized_field(self):
        """Test with categorized field instead of items"""
        data = {
            "categorized": [
                {"name": "Coffee", "category": "food"},
                {"name": "Soda", "category": "drink"}
            ]
        }
        result = filter_items_by_category(data, "drink")
        assert len(result) == 1
        assert result[0]["name"] == "Soda"
    
    def test_invalid_input_raises_error(self):
        """Test that non-list input raises TypeError"""
        with pytest.raises(TypeError, match="Items must be a list"):
            filter_items_by_category("not a list", "food")


class TestComputeItemStatistics:
    """Tests for compute_item_statistics function"""
    
    def test_basic_statistics(self):
        """Test basic statistics computation"""
        items = [
            {"description": "Coffee", "total": 3.5, "quantity": 1, "category": "food"},
            {"description": "Bagel", "total": 5.0, "quantity": 2, "category": "food"},
            {"description": "Soda", "total": 2.0, "quantity": 1, "category": "drink"}
        ]
        result = compute_item_statistics(items)
        
        assert result["count"] == 3
        assert result["total_amount"] == 10.5
        assert result["total_quantity"] == 4
        assert result["avg_amount"] == 3.5
        assert "categories" in result
    
    def test_category_breakdown(self):
        """Test category breakdown"""
        items = [
            {"total": 10.0, "category": "food"},
            {"total": 15.0, "category": "food"},
            {"total": 5.0, "category": "drink"}
        ]
        result = compute_item_statistics(items)
        
        assert result["categories"]["food"]["count"] == 2
        assert result["categories"]["food"]["total"] == 25.0
        assert result["categories"]["drink"]["count"] == 1
        assert result["categories"]["drink"]["total"] == 5.0
    
    def test_uncategorized_items(self):
        """Test items without category"""
        items = [
            {"total": 10.0},  # No category
            {"total": 20.0, "category": "food"}
        ]
        result = compute_item_statistics(items)
        
        assert "uncategorized" in result["categories"]
        assert result["categories"]["uncategorized"]["count"] == 1
    
    def test_empty_list(self):
        """Test with empty list"""
        result = compute_item_statistics([])
        assert result["count"] == 0
        assert result["total_amount"] == 0.0
        assert result["avg_amount"] == 0.0
    
    def test_items_without_quantities(self):
        """Test items without quantity or total fields"""
        items = [
            {"description": "Item1"},
            {"description": "Item2", "total": 10.0}
        ]
        result = compute_item_statistics(items)
        assert result["count"] == 2
        assert result["total_amount"] == 10.0
        assert result["total_quantity"] == 0
    
    def test_rounding(self):
        """Test rounding to 2 decimal places"""
        items = [
            {"total": 10.333},
            {"total": 20.667}
        ]
        result = compute_item_statistics(items)
        assert result["total_amount"] == 31.0
        assert result["avg_amount"] == 15.5
    
    def test_nested_dict_format(self):
        """Test with items nested in dict"""
        data = {
            "items": [
                {"total": 10.0, "category": "food"},
                {"total": 20.0, "category": "drink"}
            ]
        }
        result = compute_item_statistics(data)
        assert result["count"] == 2
        assert result["total_amount"] == 30.0
    
    def test_invalid_input_raises_error(self):
        """Test that non-list input raises TypeError"""
        with pytest.raises(TypeError, match="Items must be a list"):
            compute_item_statistics("not a list")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
