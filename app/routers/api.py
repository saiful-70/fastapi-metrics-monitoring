"""
API router with business logic endpoints for the FastAPI application
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
import time
from datetime import datetime

# Mock database for demonstration
data_store: Dict[str, Dict[str, Any]] = {}

# Pydantic models for data validation
class DataItem(BaseModel):
    id: Optional[str] = None
    name: str
    value: float
    description: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DataItemResponse(BaseModel):
    id: str
    name: str
    value: float
    description: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

class DataItemUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

# Create API router
router = APIRouter(prefix="/api/v1", tags=["data"])


@router.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with basic response"""
    return {
        "message": "FastAPI Metrics Monitoring System",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/data", response_model=DataItemResponse)
async def create_data_item(item: DataItem) -> DataItemResponse:
    """
    Create a new data item
    
    Args:
        item: Data item to create
        
    Returns:
        Created data item with ID and timestamps
    """
    # Generate ID and timestamps
    item_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Create the data item
    data_item = {
        "id": item_id,
        "name": item.name,
        "value": item.value,
        "description": item.description,
        "tags": item.tags,
        "created_at": now,
        "updated_at": now
    }
    
    # Store in mock database
    data_store[item_id] = data_item
    
    return DataItemResponse(**data_item)


@router.get("/data", response_model=List[DataItemResponse])
async def get_data_items(
    limit: int = 10,
    offset: int = 0,
    tag: Optional[str] = None
) -> List[DataItemResponse]:
    """
    Retrieve data items with optional filtering
    
    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
        tag: Filter by tag (optional)
        
    Returns:
        List of data items
    """
    items = list(data_store.values())
    
    # Filter by tag if provided
    if tag:
        items = [item for item in items if tag in item.get("tags", [])]
    
    # Apply pagination
    items = items[offset:offset + limit]
    
    return [DataItemResponse(**item) for item in items]


@router.get("/data/{item_id}", response_model=DataItemResponse)
async def get_data_item(item_id: str) -> DataItemResponse:
    """
    Retrieve a specific data item by ID
    
    Args:
        item_id: ID of the data item to retrieve
        
    Returns:
        Data item with the specified ID
        
    Raises:
        HTTPException: If item not found
    """
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Data item not found")
    
    return DataItemResponse(**data_store[item_id])


@router.put("/data/{item_id}", response_model=DataItemResponse)
async def update_data_item(item_id: str, update: DataItemUpdate) -> DataItemResponse:
    """
    Update a data item
    
    Args:
        item_id: ID of the data item to update
        update: Fields to update
        
    Returns:
        Updated data item
        
    Raises:
        HTTPException: If item not found
    """
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Data item not found")
    
    # Get existing item
    item = data_store[item_id].copy()
    
    # Update fields if provided
    update_data = update.dict(exclude_unset=True)
    for field, value in update_data.items():
        item[field] = value
    
    # Update timestamp
    item["updated_at"] = datetime.utcnow()
    
    # Store updated item
    data_store[item_id] = item
    
    return DataItemResponse(**item)


@router.delete("/data/{item_id}")
async def delete_data_item(item_id: str) -> Dict[str, str]:
    """
    Delete a data item
    
    Args:
        item_id: ID of the data item to delete
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If item not found
    """
    if item_id not in data_store:
        raise HTTPException(status_code=404, detail="Data item not found")
    
    del data_store[item_id]
    
    return {"message": f"Data item {item_id} deleted successfully"}


@router.get("/data/stats/summary")
async def get_data_stats() -> Dict[str, Any]:
    """
    Get statistics about stored data items
    
    Returns:
        Statistics summary
    """
    items = list(data_store.values())
    
    if not items:
        return {
            "total_items": 0,
            "average_value": 0,
            "min_value": 0,
            "max_value": 0,
            "unique_tags": []
        }
    
    values = [item["value"] for item in items]
    all_tags = []
    for item in items:
        all_tags.extend(item.get("tags", []))
    
    return {
        "total_items": len(items),
        "average_value": sum(values) / len(values),
        "min_value": min(values),
        "max_value": max(values),
        "unique_tags": list(set(all_tags))
    }


@router.post("/data/bulk", response_model=List[DataItemResponse])
async def create_bulk_data_items(items: List[DataItem]) -> List[DataItemResponse]:
    """
    Create multiple data items in bulk
    
    Args:
        items: List of data items to create
        
    Returns:
        List of created data items with IDs and timestamps
    """
    created_items = []
    
    for item in items:
        # Generate ID and timestamps
        item_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create the data item
        data_item = {
            "id": item_id,
            "name": item.name,
            "value": item.value,
            "description": item.description,
            "tags": item.tags,
            "created_at": now,
            "updated_at": now
        }
        
        # Store in mock database
        data_store[item_id] = data_item
        created_items.append(DataItemResponse(**data_item))
    
    return created_items
