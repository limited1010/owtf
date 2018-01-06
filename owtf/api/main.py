"""
owtf.api.main
~~~~~~~~~~~~~
"""

import sys
import argparse
import logging

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from owtf.api.routes import HANDLERS
from owtf.utils.app import Application
from owtf.error_reporting import setup_signal_handlers, get_sentry_client
from owtf.lib.owtf_process import OWTFProcess
from owtf.settings import STATIC_ROOT, UI_SERVER_LOG, SERVER_ADDR, UI_SERVER_PORT, TEMPLATES, SENTRY_API_KEY


class APIServer(OWTFProcess):
    def pseudo_run(self):
        application = Application(
            handlers=HANDLERS,
            template_path=TEMPLATES,
            debug=False,
            gzip=True,
            static_path=STATIC_ROOT,
            compiled_template_cache=True
        )
        self.server = tornado.httpserver.HTTPServer(application)
        self.disable_stream_log()
        try:
            ui_port = int(UI_SERVER_PORT)
            ui_address = SERVER_ADDR
            self.server.bind(ui_port, address=ui_address)
            tornado.options.parse_command_line(
                args=['dummy_arg', '--log_file_prefix={}'.format(UI_SERVER_LOG), '--logging=info'])
            self.server.start(1)
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass


def start_server(args, sentry_client=None):
    api = APIServer()
    api.start()


def main(sys_argv=sys.argv):
    setup_signal_handlers()

    # get arguments
    parser = build_arg_parser("api_server")
    args = parser.parse_args(sys_argv[1:])

    try:
        # setup sentry
        sentry_client = get_sentry_client(SENTRY_API_KEY)
    except:
        logging.exception("[-] Uncaught exception on startup")
        sys.exit(1)

    try:
        start_server(args, sentry_client)
    except Exception:
        sentry_client.captureException()
    finally:
        logging.info("Exiting.")
        sys.exit(-1)
