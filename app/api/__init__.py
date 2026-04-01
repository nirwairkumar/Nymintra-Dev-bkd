from fastapi import APIRouter
from app.api.endpoints import auth, users, payments, designs, preview, orders, settings, form_templates

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(designs.router, prefix="/designs", tags=["designs"])
api_router.include_router(preview.router, prefix="/preview", tags=["preview"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(form_templates.router, prefix="/form-templates", tags=["form-templates"])
