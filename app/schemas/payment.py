from pydantic import BaseModel
from typing import Optional

class PaymentCreateReq(BaseModel):
    amount: float
    order_id: Optional[str] = None

class PaymentVerifyReq(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    internal_order_id: Optional[str] = None
