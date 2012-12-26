class UserBackend(object):
    def check_password(self, username, password):
        raise NotImplementedError

class PropertyBackend(object):
    pass

class GroupBackend(object):
    pass
