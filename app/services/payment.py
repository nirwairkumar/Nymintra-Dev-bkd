import razorpay
from app.core.config import settings

# Initialize razorpay client
# Using a dummy client if keys are not set yet, so it doesn't crash on boot in dev
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
else:
    razorpay_client = None

def create_order(amount: int, currency: str = "INR", receipt: str = None):
    """
    Amount should be in smallest currency unit (e.g. paisa for INR). 
    Rs. 500 = 50000 paisa
    """
    if not razorpay_client:
        raise ValueError("Razorpay credentials not configured")
        
    data = {
        "amount": amount,
        "currency": currency,
        "receipt": receipt,
        "payment_capture": 1 # Auto capture
    }
    
    order = razorpay_client.order.create(data=data)
    return order

def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
    if not razorpay_client:
        raise ValueError("Razorpay credentials not configured")
        
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    
    try:
        # Returns None on success, raises SignatureVerificationError on failure
        razorpay_client.utility.verify_payment_signature(params_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
