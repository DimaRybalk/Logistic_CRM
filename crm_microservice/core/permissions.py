from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsCompanyMember(permissions.BasePermission):
    message = "У вас нема доступа до цих даних"

    def has_object_permission(self, request, view, obj):
        user_company_id = getattr(request.user, "company_id", None)
        obj_company_id = getattr(obj, "company_id", None)

        return user_company_id is not None and user_company_id == obj_company_id


class IsForwarderPermission(permissions.BasePermission):
    def has_permission(self,request,view):
        user_role = getattr(request.user, "role", None)
        if user_role == "FORWARDER":
            return True
        return False 

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method == "DELETE":
            return False
        
        user_id = getattr(request.user, "id", None)
        obj_user_id = getattr(obj, "responsible_id", None)

        return user_id is not None and user_id == obj_user_id

class IsOwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user_role = getattr(request.user, "role", None)
        if user_role == "OWNER":
            return True
        return False

class IsViewerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return False
        
        user_role = getattr(request.user, "role", None)
        if user_role == "VIEWER":
            return True 
        return False

        