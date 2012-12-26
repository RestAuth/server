from RestAuth.backends.base import GroupBackend
from RestAuth.backends.base import PropertyBackend
from RestAuth.backends.base import UserBackend

from RestAuth.Users.models import ServiceUser as User


class DjangoUserBackend(UserBackend):
    def list(self):
        return list(User.objects.values_list('username', flat=True))

    def verify_password(self, username, password):
        # If User.DoesNotExist: 404 Not Found
        user = User.objects.only('password').get(username=username)

        return user.check_password(password)

class DjangoPropertyBackend(PropertyBackend):
    pass

class DjangoGroupBackend(GroupBackend):
    pass
