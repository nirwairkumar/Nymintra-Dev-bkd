from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from typing import List
from supabase import Client
from app.db.database import get_supabase
from app.schemas.design import CardDesignResponse, CardDesignCreate, CardDesignUpdate
from app.api.endpoints.users import get_current_user
from uuid import uuid4
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload-image")
async def upload_card_image(file: UploadFile = File(...), current_user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """
    Upload a card image to Supabase Storage bucket 'card-images'.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload images")
        
    try:
        file_content = await file.read()
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid4()}.{file_ext}"
        
        try:
            supabase.storage.from_("card-images").upload(
                path=file_name,
                file=file_content,
                file_options={"content-type": file.content_type}
            )
        except Exception as storage_err:
            err_msg = str(storage_err).lower()
            if "bucket_not_found" in err_msg or "not found" in err_msg:
                try:
                    logger.info("Bucket 'card-images' missing. Attempting auto-creation...")
                    supabase.storage.create_bucket("card-images", options={"public": True})
                    supabase.storage.from_("card-images").upload(
                        path=file_name,
                        file=file_content,
                        file_options={"content-type": file.content_type}
                    )
                except Exception as create_err:
                    logger.error(f"Failed to auto-create bucket: {str(create_err)}")
                    raise HTTPException(status_code=404, detail="Storage bucket 'card-images' not found.")
            else:
                logger.error(f"Supabase Storage Error: {str(storage_err)}")
                raise storage_err
        
        public_url = supabase.storage.from_("card-images").get_public_url(file_name)
        return {"url": public_url}
    except Exception as e:
        logger.error(f"Image upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/", response_model=CardDesignResponse)
def create_design(design_in: CardDesignCreate, current_user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """
    Create a new card design. Restricted to Admins.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload cards")
    
    design_data = jsonable_encoder(design_in)
    
    if "categories" in design_data and isinstance(design_data["categories"], list) and len(design_data["categories"]) > 0:
        design_data["category"] = design_data["categories"][0]
    else:
        design_data["category"] = "uncategorized"
        
    if not design_data.get("preview_url"):
        design_data["preview_url"] = design_data.get("thumbnail_url", "")
    if not design_data.get("print_url"):
        design_data["print_url"] = design_data.get("thumbnail_url", "")
    if "zones_json" not in design_data:
        design_data["zones_json"] = {}
    
    try:
        response = supabase.table("card_designs").insert(design_data).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create card")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

@router.get("/", response_model=List[CardDesignResponse])
def get_designs(skip: int = 0, limit: int = 20, category: str = None, supabase: Client = Depends(get_supabase)):
    """
    Retrieve card designs. Filters by published/active status.
    """
    try:
        query = supabase.table("card_designs").select("*").eq("is_active", True)
        if category:
            query = query.filter("categories", "cs", f'["{category}"]')
        
        response = query.order("sort_order", desc=True).range(skip, skip + limit - 1).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching designs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/by-id/{id}", response_model=CardDesignResponse)
def get_design_by_id(id: str, supabase: Client = Depends(get_supabase)):
    """
    Get a specific design by ID.
    """
    response = supabase.table("card_designs").select("*").eq("id", id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Design not found")
    return response.data[0]

@router.get("/{slug}", response_model=CardDesignResponse)
def get_design_by_slug(slug: str, supabase: Client = Depends(get_supabase)):
    """
    Get a specific design by slug.
    """
    response = supabase.table("card_designs").select("*").eq("slug", slug).eq("is_active", True).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Design not found")
    return response.data[0]

@router.patch("/{id}", response_model=CardDesignResponse)
def update_design(
    id: str, 
    design_update: CardDesignUpdate, 
    current_user: dict = Depends(get_current_user), 
    supabase: Client = Depends(get_supabase)
):
    """
    Update an existing card design. Restricted to Admins.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update cards")
    
    existing = supabase.table("card_designs").select("*").eq("id", id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Design not found")
        
    update_data = design_update.model_dump(exclude_unset=True)
    
    if "categories" in update_data and update_data["categories"]:
        update_data["category"] = update_data["categories"][0]
        
    # Use jsonable_encoder to handle HttpUrl and other types
    update_data = jsonable_encoder(update_data)
        
    try:
        response = supabase.table("card_designs").update(update_data).eq("id", id).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to update card")
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to update design: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
