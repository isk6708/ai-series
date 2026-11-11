# @mcp.tool()
# def get_order(order_id:int) -> Order:
#     """get order by id"""
#     for order in orders:
#         if order.order_id == order_id:
#             return {"type": "text", "name": f"ID: {order.order_id},customer: {order.customer_id}"}
#     return None

from data import orders
from .schema import OrderModel, GetOrderByIdInputModel

async def handler(args) -> OrderModel:
    input = GetOrderByIdInputModel(**args)
    for order in orders:
        if order.order_id == input.order_id:
            return order
    raise ValueError(f"Order not found: {input.order_id}")

tool_get_order = {
    "name": "get_order",
    "description": "Gets a single order by its order_id",
    "input_schema": GetOrderByIdInputModel,
    "handler": handler
}
