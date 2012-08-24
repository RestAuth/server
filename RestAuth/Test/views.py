from django.db import transaction

from RestAuth.Users.views import UsersView, UserPropsIndex
from RestAuth.Groups import views as group_views
from RestAuth.Services.decorator import login_required

users_view = UsersView.as_view()
props_view = UserPropsIndex.as_view()

@login_required(realm="/test/users/")
@transaction.commit_manually
def users(request):
    try:
        return users_view(request)
    finally:
        transaction.rollback()


@login_required(realm="/test/users/<user>/props/")
@transaction.commit_manually
def users_user_props(request, username):
    try:
        return props_view(request, username=username)
    finally:
        transaction.rollback()


@login_required(realm="/test/groups/")
@transaction.commit_manually
def groups(request):
    try:
        return group_views.index(request)
    finally:
        transaction.rollback()
