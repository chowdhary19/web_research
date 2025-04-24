"""
Error Handler - Utility for consistent error handling.
"""
import logging
import traceback
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

def handle_error(error: Exception, query: str = None) -> Dict[str, Any]:
    """
    Handle exceptions and generate appropriate error responses.
    
    Args:
        error: The exception that occurred
        query: The user query that triggered the error
        
    Returns:
        Dictionary with error details
    """
    error_str = str(error)
    error_type = type(error).__name__
    
    # Log the error with traceback
    logger.error(f"Error processing {'query: ' + query if query else 'request'}")
    logger.error(f"{error_type}: {error_str}")
    logger.debug(traceback.format_exc())
    
    # Map error types to user-friendly messages
    error_messages = {
        "ConnectionError": "I couldn't connect to some websites. This might be due to network issues or website restrictions.",
        "Timeout": "Some websites took too long to respond. Please try again later.",
        "JSONDecodeError": "I had trouble processing some of the data I retrieved.",
        "ValueError": "I encountered an unexpected value while processing your request.",
        "KeyError": "Some expected data was missing while processing your request.",
        "AttributeError": "I encountered an issue with one of the components while processing your request.",
        "LLMProviderError": "There was an issue with the AI service that powers my research capabilities.",
    }
    
    # Get appropriate message based on error type
    if error_type in error_messages:
        message = error_messages[error_type]
    elif "api_key" in error_str.lower() or "apikey" in error_str.lower():
        message = "There was an authentication issue with one of the services I use. Please check API key configurations."
    elif "permission" in error_str.lower() or "access" in error_str.lower():
        message = "I don't have permission to access some content needed for your request."
    else:
        message = "I encountered an unexpected error while processing your request. Please try again or rephrase your query."
    
    # Add query context if available
    if query:
        message += f" Your query was: '{query}'"
    
    return {
        "success": False,
        "error_type": error_type,
        "message": message,
        "query": query,
        "summary": message,  # For consistency with successful responses
        "sources": []  # Empty sources for error responses
    }

def handle_api_error(api_name: str, status_code: int, response_text: str) -> Dict[str, Any]:
    """
    Handle API-specific errors.
    
    Args:
        api_name: Name of the API that returned an error
        status_code: HTTP status code
        response_text: Response body text
        
    Returns:
        Dictionary with error details
    """
    logger.error(f"API Error from {api_name}: {status_code} - {response_text}")
    
    # Common status code messages
    status_messages = {
        400: f"The request to {api_name} was invalid.",
        401: f"Authentication failed for {api_name}. Please check your API key.",
        403: f"Access to {api_name} was forbidden. Check your permissions.",
        404: f"The requested resource was not found on {api_name}.",
        429: f"{api_name} rate limit exceeded. Please try again later.",
        500: f"{api_name} experienced an internal server error.",
        502: f"{api_name} returned a bad gateway error.",
        503: f"{api_name} service is currently unavailable.",
        504: f"{api_name} request timed out.",
    }
    
    message = status_messages.get(status_code, f"Error communicating with {api_name} (HTTP {status_code}).")
    
    return {
        "success": False,
        "error_type": "APIError",
        "api_name": api_name,
        "status_code": status_code,
        "message": message,
        "summary": message,
        "sources": []
    }