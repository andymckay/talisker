from pyramid.config import Configurator
from server.resources import Root
from views import listing, summary, request, socketio_service

routes = [
    ('listing', listing),
    ('summary', summary),
    ('request', request),
]

def main(global_config, **settings):
    config = Configurator(root_factory=Root, settings=settings)
    config.add_view('server.views.root',
                    context='server:resources.Root',
                    renderer='server:templates/mytemplate.pt')
    config.add_route('socket_io', '/socket.io/*remaining',
                     view=socketio_service)
    for route in routes:
        config.add_route(route[0], '/%s.json' % route[0],
                         view=route[1], renderer='json')
    config.add_static_view('static', 'server:static')
    return config.make_wsgi_app()

