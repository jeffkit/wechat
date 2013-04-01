# Create your views here.
from django.http import HttpResponse
from wechat.official import WxRequest, WxTextResponse
from wechat.official import WxClient


def wechat(request):
    cli = WxClient("your official account token")
    ret = cli.is_valid_params(request.GET)  # validate the request
    if not ret:
        return HttpResponse('invalid request')
    if request.method == 'GET':
        return HttpResponse(ret[1])  # for interface validation
    else:
        req = WxRequest(request.body)
        if req.MsgType == 'text':
            return HttpResponse(WxTextResponse(req.Content, req).as_xml())
        elif req.MsgType == 'event' and req.Event == 'subscribe':
            return HttpResponse(WxTextResponse('welcome to echo bot!',
                                               req).as_xml())
        else:
            return HttpResponse(WxTextResponse('support text only',
                                               req).as_xml())
