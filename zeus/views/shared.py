
import os
import base64

from django.http import JsonResponse
from django.template.context_processors import csrf
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def get_randomness(request, *args, **kwargs):
    token = request.GET.get('token', False)
    data = {
        'randomness': base64.b64encode(os.urandom(32))
    }
    if token:
        data['token'] = str(csrf(request)['csrf_token'])
    return JsonResponse(data)
