from RestAuth.backends.base import GroupBackend
from RestAuth.backends.base import PropertyBackend
from RestAuth.backends.base import UserBackend

from RestAuth.common.responses import HttpResponseNoContent
from RestAuth.Users.models import ServiceUser


class DjangoUserBackend(UserBackend):
    def list(self):
        return list(ServiceUser.objects.values_list('username', flat=True))

    def verify_password(self, username, password):
        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('password').get(username=username)

        if not user.check_password(password):
            # password does not match - raises 404
            raise ServiceUser.DoesNotExist("Password invalid for this user.")

        return HttpResponseNoContent()  # Ok

class DjangoPropertyBackend(PropertyBackend):
    pass

class DjangoGroupBackend(GroupBackend):
    pass
