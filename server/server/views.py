import os

from pyramid.response import Response
from pyramid_socketio.io import SocketIOContext, socketio_manage
import gevent

from parser import base

col = base.Collection('/tmp/output/', blacklist=['^media\.',])

def root(request):
    return {}

def listing(request):
    return col.listing()

def summary(request):
    return 

def request(request):
    key = request.GET.get('key')
    if 'num' in request.GET:
        num = int(request.GET.get('num'))
        return col.requests[key].stats[num].summary()
    
    return col.requests[key].all()

class ConnectIOContext(SocketIOContext):
    def msg_connect(self, msg):
        def monitor():
            while self.io.connected():
                if col.update():
                    self.msg_listing(msg)
                    self.msg_summary(msg)
                gevent.sleep(0.01)
        self.msg_listing(msg)
        self.msg_summary(msg)
        self.spawn(monitor)
        
    def msg_code(self, msg):
        filename, linenumber = msg['filename'].split('#')
        self.msg("code", data={'filename':filename,
                               'linenumber':linenumber,
                               'code':open(filename).read(),
                               'brush':os.path.splitext(filename)[1][1:]})
    
    def msg_listing(self, msg):
        self.msg("listing", data=col.listing())

    def msg_summary(self, msg):
        self.msg("summary", data=[r.summary() for r in col.requests.values()])

    def msg_output(self, msg):
        if "key" not in msg:
            self.msg("output", data=col.requests[msg['request']].all())
        else:
            self.msg("output", data=col.requests[msg['request']].stats[msg['key']].all())

def socketio_service(request):
    retval = socketio_manage(ConnectIOContext(request))
    return Response(retval)