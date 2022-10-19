"""
Faraday Penetration Test IDE
Copyright (C) 2016  Infobyte LLC (https://faradaysec.com/)
See the file 'doc/LICENSE' for the license information
"""
# Standard library imports
import logging
import multiprocessing
import sys
from signal import SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIG_DFL, SIGUSR1, signal

# Related third party imports
import twisted.web
from autobahn.twisted.websocket import listenWS
from twisted.internet import reactor, error
from twisted.web.http import proxiedLogFormatter
from twisted.web.resource import Resource, ForbiddenResource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.util import Redirect
from twisted.web.wsgi import WSGIResource

# Local application imports
import faraday.server.config
from faraday.server.app import create_app
from faraday.server.config import (
    CONST_FARADAY_HOME_PATH,
    faraday_server as server_config,
)
from faraday.server.threads.reports_processor import ReportsManager, REPORTS_QUEUE
from faraday.server.threads.ping_home import PingHomeThread
from faraday.server.websocket_factories import (
    WorkspaceServerFactory,
    BroadcastServerProtocol
)

FARADAY_APP = None

logger = logging.getLogger(__name__)


class FaradaySite(Site):
    def getResourceFor(self, request):
        resource = super().getResourceFor(request)
        if isinstance(resource, twisted.web.resource.NoResource):
            resource = self.resource.getChild("index.html", request)
        return resource


class CleanHttpHeadersResource(Resource):
    def render(self, request):
        request.responseHeaders.removeHeader('Server')
        return super().render(request)


class FileWithoutDirectoryListing(File, CleanHttpHeadersResource):
    def directoryListing(self):
        return ForbiddenResource()

    def render(self, request):
        ret = super().render(request)
        if self.type == 'text/html':
            request.responseHeaders.addRawHeader('Content-Security-Policy',
                                                 'frame-ancestors \'self\'')
            request.responseHeaders.addRawHeader('X-Frame-Options', 'SAMEORIGIN')
        return ret


class FaradayWSGIResource(WSGIResource):
    def render(self, request):
        request.responseHeaders.removeHeader('Server')
        return super().render(request)


class FaradayRedirectResource(Redirect):
    def render(self, request):
        request.responseHeaders.removeHeader('Server')
        return super().render(request)


class WebServer:
    API_URL_PATH = b'_api'
    WEB_UI_LOCAL_PATH = faraday.server.config.FARADAY_BASE / 'server/www'
    # Threads
    raw_report_processor = None
    ping_home_thread = None

    def __init__(self):

        logger.info('Starting web server at http://'
                    f'{server_config.bind_address}:'
                    f'{server_config.port}/')
        self.__build_server_tree()

    def __build_server_tree(self):
        self.root_resource = self.__build_web_resource()
        self.root_resource.putChild(
            WebServer.API_URL_PATH, self.__build_api_resource())

    @staticmethod
    def __build_web_resource():
        return FileWithoutDirectoryListing(WebServer.WEB_UI_LOCAL_PATH)

    @staticmethod
    def __build_api_resource():
        return FaradayWSGIResource(reactor, reactor.getThreadPool(), get_app())

    @staticmethod
    def __build_websockets_resource():
        url = f'ws://{server_config.bind_address}:{server_config.websocket_port}/websockets'
        logger.info(f'Starting websocket server at port '
                    f'{server_config.websocket_port} with bind address {server_config.bind_address}.')
        factory = WorkspaceServerFactory(url=url)
        factory.protocol = BroadcastServerProtocol
        return factory

    @staticmethod
    def install_signal():
        for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
            signal(sig, SIG_DFL)

    def stop_threads(self):
        logger.info("Stopping threads...")
        if self.raw_report_processor.is_alive():
            self.raw_report_processor.stop()
        if self.ping_home_thread.is_alive():
            self.ping_home_thread.stop()

    def restart_threads(self, *args):
        logger.info("Restart threads")
        if self.raw_report_processor.is_alive():
            self.raw_report_processor.stop()
            self.raw_report_processor.join()
        self.raw_report_processor = ReportsManager(REPORTS_QUEUE)
        self.raw_report_processor.start()

    def start_threads(self):
        self.raw_report_processor = ReportsManager(REPORTS_QUEUE)
        self.raw_report_processor.start()
        self.ping_home_thread = PingHomeThread()
        self.ping_home_thread.start()

    def run(self):
        def signal_handler(*args):
            logger.info('Received SIGTERM, shutting down.')
            logger.info("Stopping threads, please wait...")
            self.stop_threads()

        log_path = CONST_FARADAY_HOME_PATH / 'logs' / 'access-logging.log'
        site = FaradaySite(self.root_resource, logPath=log_path, logFormatter=proxiedLogFormatter)
        site.displayTracebacks = False

        try:
            self.install_signal()
            # start threads and processes
            self.start_threads()
            # web and static content
            reactor.listenTCP(
                server_config.port, site,
                interface=server_config.bind_address)
            num_threads = multiprocessing.cpu_count() * 2
            logger.info(f'Starting webserver with {num_threads} threads.')
            reactor.suggestThreadPoolSize(num_threads)
            # websockets
            try:
                listenWS(self.__build_websockets_resource(), interface=server_config.bind_address)
            except error.CannotListenError:
                logger.warning('Could not start websockets, address already open. '
                               'This is ok is you wan to run multiple instances.')
            except Exception as ex:
                logger.warning(f'Could not start websocket, error: {ex}')
            logger.info('Faraday Server is ready')
            reactor.addSystemEventTrigger('before', 'shutdown', signal_handler)
            signal(SIGUSR1, self.restart_threads)
            reactor.run()

        except error.CannotListenError as e:
            logger.error(e)
            self.stop_threads()
            sys.exit(1)

        except Exception as e:
            logger.exception('Something went wrong when trying to setup the Web UI')
            logger.exception(e)
            self.stop_threads()
            sys.exit(1)


def get_app():
    global FARADAY_APP  # pylint: disable=W0603
    if not FARADAY_APP:
        app = create_app()  # creates a Flask(__name__) app
        # After 'Create app'
        FARADAY_APP = app
    return FARADAY_APP
