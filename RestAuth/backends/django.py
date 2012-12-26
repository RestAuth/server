from RestAuth.backends.base import GroupBackend
from RestAuth.backends.base import PropertyBackend
from RestAuth.backends.base import UserBackend

from RestAuth.common.responses import HttpResponseNoContent
from RestAuth.Users.models import ServiceUser


class DjangoBackend(UserBackend, PropertyBackend, GroupBackend):
    def verify_password(self, logger, log_args, username, password):
        # If User.DoesNotExist: 404 Not Found
        user = ServiceUser.objects.only('password').get(username=username)

        if not user.check_password(password):
            # password does not match - raises 404
            logger.info("Wrong password checked", extra=log_args)
            raise ServiceUser.DoesNotExist("Password invalid for this user.")

        logger.debug("Checked password (ok)", extra=log_args)
        return HttpResponseNoContent()  # Ok
