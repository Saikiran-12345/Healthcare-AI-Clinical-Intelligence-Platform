"""
Custom Django Authentication Middleware for JSON Storage.
Binds authenticated JsonUser or AnonymousUser to request.user based on session.
"""

from typing import Callable
from accounts.auth import AnonymousUser, JsonUser
from core.storage import db


class JsonAuthMiddleware:
    """Middleware that injects custom user object into request."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            user_data = db.users.find_by_id(user_id)
            if user_data and user_data.get('is_active', True):
                request.user = JsonUser(user_data)
            else:
                # User deleted or deactivated
                request.session.flush()
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()

        response = self.get_response(request)
        return response
