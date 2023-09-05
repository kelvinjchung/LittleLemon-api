from rest_framework.permissions import BasePermission


class BaseUserPermission(BasePermission):
    group = ""

    def has_permission(self, request, view):
        if (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name=self.group).exists()
        ):
            return True
        return False


class IsManager(BaseUserPermission):
    group = "Manager"


class IsDeliveryCrew(BaseUserPermission):
    group = "Delivery Crew"


class IsCustomer(BaseUserPermission):
    def has_permission(self, request, view):
        if (
            request.user
            and request.user.is_authenticated
            and not request.user.groups.filter(
                name__in=["Manager", "Delivery Crew"]
            ).exists()
        ):
            return True
        return False
