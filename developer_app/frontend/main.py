import time
from pyscript import document, window

def log_info(message: str):
    """Render logs directly into the UI log terminal."""
    timestamp = time.strftime("%H:%M:%S")
    formatted = f"[{timestamp}] [INFO]: {message}\n"
    print(formatted) 
    logs_div = document.getElementById("logs")
    if logs_div:
        logs_div.innerHTML += formatted
        logs_div.scrollTop = logs_div.scrollHeight

log_info("Frontend App PyScript runtime booted.")

# --- MOCK CAPABILITIES ---
# These are functions that the VoxCore Agent will eventually call 
# once we build the SDK in Phase B. For now, they are just Python functions.

def navigate_to_view(view_name: str) -> dict:
    """
    Mock capability to navigate the user to a specific page.
    Valid views: 'home', 'create', 'status', 'details'
    """
    log_info(f"Function executed: navigate_to_view('{view_name}')")
    
    if hasattr(window, 'navigate'):
        window.navigate(view_name)
        result = {"status": "success", "view_changed_to": view_name}
    else:
        result = {"status": "error", "message": "Navigation function not found in DOM."}
        
    log_info(f"navigate_to_view result: {result}")
    return result

def autofill_status_lookup(appointment_id: str) -> dict:
    """
    Mock capability to type the ID into the lookup field for the user.
    """
    log_info(f"Function executed: autofill_status_lookup('{appointment_id}')")
    
    if hasattr(window, 'navigate'):
        window.navigate('status')
        
    input_field = document.getElementById("lookup-id")
    if input_field:
        input_field.value = appointment_id
        result = {"status": "success", "message": "Field filled successfully."}
    else:
        result = {"status": "error"}
        
    log_info(f"autofill_status_lookup result: {result}")
    return result

# Expose to JS so we can test these manually if needed
window.mock_client_actions = {
    "navigate_to_view": navigate_to_view,
    "autofill_status_lookup": autofill_status_lookup
}

log_info("Mock Frontend functions are ready.")
