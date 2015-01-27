# Create your views here.
from django.http import HttpResponse
from wechat.official import WxApplication, WxTextResponse


class EchoApp(WxApplication):
    """把用户输入的文本原样返回。
    """

    SECRET_TOKEN = ''
    APP_ID = ''
    ENCODING_AES_KEY = ''

    def on_text(req):
        return WxTextResponse(req.Content, req)


def wechat(request):
    echo = EchoApp()
    return HttpResponse(echo.process(request.GEt, request.body))
