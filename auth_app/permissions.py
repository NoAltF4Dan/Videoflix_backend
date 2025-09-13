from rest_framework.permissions import BasePermission
class AllowAnyButTrackAuth(BasePermission):
     def has_permission(self, request, view):
        return True