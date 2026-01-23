# api/index.py
from flask import Flask, request, jsonify
import os
import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# === SECURE CONFIG (from Vercel Environment Variables) ===
AUTH_HOST = "salep-auth.sce.manh.com"
API_HOST = "salep.sce.manh.com"
USERNAME_BASE = "sdtadmin@"
PASSWORD = os.getenv("MANHATTAN_PASSWORD")
CLIENT_ID = "omnicomponent.1.0.0"
CLIENT_SECRET = os.getenv("MANHATTAN_SECRET")

# Critical: Fail fast if secrets missing
if not PASSWORD or not CLIENT_SECRET:
    raise Exception("Missing MANHATTAN_PASSWORD or MANHATTAN_SECRET environment variables")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_manhattan_token(org):
    """Get Manhattan WMS authentication token"""
    url = f"https://{AUTH_HOST}/oauth/token"
    username = f"{USERNAME_BASE}{org.lower()}"
    data = {
        "grant_type": "password",
        "username": username,
        "password": PASSWORD,
    }
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    try:
        r = requests.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=auth,
            timeout=30,
            verify=False,
        )
        r.raise_for_status()
        return r.json().get("access_token")
    except:
        return None


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/auth', methods=['POST'])
def auth():
    """Authenticate with Manhattan WMS"""
    org = request.json.get('org', '').strip()
    if not org:
        return jsonify({"success": False, "error": "ORG required"})
    token = get_manhattan_token(org)
    if token:
        return jsonify({"success": True, "token": token})
    return jsonify({"success": False, "error": "Auth failed"})

@app.route('/api/initiateCount', methods=['POST'])
def initiate_count():
    """Initiate cycle count for a location"""
    data = request.json
    org = data.get('org', '').strip()
    token = data.get('token', '').strip()
    payload = data.get('payload')
    
    if not org or not token:
        return jsonify({"success": False, "error": "ORG and token required"})
    
    if not payload:
        return jsonify({"success": False, "error": "Payload required"})
    
    # Extract FacilityId from ORG
    facility_id = f"{org.upper()}-DM1"
    url = f"https://{API_HOST}/inventory-management/api/inventory-management/count/initiateCount"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "FacilityId": facility_id,
        "selectedOrganization": org.upper(),
        "selectedLocation": facility_id
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60, verify=False)
        
        if r.status_code not in (200, 201):
            error_msg = f"API {r.status_code}: {r.text[:500]}"
            print(f"[INITIATE_COUNT] Error: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "response": r.text[:500] if r.text else None
            })
        
        try:
            response_data = r.json()
        except:
            response_data = {"raw_response": r.text[:500]}
        
        print(f"[INITIATE_COUNT] Success for Location: {payload.get('LocationId', 'unknown')}")
        return jsonify({
            "success": True,
            "response": response_data
        })
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"[INITIATE_COUNT] {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        })

@app.route('/api/validateItemAndGetItemDetails', methods=['POST'])
def validate_item_and_get_item_details():
    """Validate item and get item details for cycle count"""
    data = request.json
    org = data.get('org', '').strip()
    token = data.get('token', '').strip()
    payload = data.get('payload')
    
    if not org or not token:
        return jsonify({"success": False, "error": "ORG and token required"})
    
    if not payload:
        return jsonify({"success": False, "error": "Payload required"})
    
    # Extract FacilityId from ORG
    facility_id = f"{org.upper()}-DM1"
    url = f"https://{API_HOST}/inventory-management/api/inventory-management/count/validateItemAndGetItemDetails"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "FacilityId": facility_id,
        "selectedOrganization": org.upper(),
        "selectedLocation": facility_id
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60, verify=False)
        
        if r.status_code not in (200, 201):
            error_msg = f"API {r.status_code}: {r.text[:500]}"
            print(f"[VALIDATE_ITEM] Error: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "response": r.text[:500] if r.text else None
            })
        
        try:
            response_data = r.json()
        except:
            response_data = {"raw_response": r.text[:500]}
        
        location_id = payload.get('LocationId', 'unknown')
        item_id = payload.get('ItemAttributeDTO', {}).get('Item', 'unknown')
        print(f"[VALIDATE_ITEM] Success for Location: {location_id}, Item: {item_id}")
        return jsonify({
            "success": True,
            "response": response_data
        })
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"[VALIDATE_ITEM] {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        })

