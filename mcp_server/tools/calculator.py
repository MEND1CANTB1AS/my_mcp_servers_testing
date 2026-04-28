from typing import Optional
from pydantic import BaseModel

class CalculationInput(BaseModel):
    expression: str

async def calculate(input: CalculationInput) -> dict:
    """Calculates the result of a given mathematical expression."""
    try:
        # Basic evaluation, assumes controlled environment for safety.
        # In a real-world scenario, this should use a safer math library or parser.
        result = eval(input.expression)
        return {"result": result}
    except Exception as e:
        return {"error": f"Invalid expression: {e}"}