# api/index.py
from flask import Flask, request, jsonify
import os
import sys
import logging
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timezone
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger('cycle_count')

app = Flask(__name__)

# === SECURE CONFIG (from Vercel Environment Variables) ===
AUTH_HOST = "salep-auth.sce.manh.com"
API_HOST = "salep.sce.manh.com"
USERNAME_BASE = "sdtadmin@"
PASSWORD = os.getenv("MANHATTAN_PASSWORD")
CLIENT_ID = "omnicomponent.1.0.0"
CLIENT_SECRET = os.getenv("MANHATTAN_SECRET")

logger.info("Environment check: MANHATTAN_PASSWORD=%s, MANHATTAN_SECRET=%s",
            "SET" if PASSWORD else "MISSING",
            "SET" if CLIENT_SECRET else "MISSING")

# Critical: Fail fast if secrets missing
if not PASSWORD or not CLIENT_SECRET:
    raise Exception("Missing MANHATTAN_PASSWORD or MANHATTAN_SECRET environment variables")

USAGE_INGEST_URL = os.getenv("MANHATTAN_USAGE_INGEST_URL", "").strip()
USAGE_INGEST_SECRET = os.getenv("MANHATTAN_USAGE_INGEST_SECRET", "").strip()
APP_NAME = "cycle-count"
APP_VERSION = "1.3.1"


def forward_usage_event(payload):
    """POST usage JSON to Manhattan app usage dashboard ingest (Neon)."""
    if not USAGE_INGEST_URL:
        logger.warning("[usage] MANHATTAN_USAGE_INGEST_URL not set; event not recorded")
        return
    headers = {"Content-Type": "application/json"}
    if USAGE_INGEST_SECRET:
        headers["Authorization"] = f"Bearer {USAGE_INGEST_SECRET}"
    try:
        requests.post(USAGE_INGEST_URL, json=payload, headers=headers, timeout=8)
    except Exception as e:
        logger.warning("[usage] Forward failed: %s", e)


