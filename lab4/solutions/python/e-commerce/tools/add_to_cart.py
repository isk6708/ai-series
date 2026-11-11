from .schema import AddCartInputModel, CartItemModel
from data import carts, cart_items, products

async def add_handler(args) -> str:
    """Handler function for the add_to_cart tool."""
    try:
        # Validate input using Pydantic model
        input_model = AddCartInputModel(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")

    if input_model.quantity <= 0:
        raise ValueError("quantity must be greater than 0")

    if not any(product.id == input_model.product_id for product in products):
        raise ValueError(f"Invalid product_id: {input_model.product_id}")

    # FIX: previously the item was only appended to `carts`, but
    # get_all_cart_items reads `cart_items`, so added items never showed up.
    # If the product is already in the cart, increase its quantity instead.
    for item in cart_items:
        if item.cart_id == input_model.cart_id and item.product_id == input_model.product_id:
            item.quantity += input_model.quantity
            break
    else:
        cart_items.append(CartItemModel(**input_model.model_dump()))

    carts.append(input_model)  # keep a log of every add_to_cart call

    return (f"Added product {input_model.product_id} x{input_model.quantity} "
            f"to cart {input_model.cart_id}")

tool_add_to_cart = {
    "name": "add_to_cart",
    "description": "Adds a product to the shopping cart",
    "input_schema": AddCartInputModel,
    "handler": add_handler 
}
