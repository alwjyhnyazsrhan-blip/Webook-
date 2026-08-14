class WebookEndpoints:
    """
    Real Webook API Production Endpoints.
    """
    BASE_URL = "https://api.webook.com/api/v2"
    
    # Auth
    LOGIN_OTP_REQUEST = f"{BASE_URL}/register-login"
    LOGIN_VERIFY_OTP = f"{BASE_URL}/verify-otp"
    
    # Events & Discovery
    EVENT_LIST = f"{BASE_URL}/events"
    EVENT_DETAILS = lambda slug: f"{WebookEndpoints.BASE_URL}/events/{slug}"
    EVENT_AVAILABILITY = lambda slug: f"{WebookEndpoints.BASE_URL}/events/{slug}/availability"
    
    # Reservations
    CREATE_RESERVATION = f"{BASE_URL}/reservations/hold"
    RELEASE_RESERVATION = lambda hold_id: f"{WebookEndpoints.BASE_URL}/reservations/{hold_id}/cancel"
    EXTEND_RESERVATION = lambda hold_id: f"{WebookEndpoints.BASE_URL}/reservations/{hold_id}/extend"
    
    # User / Tickets
    MY_TICKETS = f"{BASE_URL}/me/tickets"
