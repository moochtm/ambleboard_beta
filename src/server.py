import asyncio
import hashlib
import importlib
import json
import logging
import os
import pathlib
import socket
import ssl
import time
import uuid
from urllib.parse import quote_plus

import aiofiles
import aiohttp
import aiohttp_jinja2
import jinja2
from aiohttp import web

import src.widgets

# SET UP LOGGING
logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(name)-25s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# GET PROJECT ROOT FOLDER
PROJECT_ROOT = pathlib.Path(__file__).parent

# GET IP ADDRESS
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
HOST_IP_ADDRESS = s.getsockname()[0]
s.close()
logger.info(f"HOST_IP_ADDRESS: {HOST_IP_ADDRESS}")


class Server:
    def __init__(self, host, port, http, debug):
        self.app = None
        self.tasks = []
        self.host = HOST_IP_ADDRESS  # used to be host
        self.port = port
        self.http = http
        self.protocol = self._get_protocol()
        if debug:
            logger.info("Server starting in debug mode.")
            logging.getLogger().setLevel(logging.DEBUG)

    def start(self):
        """
        Starts the web server.
        """
        self.app = self._init_app()
        logger.info(f"Server starting on {self.protocol}://{self.host}:{self.port}")
        if self.http:
            web.run_app(self.app, host=self.host, port=self.port)
            return
        else:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain("domain_srv.crt", "domain_srv.key")
            web.run_app(
                self.app, host=self.host, port=self.port, ssl_context=ssl_context
            )

    async def _init_app(self):
        """
        Initializes the web application.
        """
        app = web.Application()
        app["websockets"] = {}
        app.on_shutdown.append(self._shutdown_app)
        jinja2_filters = {"image_proxy": self._get_image_proxy_url}
        aiohttp_jinja2.setup(
            app, loader=jinja2.PackageLoader("src", "templates"), filters=jinja2_filters
        )
        app.router.add_get("/board/{name}", self.board_handler)
        app.router.add_get("/ws", self.websocket_handler)
        app.router.add_get("/image_proxy", self.image_proxy_handler)
        app.router.add_static("/static/", path=PROJECT_ROOT / "static", name="static")
        app.router.add_static(
            "/widgets/", path=PROJECT_ROOT / "widgets", name="widgets"
        )
        return app

    async def _shutdown_app(self, app):
        """
        Called when the app shut downs. Perform clean-up.
        """
        for ws in app["websockets"].values():
            await ws.close()
        app["websockets"].clear()

    def _get_protocol(self):
        if self.http:
            return "http"
        else:
            return "https"

    async def board_handler(self, request):
        """
        Handles returning the main html for the requested board.
        """
        name = request.match_info["name"]
        return aiohttp_jinja2.render_template(f"{name}.html", request, {})

    async def websocket_handler(self, request):
        """
        Handles web socket connections
        """
        ws_current = web.WebSocketResponse()
        ws_ready = ws_current.can_prepare(request)
        logger.debug(ws_ready)
        await ws_current.prepare(request)

        ws_identifier = str(uuid.uuid4())[:8]
        request.app["websockets"][ws_identifier] = {"ws": ws_current}
        logger.info(f"Client {ws_identifier} connected.")

        while True:
            msg = await ws_current.receive()
            if msg.type != aiohttp.WSMsgType.TEXT:
                break
            await self._handle_message(request, ws_identifier, msg)
            await asyncio.sleep(0)
        self._remove_ws(request, ws_identifier)
        return ws_current

    async def image_proxy_handler(self, request):
        """
        Handles /image_proxy requests.
        Requests always come in in form /image_proxy?url=image_url
        First, there's some clean-up done on the image_proxy folder, then
        Image_url is downloaded if hasn't been already, and then returned
        This ensures all image_proxy are served from the same domain (better browser compatibility)
        """
        params = request.rel_url.query
        # get image_proxy folder path
        dp = os.path.join(".", "image_proxy")
        if not os.path.exists(dp):
            os.mkdir(dp)

        # Do some clean-up of the image_proxy folder
        for f in os.listdir(dp):
            fp = os.path.join(dp, f)
            file_last_accessed = int(os.path.getatime(fp))
            now = int(time.time())
            if now - file_last_accessed > 8 * 60 * 60:
                logger.info(f"Images clean-up removing file: {fp}")
                os.remove(fp)

        # Now focus on the requested file
        async with aiohttp.ClientSession() as session:
            url = params["url"]
            url_hash = hashlib.sha1(url.encode("UTF-8")).hexdigest()
            fp = os.path.join(dp, url_hash + ".jpeg")
            if not os.path.exists(fp):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        fp = os.path.join(dp, url_hash + ".jpeg")
                        async with aiofiles.open(fp, mode="wb+") as f:
                            await f.write(await resp.read())
                            await f.close()
            resp = web.FileResponse(fp)
            return resp

    def _get_image_proxy_url(self, url):
        url_param = quote_plus(url)
        return f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={url_param}"

    def _remove_ws(self, request, ws_identifier):
        """
        Removes web socket from list stored by server
        """
        logger.info(f"Client {ws_identifier} disconnected.")
        del request.app["websockets"][ws_identifier]

    async def send_message(self, data_dict, request, ws_identifier, html):
        try:
            ws = request.app["websockets"][ws_identifier]["ws"]
        except KeyError:
            return
        try:
            await ws.send_json(
                {
                    "target": f"#{data_dict['target']}",
                    "action": "refresh",
                    "data": html,
                }
            )
        except ConnectionResetError:
            self._remove_ws(request, ws_identifier)

    async def _handle_message(self, request, ws_identifier, msg):
        """
        Handles messages coming in from web socket connections.
        Routes actions after checking data in msg is compliant.
        Gets HTML response back from widget.
        Sends HTML back to client.
        """
        if msg.type != aiohttp.WSMsgType.TEXT:
            return
        data_dict = json.loads(msg.data)
        logger.info(f"Msg from client {ws_identifier}: {data_dict}")
        if "data-widget" not in data_dict:
            logger.warning("No data-widget entry in msg data.")
            return
        if "target" not in data_dict:
            logger.warning("No target entry in msg data.")
            return
        if "widgets" not in request.app["websockets"][ws_identifier]:
            request.app["websockets"][ws_identifier]["widgets"] = {}

        widget_module = importlib.import_module(
            f".{data_dict['data-widget']}.{data_dict['data-widget']}",
            package="src.widgets",
        )

        if (
            data_dict["data-widget"]
            not in request.app["websockets"][ws_identifier]["widgets"]
        ):
            request.app["websockets"][ws_identifier]["widgets"][
                data_dict["target"]
            ] = widget_module.Widget()
            await request.app["websockets"][ws_identifier]["widgets"][
                data_dict["target"]
            ].init(data_dict, request, ws_identifier, self.send_message)
        else:
            logger.info("widget already exists")
        return
