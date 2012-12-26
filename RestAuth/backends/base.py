class UserBackend(object):
    def list(self, username, password, log, log_args):
        raise NotImplementedError

    def create(self, username, password, properties, log):
        raise NotImplementedError

    def exists(self, username, log, log_args):
        raise NotImplementedError

    def check_password(self, username, password, log, log_args):
        raise NotImplementedError

    def set_password(self, username, password, log, log_args):
        raise NotImplementedError

    def remove(self, username, log, log_args):
        raise NotImplementedError


class PropertyBackend(object):
    def list(self, username, log, log_args):
        raise NotImplementedError

    def create(self, username, key, value, log, log_args):
        raise NotImplementedError

    def get(self, username, key, log, log_args):
        raise NotImplementedError

    def set(self, username, key, value, log, log_args):
        raise NotImplementedError

    def set_multiple(self, username, props, log, log_args):
        raise NotImplementedError

    def remove(self, username, key, log, log_args):
        raise NotImplementedError


class GroupBackend(object):
    def create(self, service, groupname, log, log_args):
        raise NotImplementedError

    def exists(self, service, groupname, log, log_args):
        raise NotImplementedError

    def add_user(self, service, groupname, username, log, log_args):
        raise NotImplementedError

    def users(self, service, groupname, log, log_args):
        raise NotImplementedError

    def member(self, service, groupname, username):
        raise NotImplementedError

    def rm_user(self, service, groupname, username):
        raise NotImplementedError

    def add_subgroup(self, service, groupname, subservice, subgroupname,
                  log, log_args):
        raise NotImplementedError

    def subgroups(self, service, groupname, subservice, log, log_args):
        raise NotImplementedError

    def rm_subgroup(self, service, groupname, subservice, subgroupname,
                 log, log_args):
        raise NotImplementedError

    def remove(self, service, groupname, log, log_args):
        raise NotImplementedError

