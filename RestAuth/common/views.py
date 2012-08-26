from django.views.generic.base import View


class RestAuthView(View):
    def sanitize_arguments(self, resource_name, **kwargs):
        if 'largs' not in kwargs:
            kwargs['largs'] = {}

        kwargs[resource_name] = kwargs.get(resource_name).lower()
        kwargs['largs'][resource_name] = kwargs.get(resource_name)
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.largs = kwargs.pop('largs', {})
        self.largs['service'] = request.user.username
        return super(RestAuthView, self).dispatch(request, *args, **kwargs)

class RestAuthResourceView(RestAuthView):
    def dispatch(self, request, *args, **kwargs):
        kwargs = self.sanitize_arguments('name', **kwargs)
        return super(RestAuthResourceView, self).dispatch(
            request, *args, **kwargs)

class RestAuthSubResourceView(RestAuthView):
    def dispatch(self, request, *args, **kwargs):
        kwargs = self.sanitize_arguments('subname', **kwargs)
        return super(RestAuthSubResourceView, self).dispatch(
            request, *args, **kwargs)
