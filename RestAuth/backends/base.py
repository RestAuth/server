class UserBackend(object):
    def check_password(self, logger, log_args, username, password):
        raise NotImplementedError

class PropertyBackend(object):
    pass

class GroupBackend(object):
    pass
