from django.db import transaction

from RestAuth.Users import views as user_views
from RestAuth.Groups import views as group_views
from RestAuth.Services.decorator import login_required


@login_required(realm="/test/users/")
@transaction.commit_manually
def users(request):
    try:
        return user_views.index(request)
    finally:
        transaction.rollback()


@login_required(realm="/test/users/<user>/props/")
@transaction.commit_manually
def users_user_props(request, username):
    try:
        return user_views.userprops_index(request, username)
    finally:
        transaction.rollback()


@login_required(realm="/test/groups/")
@transaction.commit_manually
def groups(request):
    try:
        return group_views.index(request)
    finally:
        transaction.rollback()
