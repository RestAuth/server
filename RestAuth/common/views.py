from django.views.generic.base import View


class RestAuthView(View):
    def dispatch(self, request, *args, **kwargs):
        self.largs = kwargs.pop('largs', {})
        self.largs['service'] = request.user.username
        return super(RestAuthView, self).dispatch(request, *args, **kwargs)

class RestAuthResourceView(RestAuthView):
    def dispatch(self, request, *args, **kwargs):
        largs = kwargs.pop('largs', {})

        kwargs['name'] = kwargs.get('name').lower()
        largs['name'] = kwargs.get('name')

        return super(RestAuthResourceView, self).dispatch(
            request, largs=largs, *args, **kwargs)

class RestAuthSubResourceView(RestAuthView):
    def dispatch(self, request, *args, **kwargs):
        largs = kwargs.pop('largs', {})

        kwargs['subname'] = kwargs.get('subname').lower()
        largs['subname'] = kwargs.get('subname')

        return super(RestAuthSubResourceView, self).dispatch(
            request, largs=largs, *args, **kwargs)
