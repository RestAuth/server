from django.views.generic.base import View


class RestAuthView(View):
    def dispatch(self, request, *args, **kwargs):
        self.largs = kwargs.pop('largs', {})
        self.largs['service'] = request.user.username
        return super(RestAuthView, self).dispatch(request, *args, **kwargs)
