import asyncio
import base64
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
from aiohttp import web, ClientSession
import aiohttp_jinja2
from aiohttp_sse import sse_response
import jinja2


# SET UP LOGGING
logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(name)-30s: %(message)s",
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
        logger.info(f"Server starting on {self.protocol}://{self.host}:{self.port}")

        self.app = self._init_app()

        # IF PROTOCOL IS HTTP
        if self.http:
            web.run_app(self.app, host=self.host, port=self.port)
            return
        # IF PROTOCOL IS HTTPS
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
        app["subscriptions"] = {}

        # APP SIGNALS INIT
        app.on_shutdown.append(self._shutdown_app)

        # JINJA INIT
        jinja2_filters = {"image_proxy": self._get_image_proxy_url}
        aiohttp_jinja2.setup(
            app, loader=jinja2.PackageLoader("src", "templates"), filters=jinja2_filters
        )

        # APP ROUTING INIT
        app.router.add_get("/board/{board_name}", self._board_handler)
        app.router.add_get("/subscribe", self._subscription_handler)
        app.router.add_post("/widget", self._widget_handler)
        app.router.add_get("/image_proxy", self._image_proxy_handler)
        app.router.add_static("/static/", path=PROJECT_ROOT / "static", name="static")
        app.router.add_static(
            "/widgets/", path=PROJECT_ROOT / "widgets", name="widgets"
        )
        return app

    async def _shutdown_app(self, app):
        """
        Called when the app shut downs. Perform clean-up.
        """
        logger.info("Server shutting down.")
        # TODO finish shutdown / cleanup code. E.g. shutdown all Sonos subscriptions?

    def _get_protocol(self):
        if self.http:
            return "http"
        else:
            return "https"

    async def _board_handler(self, request):
        """
        Handles returning the main html for the requested board.
        """
        board_name = request.match_info["board_name"]
        return aiohttp_jinja2.render_template(f"{board_name}.html", request, {})

    async def _subscription_handler(self, request):
        """
        Handles SSE subscriptions.
        """
        async with sse_response(request) as response:

            subscription_id = "$" + str(uuid.uuid4())[:8]

            # create queue and send initial message (to ensure "opened" event in client)
            queue = asyncio.Queue()
            await queue.put(subscription_id)

            # store session queue and widgets list
            widgets = []
            request.app["subscriptions"][subscription_id] = {
                "queue": queue,
                "widgets": widgets,
            }
            try:
                while not response.task.done():
                    payload = await queue.get()
                    logger.info(
                        f"Subscription {subscription_id}: sending payload: {payload}"
                    )
                    await response.send(payload)
                    queue.task_done()
            finally:
                # when disconnected, cancel widget tasks
                for widget in widgets:
                    logger.info("Cancelling widget.")
                    widget.cancel()
                del request.app["subscriptions"][subscription_id]
                logger.info(f"Goodbye, subscription {subscription_id}!")
        return response

    async def _image_proxy_handler(self, request):
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
        async with ClientSession() as session:
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

    async def _widget_handler(self, request):
        """
        Handles requests to initialise a widget
        """

        data_dict = await request.json()

        if "data-widget" not in data_dict:
            logger.warning("No data-widget entry in msg data.")
            return
        if "target" not in data_dict:
            logger.warning("No target entry in msg data.")
            return
        if "subscription_id" not in data_dict:
            logger.warning("No subscription_id entry in msg data.")
            return
        logger.info(f"Message: {data_dict}")

        # lazy load widget module
        widget_module = importlib.import_module(
            f".{data_dict['data-widget']}.{data_dict['data-widget']}",
            package="src.widgets",
        )

        # get queue
        queue = request.app["subscriptions"][data_dict["subscription_id"]]["queue"]
        # add widget instance to session widgets
        request.app["subscriptions"][data_dict["subscription_id"]]["widgets"].append(
            asyncio.ensure_future(
                widget_module.Widget(request=request, queue=queue, **data_dict).start()
            )
        )
        return web.Response(status=200)
