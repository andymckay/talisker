from pyramid.config import Configurator
from server.resources import Root
from views import socketio_service, create_base

def main(global_config, **settings):
    if 'talisker_path' not in settings:
        raise ValueError('Warning: talikser_path not defined in the config, '
                         'please set talisker_path in app:server.')
    create_base(settings['talisker_path'])
    
    config = Configurator(root_factory=Root, settings=settings)
    config.add_view('server.views.root',
                    context='server:resources.Root',
                    renderer='server:templates/mytemplate.pt')
    config.add_route('socket_io', '/socket.io/*remaining',
                     view=socketio_service)
    config.add_static_view('static', 'server:static')
    return config.make_wsgi_app()