@app.route('/api/acceptQuantity', methods=['POST'])
def accept_quantity():
    """Accept quantity for cycle count"""
    data = request.json
    org = data.get('org', '').strip()
    token = data.get('token', '').strip()
    payload = data.get('payload')
    
    if not org or not token:
        return jsonify({"success": False, "error": "ORG and token required"})
    
    if not payload:
        return jsonify({"success": False, "error": "Payload required"})
    
    # Extract FacilityId from ORG
    facility_id = f"{org.upper()}-DM1"
    url = f"https://{API_HOST}/inventory-management/api/inventory-management/count/acceptQuantity"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "FacilityId": facility_id,
        "selectedOrganization": org.upper(),
        "selectedLocation": facility_id
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60, verify=False)
        
        if r.status_code not in (200, 201):
            error_msg = f"API {r.status_code}: {r.text[:500]}"
            print(f"[ACCEPT_QUANTITY] Error: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "response": r.text[:500] if r.text else None
            })
        
        try:
            response_data = r.json()
        except:
            response_data = {"raw_response": r.text[:500]}
        
        location_id = payload.get('LocationId', 'unknown')
        quantity = payload.get('Quantity', 'unknown')
        item_id = payload.get('ItemAttributeDTO', {}).get('Item', 'unknown')
        print(f"[ACCEPT_QUANTITY] Success for Location: {location_id}, Quantity: {quantity}, Item: {item_id}")
        return jsonify({
            "success": True,
            "response": response_data
        })
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"[ACCEPT_QUANTITY] {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        })

@app.route('/api/persistCountDetails', methods=['POST'])
def persist_count_details():
    """Persist count details for cycle count"""
    data = request.json
    org = data.get('org', '').strip()
    token = data.get('token', '').strip()
    payload = data.get('payload')
    
    if not org or not token:
        return jsonify({"success": False, "error": "ORG and token required"})
    
    if not payload:
        return jsonify({"success": False, "error": "Payload required"})
    
    # Extract FacilityId from ORG
    facility_id = f"{org.upper()}-DM1"
    url = f"https://{API_HOST}/inventory-management/api/inventory-management/count/quantity/persistCountDetails"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "FacilityId": facility_id,
        "selectedOrganization": org.upper(),
        "selectedLocation": facility_id
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60, verify=False)
        
        if r.status_code not in (200, 201):
            error_msg = f"API {r.status_code}: {r.text[:500]}"
            print(f"[PERSIST_COUNT_DETAILS] Error: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "response": r.text[:500] if r.text else None
            })
        
        try:
            response_data = r.json()
        except:
            response_data = {"raw_response": r.text[:500]}
        
        location_id = payload.get('LocationId', 'unknown')
        quantity = payload.get('Quantity', 'unknown')
        item_id = payload.get('ItemAttributeDTO', {}).get('Item', 'unknown')
        print(f"[PERSIST_COUNT_DETAILS] Success for Location: {location_id}, Quantity: {quantity}, Item: {item_id}")
        return jsonify({
            "success": True,
            "response": response_data
        })
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"[PERSIST_COUNT_DETAILS] {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        })

@app.route('/api/getInventory', methods=['POST'])
def get_inventory():
    """Get inventory ItemId for a location"""
    data = request.json
    org = data.get('org', '').strip()
    token = data.get('token', '').strip()
    locationId = data.get('locationId', '').strip()
    
    if not org or not token:
        return jsonify({"success": False, "error": "ORG and token required"})
    
    if not locationId:
        return jsonify({"success": False, "error": "LocationId required"})
    
    # Extract FacilityId from ORG
    facility_id = f"{org.upper()}-DM1"
    url = f"https://{API_HOST}/dcinventory/api/dcinventory/inventory"
    params = {
        "query": f'LocationId="{locationId}"'
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "FacilityId": facility_id,
        "selectedOrganization": org.upper(),
        "selectedLocation": facility_id
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=60, verify=False)
        
        if r.status_code not in (200, 201):
            error_msg = f"API {r.status_code}: {r.text[:500]}"
            print(f"[GET_INVENTORY] Error: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "response": r.text[:500] if r.text else None
            })
        
        try:
            response_data = r.json()
        except:
            response_data = {"raw_response": r.text[:500]}
        
        # Extract ItemId from first record if multiple records exist
        itemId = None
        if isinstance(response_data, dict):
            # Check if response has a data array
            data_list = response_data.get("data") or response_data.get("Data") or []
            if isinstance(data_list, list) and len(data_list) > 0:
                first_record = data_list[0]
                itemId = first_record.get("ItemId") or first_record.get("itemId")
            # Or if response itself is a record
            elif "ItemId" in response_data:
                itemId = response_data.get("ItemId")
            elif "itemId" in response_data:
                itemId = response_data.get("itemId")
        elif isinstance(response_data, list) and len(response_data) > 0:
            first_record = response_data[0]
            itemId = first_record.get("ItemId") or first_record.get("itemId")
        
        if itemId:
            print(f"[GET_INVENTORY] Success for Location: {locationId}, ItemId: {itemId}")
            return jsonify({
                "success": True,
                "itemId": itemId,
                "response": response_data
            })
        else:
            print(f"[GET_INVENTORY] No ItemId found for Location: {locationId}")
            return jsonify({
                "success": False,
                "error": "No ItemId found in response",
                "response": response_data
            })
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"[GET_INVENTORY] {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        })

# Vercel Python automatically detects the Flask app instance


























