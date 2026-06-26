"""
Auth middleware
Clerk JWT verification — stubbed for initial testing
"""

async def get_current_user():
    """
    Stub user for testing without Clerk auth.
    Replace with real Clerk JWT verification before launch.
    """
    return {
        "id": "test-user-001",
        "email": "test@betterthanbusy.com",
        "plan": "pro"
    }
