from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from supabase import Client
from app.db.database import get_supabase
from app.schemas.user import Token, UserCreate
# Removed jose and custom security imports as we'll use Supabase Auth directly

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, supabase: Client = Depends(get_supabase)):
    try:
        # Pre-check if user already exists
        admin_client = get_supabase()
        existing_user = admin_client.table("users").select("id").eq("email", user_in.email).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Account already exists for this email")

        # 1. Sign up with Supabase Auth
        # Email is now required, phone is optional
        auth_params = {
            "email": user_in.email,
            "password": user_in.password
        }
        
        # If phone is provided, we'll store it in the user metadata or public table
        # Supabase auth.sign_up also accepts phone if configured, but we want 
        # Email to be the primary login method.
        if user_in.phone:
            auth_params["options"] = {"data": {"phone": user_in.phone}}

        auth_res = supabase.auth.sign_up(auth_params)
        
        if not auth_res.user:
            raise HTTPException(status_code=400, detail="Failed to create auth user")

        # 2. Insert into public.users table (Metadata) using a fresh client
        # This ensures we use the service_role and bypass RLS even if sign_up modified the session
        admin_client = get_supabase()
        
        # Sanitize phone: ensure empty strings are treated as NULL to avoid unique constraint violations
        phone = user_in.phone.strip() if user_in.phone else None
        if not phone:
            phone = None

        new_user_data = {
            "id": auth_res.user.id,
            "name": user_in.name,
            "email": user_in.email,
            "phone": phone,
            "auth_provider": "supabase"
        }
        
        admin_client.table("users").upsert(new_user_data).execute()
        
        return {
            "access_token": auth_res.session.access_token if auth_res.session else "pending_verification",
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), supabase: Client = Depends(get_supabase)):
    try:
        # User login should now strictly use email via the username field
        login_params = {
            "email": form_data.username,
            "password": form_data.password
        }

        auth_res = supabase.auth.sign_in_with_password(login_params)
        
        if not auth_res.session:
            raise HTTPException(status_code=401, detail="Invalid credentials or email not confirmed")
            
        # Fetch user profile data to return
        user_data = supabase.table("users").select("*").eq("id", auth_res.user.id).execute()
        user_profile = user_data.data[0] if user_data.data else {"id": auth_res.user.id, "email": auth_res.user.email, "name": "User"}
        user_profile["role"] = "user"
            
        return {
            "access_token": auth_res.session.access_token,
            "token_type": "bearer",
            "user": user_profile
        }
    except Exception as e:
        err_str = str(e).lower()
        if isinstance(e, HTTPException):
            raise e
        print(f"Login error details: {e}") # Log for debugging
        if "email not confirmed" in err_str:
            raise HTTPException(status_code=403, detail="Please verify your email address to log in.")
        if "invalid login credentials" in err_str:
             raise HTTPException(status_code=401, detail="Invalid credentials. Please check your email and password.")
        if "timeout" in err_str or "readtimeout" in err_str:
            raise HTTPException(status_code=503, detail="Login service timed out, please try again")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@router.post("/admin-login", response_model=Token)
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), supabase: Client = Depends(get_supabase)):
    try:
        # 1. Sign in with Supabase Auth
        login_params = {"password": form_data.password}
        if "@" in form_data.username:
            login_params["email"] = form_data.username
        else:
            login_params["phone"] = form_data.username

        auth_res = supabase.auth.sign_in_with_password(login_params)
        
        if not auth_res.session:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
        # 2. Verify user is in the admins table
        admin_check = supabase.table("admins").select("*").eq("email", auth_res.user.email).execute()
        if not admin_check.data:
            # Also check by phone if email didn't match
            admin_check = supabase.table("admins").select("*").eq("phone", auth_res.user.phone).execute()
            if not admin_check.data:
                # Sign out the user if they're not an admin but successfully authenticated
                supabase.auth.sign_out()
                raise HTTPException(status_code=403, detail="Not authorized as admin")
                
        admin_user = admin_check.data[0]
        admin_user["role"] = "admin"

        # Update Supabase Auth metadata for fast future checks
        if not auth_res.user.user_metadata or auth_res.user.user_metadata.get("role") != "admin":
            supabase.auth.update_user({"data": {"role": "admin"}})
                
        return {
            "access_token": auth_res.session.access_token,
            "token_type": "bearer",
            "user": admin_user
        }
    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "readtimeout" in err_str:
            raise HTTPException(status_code=503, detail="Admin service timed out, please try again")
        raise HTTPException(status_code=401, detail=str(e))
