from django.db import models
from RestAuth.Groups.querysets import GroupQuerySet


class GroupManager(models.Manager):
    def get_query_set(self):
        return GroupQuerySet(self.model)

    def member(self, user, service=None, depth=None):
        return self.get_query_set().member(user, service, depth)
