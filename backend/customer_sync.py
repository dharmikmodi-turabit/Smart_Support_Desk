from database import access_db
from hubspot_contacts import create_contact_from_db

def sync_single_customer(customer_id: int):
    db = access_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM customer WHERE customer_id = %s",
        (customer_id,)
    )
    customer = cursor.fetchone()

    if not customer:
        return {"error": "Customer not found"}

    create_contact_from_db(customer)
    return {"success": True}
