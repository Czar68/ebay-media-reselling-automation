"""Enhanced debugging logging for API integration"""
import logging
import json
from datetime import datetime
from typing import Any, Optional

# Configure detailed logging
logger = logging.getLogger(__name__)

def setup_debug_logger(log_level=logging.DEBUG):
    """Setup enhanced debugging logger"""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger

def log_api_request(endpoint: str, method: str, payload: Optional[dict] = None):
    """Log API request details"""
    logger.debug(f"API Request: {method} {endpoint}")
    if payload:
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

def log_api_response(status_code: int, response_data: Any, endpoint: str = ""):
    """Log API response details with type information"""
    logger.debug(f"API Response Status: {status_code} {endpoint}")
    logger.debug(f"Response Type: {type(response_data).__name__}")
    
    if isinstance(response_data, dict):
        logger.debug(f"Response Keys: {list(response_data.keys())}")
        logger.debug(f"Response: {json.dumps(response_data, indent=2)}")
    elif isinstance(response_data, list):
        logger.debug(f"Response List Length: {len(response_data)}")
        if response_data:
            logger.debug(f"First item type: {type(response_data[0]).__name__}")
            logger.debug(f"First item: {str(response_data[0])[:200]}")
    else:
        logger.debug(f"Response: {str(response_data)[:500]}")

def log_json_extraction(content: Any, extraction_method: str = "", success: bool = False, error: Optional[str] = None):
    """Log JSON extraction attempts"""
    logger.debug(f"JSON Extraction: {extraction_method}")
    logger.debug(f"Input Type: {type(content).__name__}")
    
    if isinstance(content, (dict, list)):
        logger.debug(f"Input Structure: {str(content)[:300]}")
    elif isinstance(content, str):
        logger.debug(f"Input String Length: {len(content)}")
        logger.debug(f"Input Preview: {content[:200]}")
    
    if success:
        logger.debug("✓ JSON extraction successful")
    elif error:
        logger.warning(f"✗ JSON extraction failed: {error}")

def log_airtable_update(table_name: str, record_id: str, fields: dict, success: bool = False):
    """Log Airtable update operations"""
    logger.debug(f"Airtable Update: {table_name} - Record {record_id}")
    logger.debug(f"Fields being updated: {list(fields.keys())}")
    if success:
        logger.debug(f"✓ Successfully updated {record_id}")
    else:
        logger.debug(f"✗ Failed to update {record_id}")

def log_error_context(error_type: str, error_message: str, context: Optional[dict] = None):
    """Log error with full context information"""
    logger.error(f"Error Type: {error_type}")
    logger.error(f"Error Message: {error_message}")
    if context:
        logger.error(f"Error Context: {json.dumps(context, indent=2, default=str)}")
        
if __name__ == "__main__":
    # Test the logging setup
    setup_debug_logger()
    logger.debug("Debug logging initialized")
    log_api_request("/webhook/airtable", "POST", {"test": "data"})
    log_api_response(200, {"status": "success"}, "/webhook/airtable")
    log_json_extraction({"test": "data"}, "direct_parse", success=True)
