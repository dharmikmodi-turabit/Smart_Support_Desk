import requests,os

HUBSPOT_BASE_URL = "https://api.hubapi.com"

def delete_hubspot_object(object_type: str, object_id: str):
    """
    Delete a HubSpot object by type and ID.

    This function deletes a specific object (e.g., contact, company, deal)
    from HubSpot CRM using the provided object type and object ID.

    Args:
    - object_type (str): Type of the HubSpot object (e.g., "contacts", "companies").
    - object_id (str): Unique identifier of the object to delete.

    Returns:
    - dict:
        - {"status": "success", "message": "Deleted successfully"} if deletion succeeds.
        - {"status": "error", "status_code": int, "detail": str} if deletion fails.

    Raises:
    - RuntimeError: If there is a problem with the HubSpot API request or connection.
    """

    try:
        HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
        url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/{object_type}/{int(object_id)}"
        
        headers = {
            "Authorization": f"Bearer {HUBSPOT_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            return {"status": "success", "message": "Deleted successfully"}
        
        return {
            "status": "error",
            "status_code": response.status_code,
            "detail": response.text
        }
    except requests.RequestException as e:
        raise RuntimeError(f"HubSpot delete failed: {e}")   
