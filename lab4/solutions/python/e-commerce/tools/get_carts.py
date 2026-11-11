from data import cart_items

async def handler(args) -> list[dict]:
    """Summarise every cart (built from cart_items, so it includes items added with add_to_cart)."""
    summary: dict[int, dict] = {}
    for item in cart_items:
        cart = summary.setdefault(item.cart_id, {"cart_id": item.cart_id, "items": 0, "total_quantity": 0})
        cart["items"] += 1
        cart["total_quantity"] += item.quantity
    return list(summary.values())

tool_get_all_carts = {
    "name": "get_all_carts",
    "description": "Gets all carts with their item count and total quantity",
    "input_schema": None,
    "handler": handler
}
