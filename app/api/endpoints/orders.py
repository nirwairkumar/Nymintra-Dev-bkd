from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.db.database import get_supabase
from app.api.endpoints.users import get_current_user

router = APIRouter()

class OrderCreate(BaseModel):
    design_slug: str
    quantity: int
    customization_data: Dict[str, Any]
    delivery_address: Dict[str, str]
    razorpay_payment_id: Optional[str] = None
    payment_status: Optional[str] = "pending"

class OrderStatusUpdate(BaseModel):
    status: str

@router.post("/", response_model=Dict[str, Any])
def create_order(
    order_in: OrderCreate, 
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    try:
        user_id = current_user['id']
        email = current_user.get("email")
        
        # Ensure user exists in public.users table (Safe Sync)
        # We check by ID first, then by email to avoid unique constraint violations
        existing_by_id = supabase.table("users").select("*").eq("id", user_id).execute()
        
        user_sync = {
            "name": current_user.get("name", "User"),
            "phone": current_user.get("phone"),
            "email": email
        }
        
        if existing_by_id.data:
            # User exists by ID, just update details
            supabase.table("users").update(user_sync).eq("id", user_id).execute()
        else:
            # Check if email exists under a different ID
            if email:
                existing_by_email = supabase.table("users").select("*").eq("email", email).execute()
                if existing_by_email.data:
                    # Email exists for another ID. We "reclaim" this record for the current auth ID
                    # or simply update the ID if the schema allows. 
                    # Most reliable: Update the existing record's ID to match current auth.id
                    old_id = existing_by_email.data[0]['id']
                    supabase.table("users").update({"id": user_id, **user_sync}).eq("id", old_id).execute()
                else:
                    # New user entirely
                    supabase.table("users").insert({"id": user_id, **user_sync}).execute()
            else:
                # No email provided, just insert by ID
                supabase.table("users").insert({"id": user_id, **user_sync}).execute()
        
        # 1. Insert Customization
        cust_payload = {
            "user_id": user_id,
            "bride_name": order_in.customization_data.get("bride_name"),
            "groom_name": order_in.customization_data.get("groom_name"),
            "event_date": order_in.customization_data.get("event_date"),
            "venue": order_in.customization_data.get("venue"),
            "extra_notes": order_in.customization_data.get("extra_notes", ""),
            "print_color": order_in.customization_data.get("print_color", "")
        }
        cust_res = supabase.table("customizations").insert(cust_payload).execute()
        customization_id = cust_res.data[0]['id']

        # 2. Insert Delivery Address
        addr_payload = {
            "user_id": user_id,
            "full_name": order_in.delivery_address.get("full_name"),
            "street": order_in.delivery_address.get("street"),
            "city": order_in.delivery_address.get("city"),
            "state": order_in.delivery_address.get("state"),
            "zip_code": order_in.delivery_address.get("zip_code"),
            "phone": order_in.delivery_address.get("phone")
        }
        addr_res = supabase.table("addresses").insert(addr_payload).execute()
        address_id = addr_res.data[0]['id']

        # Fetch design to check stock and calculate price
        design_res = supabase.table("card_designs").select("base_price, available_stock, print_price, print_price_unit").eq("slug", order_in.design_slug).execute()
        if not design_res.data:
            raise HTTPException(status_code=404, detail="Design not found")
        
        design_data = design_res.data[0]
        base_price = design_data.get('base_price', 15)
        available_stock = design_data.get('available_stock', 1000)
        print_price = design_data.get('print_price', 0)
        print_price_unit = design_data.get('print_price_unit', 100)
        
        # Verify enough stock
        if order_in.quantity > available_stock:
            raise HTTPException(status_code=400, detail=f"Only {available_stock} cards available in stock.")
            
        # Calculate totals
        card_cost = base_price * order_in.quantity
        printing_cost = (print_price / print_price_unit) * order_in.quantity
        total_amount = card_cost + printing_cost

        # 3. Create Order
        order_payload = {
            "user_id": user_id,
            "design_slug": order_in.design_slug,
            "quantity": order_in.quantity,
            "total_amount": total_amount,
            "status": "pending",
            "customization_id": customization_id,
            "address_id": address_id,
            "razorpay_payment_id": order_in.razorpay_payment_id,
            "payment_status": order_in.payment_status
        }
        order_res = supabase.table("orders").insert(order_payload).execute()
        
        # 4. Decrement available stock
        new_stock = available_stock - order_in.quantity
        supabase.table("card_designs").update({"available_stock": new_stock}).eq("slug", order_in.design_slug).execute()
        
        return {"status": "success", "order_id": order_res.data[0]['id']}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        err_msg = str(e)
        if "payment_status" in err_msg or "razorpay_payment_id" in err_msg:
             raise HTTPException(
                status_code=500, 
                detail="Database schema mismatch: missing payment columns. Please run the SQL migration provided in the instructions."
            )
        raise HTTPException(status_code=500, detail=f"Order creation failed: {err_msg}")

@router.get("/", response_model=List[Dict[str, Any]])
def get_user_orders(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    try:
        # For admins, return all orders. Otherwise just the user's
        if current_user.get('role') == 'admin':
            res = supabase.table("orders").select("*, customizations(*), addresses(*)").order('created_at', desc=True).execute()
        else:
            res = supabase.table("orders").select("*, customizations(*), addresses(*)").eq("user_id", current_user['id']).order('created_at', desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized to update order status")
        
    valid_statuses = ["pending", "processing", "printing", "packing", "shipping", "delivered"]
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    try:
        res = supabase.table("orders").update({"status": status_update.status}).eq("id", order_id).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=Dict[str, Any])
def get_order_by_id(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    try:
        # Check permissions: user must own the order or be an admin
        res = supabase.table("orders").select("*, customizations(*), addresses(*)").eq("id", order_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Order not found")
            
        order = res.data[0]
        
        if current_user.get('role') != 'admin' and order.get('user_id') != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Not authorized to view this order")
            
        # Optional: fetch user details for admin
        if current_user.get('role') == 'admin':
            user_res = supabase.table("users").select("name, email, phone").eq("id", order.get('user_id')).execute()
            if user_res.data:
                order['user_details'] = user_res.data[0]
                
        return order
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
