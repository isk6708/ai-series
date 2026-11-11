from pydantic import BaseModel

class AddInputModel(BaseModel):
    a: float
    b: float

class MultiplyInputModel(BaseModel):
    a: float
    b: float