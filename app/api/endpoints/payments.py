from fastapi import APIRouter, Depends, HTTPException, status
from app.api.endpoints.users import get_current_user
from app.services.payment import create_order as rzp_create_order, verify_payment_signature
from app.schemas.payment import PaymentCreateReq, PaymentVerifyReq
from app.core.config import settings
import logging
import razorpay

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create-order")
def create_order(
    req: PaymentCreateReq,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Amount from frontend is in rupees, service expects paise
        amount_in_paise = int(req.amount * 100)
        
        order = rzp_create_order(amount=amount_in_paise)
        return {"id": order["id"], "amount": order["amount"], "currency": order["currency"]}
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment order: {str(e)}")

@router.post("/verify")
def verify_payment(
    req: PaymentVerifyReq,
    current_user: dict = Depends(get_current_user)
):
    try:
        success = verify_payment_signature(
            razorpay_order_id=req.razorpay_order_id,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_signature=req.razorpay_signature
        )
        
        if success:
            return {"status": "success", "message": "Payment verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Payment signature verification failed")
            
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify payment: {str(e)}")
