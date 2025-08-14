from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Allow read-only access to everyone,
    but write access only to admin (staff) users.
    """

    def has_permission(self, request, view):
        # This ensures read access (GET, HEAD, OPTIONS) is allowed to everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions require the user to be staff
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Same logic for object-level permissions
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
