from fastapi import APIRouter
from customer_sync import sync_single_customer

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/sync-customer/{customer_id}")
def sync_customer(customer_id: int):
    return sync_single_customer(customer_id)
