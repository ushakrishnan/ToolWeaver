"""
Example structured functions for the hybrid orchestrator.

These functions demonstrate how to create type-safe, reusable functions
that can be called through the function_call tool in execution plans.
"""

from typing import List, Dict, Any
from .hybrid_dispatcher import register_function


@register_function("compute_tax")
def compute_tax(amount: float, tax_rate: float = 0.07) -> float:
    """
    Calculate tax amount based on a given amount and tax rate.
    
    Args:
        amount: The base amount to calculate tax on
        tax_rate: Tax rate as a decimal (default: 0.07 = 7%)
        
    Returns:
        Tax amount rounded to 2 decimal places
        
    Example:
        {"name": "compute_tax", "args": {"amount": 100.0, "tax_rate": 0.08}}
        -> {"result": 8.0}
    """
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    if tax_rate < 0 or tax_rate > 1:
        raise ValueError("Tax rate must be between 0 and 1")
    return round(amount * tax_rate, 2)


@register_function("merge_items")
def merge_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge a list of items and compute aggregate statistics.
    
    Args:
        items: List of item dictionaries, each optionally containing 'total' and 'quantity'
        
    Returns:
        Dictionary with:
        - total_sum: Sum of all item totals
        - count: Number of items
        - avg_total: Average total per item (if applicable)
        
    Example:
        {"name": "merge_items", "args": {"items": [{"total": 10}, {"total": 20}]}}
        -> {"result": {"total_sum": 30, "count": 2, "avg_total": 15.0}}
    """
    # Handle case where items is nested in a dict (from step reference)
    if isinstance(items, dict):
        items = items.get("items", [])
    if not isinstance(items, list):
        raise TypeError("Items must be a list")
    
    total_sum = sum(item.get("total", 0) for item in items)
    count = len(items)
    avg_total = total_sum / count if count > 0 else 0
    
    return {
        "total_sum": round(total_sum, 2),
        "count": count,
        "avg_total": round(avg_total, 2)
    }


@register_function("apply_discount")
def apply_discount(amount: float, discount_percent: float) -> Dict[str, float]:
    """
    Apply a percentage discount to an amount.
    
    Args:
        amount: Original amount
        discount_percent: Discount percentage (e.g., 10 for 10%)
        
    Returns:
        Dictionary with original, discount, and final amounts
        
    Example:
        {"name": "apply_discount", "args": {"amount": 100, "discount_percent": 15}}
        -> {"result": {"original": 100, "discount": 15.0, "final": 85.0}}
    """
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percent must be between 0 and 100")
    
    discount = round(amount * (discount_percent / 100), 2)
    final = round(amount - discount, 2)
    
    return {
        "original": amount,
        "discount": discount,
        "final": final
    }


@register_function("filter_items_by_category")
def filter_items_by_category(items: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """
    Filter items by category.
    
    Args:
        items: List of item dictionaries with 'category' field
        category: Category to filter by
        
    Returns:
        List of items matching the category
        
    Example:
        {"name": "filter_items_by_category", "args": {
            "items": [{"name": "A", "category": "food"}, {"name": "B", "category": "drink"}],
            "category": "food"
        }}
        -> {"result": [{"name": "A", "category": "food"}]}
    """
    # Handle case where items is nested in a dict (from step reference)
    if isinstance(items, dict):
        items = items.get("items", []) or items.get("categorized", [])
    if not isinstance(items, list):
        raise TypeError("Items must be a list")
    
    return [item for item in items if item.get("category", "").lower() == category.lower()]


@register_function("compute_item_statistics")
def compute_item_statistics(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute comprehensive statistics for a list of items.
    
    Args:
        items: List of item dictionaries with optional 'total', 'quantity', 'unit_price' fields
        
    Returns:
        Dictionary with various statistics about the items
        
    Example:
        {"name": "compute_item_statistics", "args": {
            "items": [
                {"description": "Coffee", "total": 3.5, "quantity": 1},
                {"description": "Bagel", "total": 5.0, "quantity": 2}
            ]
        }}
        -> {"result": {"count": 2, "total_amount": 8.5, "total_quantity": 3, ...}}
    """
    # Handle case where items is nested in a dict (from step reference)
    if isinstance(items, dict):
        items = items.get("items", []) or items.get("categorized", [])
    if not isinstance(items, list):
        raise TypeError("Items must be a list")
    
    count = len(items)
    total_amount = sum(item.get("total", 0) for item in items)
    total_quantity = sum(item.get("quantity", 0) for item in items)
    
    # Category breakdown
    categories = {}
    for item in items:
        cat = item.get("category", "uncategorized")
        if cat not in categories:
            categories[cat] = {"count": 0, "total": 0}
        categories[cat]["count"] += 1
        categories[cat]["total"] += item.get("total", 0)
    
    return {
        "count": count,
        "total_amount": round(total_amount, 2),
        "total_quantity": total_quantity,
        "avg_amount": round(total_amount / count, 2) if count > 0 else 0,
        "categories": categories
    }


# Phase 6: Tool Search Tool
# Import and register the tool search function
try:
    from orchestrator.tools.tool_search_tool import tool_search_tool
    register_function("tool_search_tool")(tool_search_tool)
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to register tool_search_tool: {e}")
