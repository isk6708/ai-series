# @mcp.tool()
# def get_cart_items(cart_id:int) -> [CartItem]:
#     """get cart items"""
#     cart_items = [item for item in carts if item.cart_id == cart_id]
#     return [{"type": "text", "name": f"ID: {item.cart_id},product: {item.product_id},quantity: {item.quantity}"} for item in cart_items]

from data import cart_items
from .schema import CartItemModel, GetCartItemsInputModel

async def handler(args) -> list[CartItemModel]:
    # FIX: support filtering by cart_id (0 or omitted = all carts)
    input = GetCartItemsInputModel(**(args or {}))
    if input.cart_id != 0:
        return [item for item in cart_items if item.cart_id == input.cart_id]
    return cart_items

tool_get_all_cart_items = {
    "name": "get_all_cart_items",
    "description": "Gets cart items. Pass cart_id to get the items of one cart, or omit it (or 0) for all carts",
    "input_schema": GetCartItemsInputModel,
    "handler": handler
}
