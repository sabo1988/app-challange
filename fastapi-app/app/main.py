from fastapi import FastAPI, HTTPException
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone

app = FastAPI(
    title="FastAPI App",
    version="0.1.0",
)

# --- Models ---

Category = Literal["main", "side", "drink", "dessert"]

class ItemCreate(BaseModel):
    name: str
    category: Category
    price: float
    isAvailable: bool = True

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[Category] = None
    price: Optional[float] = None
    isAvailable: Optional[bool] = None

class Item(BaseModel):
    id: str
    name: str
    category: Category
    price: float
    isAvailable: bool = True
    isDeleted: bool = False
    createdAt: str
    updatedAt: str

# --- Fake DB (in-memory) ---
items: List[Item] = []

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def find_item(item_id: str) -> Item:
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


# --- Routes (CRUD) ---

@app.get("/")
def home():
    return {"Welcome to menu API"}

@app.get("/api/items", response_model=List[Item])
def list_items(include_deleted: bool = False):
    if include_deleted:
        return items
    return [i for i in items if not i.isDeleted]

@app.post("/api/items", response_model=Item, status_code=201)
def create_item(payload: ItemCreate):
    t = now_iso()
    item = Item(
        id=str(uuid4()),
        name=payload.name,
        category=payload.category,
        price=payload.price,
        isAvailable=payload.isAvailable,
        isDeleted=False,
        createdAt=t,
        updatedAt=t,
    )
    items.append(item)
    return item

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: str, payload: ItemUpdate):
    item = find_item(item_id)

    # (simple) prevent editing deleted items
    if item.isDeleted:
        raise HTTPException(status_code=400, detail="Item is deleted")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)

    item.updatedAt = now_iso()
    return item

@app.delete("/api/items/{item_id}", response_model=Item)
def delete_item(item_id: str):
    item = find_item(item_id)

    # soft delete
    item.isDeleted = True
    item.updatedAt = now_iso()
    return item
