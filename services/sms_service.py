import os
import re
import logging
from typing import Dict, Any, Tuple
import requests
import config

logger = logging.getLogger("awaaz_adhikar.sms")

# Supported SMS Providers via Environment Variables
# Fast2SMS: FAST2SMS_API_KEY
# Twilio: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER (or TWILIO_PHONE_NUMBER)
# MSG91: MSG91_AUTH_KEY, MSG91_TEMPLATE_ID
# Custom Gateway: SMS_GATEWAY_URL, SMS_GATEWAY_API_KEY

def validate_mobile(mobile: str) -> Tuple[bool, str]:
    """
    Validates mobile number format.
    Accepts 10 digits or numbers with +91/91 prefix.
    Returns (is_valid, 10_digit_string).
    """
    if not mobile:
        return False, ""
    digits = re.sub(r'\D', '', str(mobile))
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    
    if len(digits) == 10 and digits[0] in '6789':
        return True, digits
    elif len(digits) == 10:
        return True, digits
    return False, ""

def mask_mobile(mobile: str) -> str:
    """Masks mobile number for safe display (e.g. 98XXXXX210)."""
    digits = re.sub(r'\D', '', str(mobile))[-10:]
    if len(digits) == 10:
        return f"{digits[:2]}XXXXX{digits[-3:]}"
    return "XXXXX"

def is_sms_configured() -> bool:
    """Checks whether an authorized SMS gateway is configured."""
    if getattr(config, "DEMO_MODE", False):
        return True
    fast2sms = bool(os.getenv("FAST2SMS_API_KEY", "").strip())
    twilio = bool(
        os.getenv("TWILIO_ACCOUNT_SID", "").strip() and
        os.getenv("TWILIO_AUTH_TOKEN", "").strip() and
        (os.getenv("TWILIO_FROM_NUMBER", "").strip() or os.getenv("TWILIO_PHONE_NUMBER", "").strip())
    )
    msg91 = bool(os.getenv("MSG91_AUTH_KEY", "").strip())
    custom = bool(os.getenv("SMS_GATEWAY_URL", "").strip())
    return fast2sms or twilio or msg91 or custom

def get_configured_provider_name() -> str:
    """Returns the name of the active SMS gateway provider."""
    if getattr(config, "DEMO_MODE", False):
        return "Demo Mode"
    if os.getenv("FAST2SMS_API_KEY", "").strip():
        return "Fast2SMS"
    if os.getenv("TWILIO_ACCOUNT_SID", "").strip() and os.getenv("TWILIO_AUTH_TOKEN", "").strip():
        return "Twilio"
    if os.getenv("MSG91_AUTH_KEY", "").strip():
        return "MSG91"
    if os.getenv("SMS_GATEWAY_URL", "").strip():
        return "Custom Gateway"
    return "None"

def send_sms_otp(mobile: str, otp: str) -> Dict[str, Any]:
    """
    Dispatches a 6-digit OTP to the citizen's mobile number via configured SMS gateway.
    Never logs or leaks the OTP value.
    If no SMS gateway is configured, returns {"success": False, "error": "SMS service is not configured."}
    """
    is_valid, digits = validate_mobile(mobile)
    if not is_valid:
        return {"success": False, "error": "Please provide a valid 10-digit mobile number."}
    if getattr(config, "DEMO_MODE", False):
        return {"success": True, "provider": "Demo Mode"}
    
    if not is_sms_configured():
        return {"success": False, "error": "SMS service is not configured."}
    
    masked = mask_mobile(digits)
    message_text = f"Your Awaaz Adhikar verification OTP is {otp}. Valid for 5 minutes."
    
    # 1. Fast2SMS Provider
    fast2sms_key = os.getenv("FAST2SMS_API_KEY", "").strip()
    if fast2sms_key:
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": "otp",
                "variables_values": otp,
                "numbers": digits
            }
            headers = {
                "authorization": fast2sms_key,
                "Content-Type": "application/json"
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if resp.status_code == 200 and (data.get("return") is True or data.get("status_code") == 200):
                logger.info(f"SMS OTP dispatched via Fast2SMS to {masked}")
                return {"success": True, "provider": "Fast2SMS"}
            else:
                err_msg = data.get("message") or f"Fast2SMS error (HTTP {resp.status_code})"
                logger.error(f"Fast2SMS delivery error for {masked}: {err_msg}")
                return {"success": False, "error": f"SMS gateway error: {err_msg}"}
        except Exception as e:
            logger.error(f"Fast2SMS request failed for {masked}: {str(e)}")
            return {"success": False, "error": "Failed to connect to SMS gateway."}
    
    # 2. Twilio Provider
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    twilio_from = os.getenv("TWILIO_FROM_NUMBER", "").strip() or os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    if twilio_sid and twilio_token and twilio_from:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            to_number = f"+91{digits}" if not digits.startswith("+") else digits
            resp = requests.post(
                url,
                data={"To": to_number, "From": twilio_from, "Body": message_text},
                auth=(twilio_sid, twilio_token),
                timeout=10
            )
            if resp.status_code in (200, 201):
                logger.info(f"SMS OTP dispatched via Twilio to {masked}")
                return {"success": True, "provider": "Twilio"}
            else:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = data.get("message") or f"Twilio error (HTTP {resp.status_code})"
                logger.error(f"Twilio delivery error for {masked}: {err_msg}")
                return {"success": False, "error": f"SMS gateway error: {err_msg}"}
        except Exception as e:
            logger.error(f"Twilio request failed for {masked}: {str(e)}")
            return {"success": False, "error": "Failed to connect to SMS gateway."}
    
    # 3. Custom Gateway Provider
    custom_url = os.getenv("SMS_GATEWAY_URL", "").strip()
    custom_key = os.getenv("SMS_GATEWAY_API_KEY", "").strip()
    if custom_url:
        try:
            headers = {"Content-Type": "application/json"}
            if custom_key:
                headers["Authorization"] = f"Bearer {custom_key}"
            payload = {
                "mobile": digits,
                "message": message_text,
                "otp": otp
            }
            resp = requests.post(custom_url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201, 202):
                logger.info(f"SMS OTP dispatched via custom gateway to {masked}")
                return {"success": True, "provider": "Custom Gateway"}
            else:
                logger.error(f"Custom gateway delivery error for {masked}: HTTP {resp.status_code}")
                return {"success": False, "error": f"Custom SMS gateway returned status {resp.status_code}"}
        except Exception as e:
            logger.error(f"Custom gateway request failed for {masked}: {str(e)}")
            return {"success": False, "error": "Failed to connect to SMS gateway."}
    
    return {"success": False, "error": "SMS service is not configured."}
