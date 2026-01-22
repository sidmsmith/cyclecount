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

# Vercel Python automatically detects the Flask app instance


























