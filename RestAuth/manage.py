#!/usr/bin/env python
import os
import sys

from pkg_resources import DistributionNotFound
from pkg_resources import Requirement
from pkg_resources import resource_filename


try:
    req = Requirement.parse("RestAuth")
    path = resource_filename(req, 'RestAuth')
    if os.path.exists(path):  # pragma: no cover
        sys.path.insert(0, path)
except DistributionNotFound:
    pass  # we're run in a not-installed environment

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RestAuth.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
