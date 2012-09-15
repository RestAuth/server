from django.db import transaction

from RestAuth.Users.views import UsersView, UserPropsIndex
from RestAuth.Groups.views import GroupsView
from RestAuth.Services.decorator import login_required

users_view = UsersView.as_view(manage_transactions=False)
props_view = UserPropsIndex.as_view()
groups_view = GroupsView.as_view()

@login_required(realm="/test/users/")
@transaction.commit_manually
def users(request):
    try:
        return users_view(request)
    finally:
        transaction.rollback()


@login_required(realm="/test/users/<user>/props/")
@transaction.commit_manually
def users_user_props(request, name):
    try:
        return props_view(request, name=name)
    finally:
        transaction.rollback()


@login_required(realm="/test/groups/")
@transaction.commit_manually
def groups(request):
    try:
        return groups_view(request)
    finally:
        transaction.rollback()
