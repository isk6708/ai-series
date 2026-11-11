from .schema import MultiplyInputModel


async def multiply_handler(args) -> float:
    """Handler function for the multiply tool."""
    try:
        # Validate input using Pydantic model
        input_model = MultiplyInputModel(**args)
    except Exception as e:
        raise ValueError(f"Invalid input: {str(e)}")

    return float(input_model.a) * float(input_model.b)


tool_multiply = {
    "name": "multiply",
    "description": "Multiplies two numbers",
    "input_schema": MultiplyInputModel,
    "handler": multiply_handler,
}
