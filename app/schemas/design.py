from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

class ZoneSchema(BaseModel):
    id: str
    label: str
    type: str # text, image
    position: Dict[str, int] # {"x": 350, "y": 120}
    dimensions: Dict[str, int] # {"width": 500, "height": 60}
    style: Dict[str, str | int]
    constraints: Dict[str, Any]
    languages: List[str]

class CardDesignBase(BaseModel):
    name: str
    slug: str
    categories: List[str] # Changed to support multiple categories
    style: Optional[str] = None
    description: Optional[str] = None
    original_price: Optional[float] = None
    base_price: float
    min_quantity: int = 50 # New field for minimum purchase
    thumbnail_url: HttpUrl
    image_urls: List[HttpUrl] = [] # New field for multi-image gallery
    preview_url: Optional[HttpUrl] = None
    print_url: Optional[HttpUrl] = None
    zones_json: Optional[Dict[str, List[ZoneSchema]]] = None
    supported_langs: List[str] = ["en"]
    orientation: str = "portrait"
    is_active: bool = True
    sort_order: int = 0
    available_stock: int = 1000
    print_price: float = 0.0
    print_price_unit: int = 100
    print_colors: List[str] = []

class CardDesignCreate(CardDesignBase):
    pass

class CardDesignUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    categories: Optional[List[str]] = None
    style: Optional[str] = None
    description: Optional[str] = None
    original_price: Optional[float] = None
    base_price: Optional[float] = None
    min_quantity: Optional[int] = None
    thumbnail_url: Optional[HttpUrl] = None
    image_urls: Optional[List[HttpUrl]] = None
    preview_url: Optional[HttpUrl] = None
    print_url: Optional[HttpUrl] = None
    zones_json: Optional[Dict[str, List[ZoneSchema]]] = None
    supported_langs: Optional[List[str]] = None
    orientation: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    available_stock: Optional[int] = None
    print_price: Optional[float] = None
    print_price_unit: Optional[int] = None
    print_colors: Optional[List[str]] = None

class CardDesignResponse(CardDesignBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PreviewRequest(BaseModel):
    design_id: str
    customizations: Dict[str, str] # e.g., {"event_title": "Rahul Weds Priya", "time": "2:00 PM"}
