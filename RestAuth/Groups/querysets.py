from django.conf import settings
from django.db import models
from django.db.models import Q


class GroupQuerySet(models.query.QuerySet):
    def member(self, user, service=None, depth=None):
        if depth is None:
            depth = settings.GROUP_RECURSION_DEPTH

        expr = Q(users=user, service=service)

        kwarg = 'users'
        for i in range(depth):
            kwarg = 'parent_groups__%s' % kwarg
            expr |= models.Q(**{kwarg: user, 'service': service})

        return self.filter(expr).distinct()
