from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Для операций с конкретным объектом (retrieve, update, delete)
        if request.user.is_staff:
            return True
        return obj.owner == request.user

    def has_permission(self, request, view):
        # Для операций со списком (list, create)
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated