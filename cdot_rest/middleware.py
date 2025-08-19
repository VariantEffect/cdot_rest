from django.http import HttpResponse


# Use middleware to handle health check requests. This lets us return a simple response for
# applicatoin health prior to checking allowed hosts. When deployed on AWS Elastic Beanstalk,
# the host header comes from the load balancer and is not static, so can be difficult to maintain.
class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health':
            return HttpResponse('ok')
        return self.get_response(request)
