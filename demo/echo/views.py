# -*- coding: UTF-8 –*-
# Create your views here.
from django.http import HttpResponse
from wechat.official import WxApplication, WxTextResponse
from django.views.decorators.csrf import csrf_exempt

class WxApp(WxApplication):
    """把用户输入的文本原样返回。
    """

    SECRET_TOKEN = ''
    APP_ID = ''
    ENCODING_AES_KEY = ''

    def on_text(self, req):
        return WxTextResponse(req.Content, req)

@csrf_exempt
def wechat(request):
    app = WxApp()
    result = app.process(request.GET, request.body)
    return HttpResponse(result)