@app.route('/api/usage-track', methods=['POST'])
def usage_track():
    """Receive usage events from the SPA and forward to ingest."""
    data = request.json or {}
    event_name = data.get("event_name")
    metadata = data.get("metadata") or {}
    if not event_name:
        return jsonify({"success": True})
    payload = {
        **metadata,
        "event_name": event_name,
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    forward_usage_event(payload)
    return jsonify({"success": True})

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

    logger.info("Auth request: url=%s, username=%s, org=%s", url, username, org)

    try:
        r = requests.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=auth,
            timeout=30,
            verify=False,
        )
        logger.info("Auth response: status=%s", r.status_code)

        if r.status_code != 200:
            logger.error("Auth failed: status=%s, body=%s", r.status_code, r.text[:500])
            return None, f"HTTP {r.status_code}: {r.text[:200]}"

        token_data = r.json()
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("Auth response missing access_token. Keys: %s", list(token_data.keys()))
            return None, "Response missing access_token"

        logger.info("Auth success: token length=%d", len(access_token))
        return access_token, None

    except requests.exceptions.Timeout:
        logger.error("Auth timeout after 30s for org=%s", org)
        return None, "Request timed out (30s)"
    except requests.exceptions.ConnectionError as e:
        logger.error("Auth connection error for org=%s: %s", org, str(e))
        return None, f"Connection error: {str(e)[:200]}"
    except requests.exceptions.HTTPError as e:
        logger.error("Auth HTTP error for org=%s: %s", org, str(e))
        return None, f"HTTP error: {str(e)[:200]}"
    except Exception as e:
        logger.error("Auth unexpected error for org=%s: %s: %s", org, type(e).__name__, str(e))
        return None, f"{type(e).__name__}: {str(e)[:200]}"


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/auth', methods=['POST'])
def auth():
    """Authenticate with Manhattan WMS"""
    logger.info("Auth endpoint called")
    try:
        body = request.json
        logger.info("Auth request body keys: %s", list(body.keys()) if body else "None")
    except Exception as e:
        logger.error("Failed to parse request body: %s", str(e))
        return jsonify({"success": False, "error": f"Invalid request body: {str(e)}"})

    org = body.get('org', '').strip() if body else ''
    if not org:
        logger.warning("Auth called with empty org")
        return jsonify({"success": False, "error": "ORG required"})

    logger.info("Authenticating org=%s", org)
    token, error_detail = get_manhattan_token(org)
    if token:
        logger.info("Auth succeeded for org=%s", org)
        return jsonify({"success": True, "token": token})

    logger.error("Auth failed for org=%s: %s", org, error_detail)
    return jsonify({"success": False, "error": f"Auth failed: {error_detail}"})

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
        
        # Try to parse JSON response regardless of status code (API may return 400 with warning messages)
        try:
            response_data = r.json()
        except:
            # If JSON parsing fails, handle based on status code
            if r.status_code not in (200, 201):
                error_msg = f"API {r.status_code}: {r.text[:500]}"
                print(f"[ACCEPT_QUANTITY] Error: {error_msg}")
                return jsonify({
                    "success": False,
                    "error": error_msg,
                    "response": r.text[:500] if r.text else None
                })
            else:
                response_data = {"raw_response": r.text[:500]}
        
        location_id = payload.get('LocationId', 'unknown')
        quantity = payload.get('Quantity', 'unknown')
        item_id = payload.get('ItemAttributeDTO', {}).get('Item', 'unknown')
        
        # Check the actual API response success field (may be false even with 200/400 status)
        api_success = response_data.get('success', True) if isinstance(response_data, dict) else True
        
        # If API says success=false, we still return it but let frontend check for warnings
        # Even if status code is 400, we return the full response so frontend can check for warnings
        if api_success:
            print(f"[ACCEPT_QUANTITY] Success for Location: {location_id}, Quantity: {quantity}, Item: {item_id}")
        else:
            print(f"[ACCEPT_QUANTITY] API returned success=false for Location: {location_id}, Quantity: {quantity}, Item: {item_id}")
            if r.status_code not in (200, 201):
                print(f"[ACCEPT_QUANTITY] Status code: {r.status_code} (may contain warning messages)")
        
        return jsonify({
            "success": api_success,
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

@app.route('/api/endCount', methods=['POST'])
def end_count():
    """End cycle count"""
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
    url = f"https://{API_HOST}/inventory-management/api/inventory-management/count/end"
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
            print(f"[END_COUNT] Error: {error_msg}")
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
        count_run_id = payload.get('CountRunId', 'unknown')
        print(f"[END_COUNT] Success for Location: {location_id}, CountRunId: {count_run_id}")
        return jsonify({
            "success": True,
            "response": response_data
        })
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"[END_COUNT] {error_msg}")
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

@app.route('/api/sendMessage', methods=['POST'])
def send_message():
    """Send a chat message via Manhattan Messenger"""
    data = request.json
    org = data.get('org', '').strip()
    token = data.get('token', '').strip()
    content = data.get('content', '').strip()
    users = data.get('users', [])

    if not org or not token:
        return jsonify({"success": False, "error": "ORG and token required"})

    if not content or not users:
        return jsonify({"success": False, "error": "Content and users required"})

    facility_id = f"{org.upper()}-DM1"
    url = f"https://{API_HOST}/messenger/api/messenger/user/chat/save"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "FacilityId": facility_id,
        "selectedOrganization": org.upper(),
        "selectedLocation": facility_id
    }
    payload = {
        "Content": content,
        "Users": users
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
        logger.info("[SEND_MESSAGE] status=%s, content='%s', users=%s", r.status_code, content, users)

        try:
            response_data = r.json()
        except Exception:
            response_data = {"raw_response": r.text[:500]}

        if r.status_code not in (200, 201):
            logger.error("[SEND_MESSAGE] Error: %s", r.text[:500])
            return jsonify({"success": False, "error": f"API {r.status_code}", "response": response_data})

        return jsonify({"success": True, "response": response_data})

    except Exception as e:
        logger.error("[SEND_MESSAGE] Exception: %s", str(e))
        return jsonify({"success": False, "error": str(e)})

# Vercel Python automatically detects the Flask app instance


























