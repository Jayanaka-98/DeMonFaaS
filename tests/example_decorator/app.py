from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import requests
from typing import Optional
from demonfaas.func_extractor import ExtractFunctionToFile

app = FastAPI()

class Item(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=datetime.utcnow)


@ExtractFunctionToFile
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI in serverless!"}

@ExtractFunctionToFile
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    """
    Endpoint to get an item by ID.
    Simulates fetching from an external API.
    """
    try:
        response = requests.get(f"https://jsonplaceholder.typicode.com/posts/{item_id}")
        response.raise_for_status()
        data = response.json()
        return {"item_id": item_id, "data": data, "query": q}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching item: {str(e)}")

@ExtractFunctionToFile
@app.post("/create")
def create_item(item: Item):
    """
    Endpoint to create an item.
    Uses Pydantic model for input validation.
    """
    # Process the item (e.g., save to a database or perform other actions)
    return {"name": item.name, "description": item.description or "No description provided", "created_at": item.created_at}