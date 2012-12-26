class UserBackend(object):
    def list(self):
        raise NotImplementedError

    def create(self, username, password=None, properties=None, dry=False):
        raise NotImplementedError

    def exists(self, username):
        raise NotImplementedError

    def check_password(self, username, password):
        raise NotImplementedError

    def set_password(self, username, password):
        raise NotImplementedError

    def remove(self, username):
        raise NotImplementedError


class PropertyBackend(object):
    def list(self, username):
        raise NotImplementedError

    def create(self, username, key, value):
        raise NotImplementedError

    def get(self, username, key):
        raise NotImplementedError

    def set(self, username, key, value):
        raise NotImplementedError

    def set_multiple(self, username, props):
        raise NotImplementedError

    def remove(self, username, key):
        raise NotImplementedError


class GroupBackend(object):
    def create(self, service, groupname):
        raise NotImplementedError

    def exists(self, service, groupname):
        raise NotImplementedError

    def add_user(self, service, groupname, username):
        raise NotImplementedError

    def users(self, service, groupname):
        raise NotImplementedError

    def member(self, service, groupname, username):
        raise NotImplementedError

    def rm_user(self, service, groupname, username):
        raise NotImplementedError

    def add_subgroup(self, service, groupname, subservice, subgroupname):
        raise NotImplementedError

    def subgroups(self, service, groupname, subservice):
        raise NotImplementedError

    def rm_subgroup(self, service, groupname, subservice, subgroupname):
        raise NotImplementedError

    def remove(self, service, groupname):
        raise NotImplementedError
