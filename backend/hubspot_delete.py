import requests,os

HUBSPOT_BASE_URL = "https://api.hubapi.com"

def delete_hubspot_object(object_type: str, object_id: str):
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN") 
    print(object_id)
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
