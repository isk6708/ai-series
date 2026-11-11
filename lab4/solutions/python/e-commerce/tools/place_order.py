# @mcp.tool()
# def place_order(customer_id:int) -> Order:
#     """place order"""
#     if customer_id != 0 and not any(customer.id == customer_id for customer in customers):
#         raise ValueError(f"Invalid customer_id: {customer_id}")

#     new_order = Order(0, customer_id)
#     orders.append(new_order)
#     return {"type": "text", "name": f"ID: {new_order.order_id},customer: {new_order.customer_id}"}

from data import orders, customers
from .schema import OrderModel, PlaceOrderInputModel

async def handler(args) -> OrderModel:
    # FIX: the caller no longer has to send an order_id (the server generates it)
    order = PlaceOrderInputModel(**args)

    # FIX: customer_id=0 used to bypass validation; every order needs a real customer
    if not any(customer.id == order.customer_id for customer in customers):
        raise ValueError(f"Invalid customer_id: {order.customer_id}")

    if order.quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    # Create a new order with a new ID
    new_order = OrderModel(
        order_id=max((o.order_id for o in orders), default=0) + 1,
        customer_id=order.customer_id,
        quantity=order.quantity,
        total_price=order.total_price,
    )
    orders.append(new_order)

    return new_order

tool_place_order = {
    "name": "place_order",
    "description": "Places a new order for a customer (order_id is generated automatically)",
    "input_schema": PlaceOrderInputModel,
    "handler": handler
}
