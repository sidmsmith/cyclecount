# api/index.py
from flask import Flask, request, jsonify
import os
import sys
import logging
import requests
from requests.auth import HTTPBasicAuth
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

# Vercel Python automatically detects the Flask app instance


























