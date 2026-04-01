from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class FormField(BaseModel):
    id: str
    type: str  # text, textarea, date, time, select
    label: str
    placeholder: Optional[str] = None
    required: bool = False
    options: Optional[List[str]] = None  # Used only if type == 'select'

class FormTemplateBase(BaseModel):
    category: str
    name: str
    fields: List[FormField] = []
    is_active: bool = True

class FormTemplateCreate(FormTemplateBase):
    pass

class FormTemplateUpdate(BaseModel):
    name: Optional[str] = None
    fields: Optional[List[FormField]] = None
    is_active: Optional[bool] = None

class FormTemplateResponse(FormTemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
