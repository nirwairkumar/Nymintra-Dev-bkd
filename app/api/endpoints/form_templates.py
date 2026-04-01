from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.db.database import get_supabase
from app.api.endpoints.users import get_current_user
from app.schemas.form_template import FormTemplateCreate, FormTemplateUpdate, FormTemplateResponse

router = APIRouter()

@router.post("", response_model=FormTemplateResponse)
def create_form_template(
    template_in: FormTemplateCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if a template for this category already exists
    existing = supabase.table("form_templates").select("id").eq("category", template_in.category).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail=f"A template for category '{template_in.category}' already exists. Please update the existing one.")

    payload = template_in.model_dump()
    try:
        res = supabase.table("form_templates").insert(payload).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[FormTemplateResponse])
def get_all_form_templates(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        res = supabase.table("form_templates").select("*").order("category").execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}", response_model=FormTemplateResponse)
def get_template_by_category(
    category: str,
    supabase = Depends(get_supabase)
):
    try:
        res = supabase.table("form_templates").select("*").eq("category", category).eq("is_active", True).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail=f"No active template found for category '{category}'")
        return res.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{template_id}", response_model=FormTemplateResponse)
def update_form_template(
    template_id: str,
    template_in: FormTemplateUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    payload = template_in.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields provided for update")
        
    try:
        res = supabase.table("form_templates").update(payload).eq("id", template_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Template not found")
        return res.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{template_id}")
def delete_form_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        res = supabase.table("form_templates").delete().eq("id", template_id).execute()
        return {"status": "success", "message": "Template deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
