from fastapi import APIRouter, HTTPException, Response, Depends
from supabase import Client
from app.db.database import get_supabase
from app.schemas.design import PreviewRequest
from app.services.preview_engine import generate_preview
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate")
async def create_preview(req: PreviewRequest, supabase: Client = Depends(get_supabase)):
    """
    Endpoint for the frontend to hit during the live-preview wizard.
    """
    response = supabase.table("card_designs").select("*").eq("id", req.design_id).execute()
    if len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Design not found")
        
    design = response.data[0]
        
    # In a real setup, `design.preview_url` might be a local path or cloud URL downloading to a temp file
    # For MVP scaffold, we'll assume it's a local mock path.
    # mock_path = os.path.join(STATIC_DIR, design.preview_url)
    mock_path = "mock_template.png" 
    
    try:
        # This would usually read from the actual image path
        # image_bytes = generate_preview(mock_path, design.zones_json, req.customizations)
        
        # For the scaffold, we just return a success indicating the engine is wired up.
        # In a real environment, we'd return Response(content=image_bytes, media_type="image/webp")
        return {"status": "success", "message": "Preview engine wired up"}
    except Exception as e:
        logger.error(f"Preview Error: {e}")
        raise HTTPException(status_code=500, detail="Preview generation failed")
