import asyncio
import aioftp
import hashlib
import importlib
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import pathlib
import socket
import ssl
import time
import uuid
from urllib.parse import quote_plus, unquote, urlparse, parse_qs
from datetime import datetime, timedelta
import sys

import aiofiles
from aiohttp import web, ClientSession
import aiohttp_jinja2
from aiohttp_sse import sse_response
import jinja2


# SET UP LOGGING
logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        TimedRotatingFileHandler(
            filename="log.log", when="H", interval=6, backupCount=12
        ),
    ],
)
logger = logging.getLogger(__name__)


# TRY TO IMPORT OPENCV
OPENCV_IMPORTED = True
try:
    import cv2

    logger.info(f"OpenCV imported successfully.")
except ImportError as e:
    logger.error(f"Error importing OpenCV: {str(e)}")
    OPENCV_IMPORTED = False
# try:
#     import numpy as np
#     logger.info(f"Numpty imported successfully.")
# except ImportError as e:
#     logger.error(f"Error importing Numpy: {str(e)}")
#     OPENCV_IMPORTED = False

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
        jinja2_filters = {
            "image_proxy": self._get_image_proxy_url,
            "convert_date_time": self._convert_date_time,
            "today": self._today,
        }
        aiohttp_jinja2.setup(
            app, loader=jinja2.PackageLoader("src", "templates"), filters=jinja2_filters
        )

        # APP ROUTING INIT
        # TODO: add route and handler to return links to all boards
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
            logger.info(f"Hello, subscription {subscription_id}!")

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
                    # await widget
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
        main_url = str(request.rel_url)
        query = urlparse(main_url).query
        image_url = unquote(parse_qs(query)["url"][0])

        # below is the old way that we determined the image_url
        # image_url = unquote(str(request.rel_url)[17:])

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
        # TODO: Find a way to stop concurrent downloads caused by multiple GETs in small time window.
        #   e.g. a lock file?
        url = image_url
        url_hash = hashlib.sha1(url.encode("UTF-8")).hexdigest()
        fp = os.path.join(dp, url_hash + ".jpeg")

        if not os.path.exists(fp):

            logger.info(f"Image Proxy downloading image: url={url}, path={fp}")

            parsed_url = urlparse(image_url)
            logger.info(f"Parsed URL: {parsed_url}")

            if parsed_url.scheme == "http" or parsed_url.scheme == "https":
                async with ClientSession() as session:
                    if not os.path.exists(fp):
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                fp = os.path.join(dp, url_hash + ".jpeg")
                                async with aiofiles.open(fp, mode="wb+") as f:
                                    await f.write(await resp.read())
                                    await f.close()

            elif parsed_url.scheme == "ftp":
                logger.info(f"Downloading Path: {parsed_url.path}")
                client = aioftp.Client()
                await client.connect(parsed_url.hostname)
                if parsed_url.username is not None:
                    await client.login(parsed_url.username, parsed_url.password)
                await client.download(parsed_url.path, fp, write_into=True)

        # handle requests for resized image
        image_w = parse_qs(query)["w"][0] if "w" in parse_qs(query).keys() else None
        image_h = parse_qs(query)["h"][0] if "h" in parse_qs(query).keys() else None

        # TODO! FIX THIS ITS DISABLED AT THE MOMENT!
        # if image_w is not None and image_h is not None and False:
        #
        #     size = int(image_w), int(image_h)
        #     outfile = os.path.splitext(fp)[0] + f"_{image_w}x{image_h}.jpeg"
        #     if not os.path.exists(outfile):
        #         try:
        #             im = Image.open(fp)
        #             im.thumbnail(size, Image.Resampling.LANCZOS)
        #             im.save(outfile, "JPEG")
        #         except IOError:
        #             print("cannot create thumbnail for '%s'" % fp)
        #     fp = outfile

        # Try OpenCV for image resizing
        if image_w is not None and image_h is not None and OPENCV_IMPORTED:
            outfile = os.path.splitext(fp)[0] + f"_{image_w}x{image_h}.jpeg"
            image = cv2.imread(fp)
            image = cv2.resize(
                image, (int(image_w), int(image_h)), interpolation=cv2.INTER_LINEAR
            )
            cv2.imwrite(outfile, image)
            fp = outfile

        resp = web.FileResponse(fp)
        logger.info(f"Image Proxy sending image: url={url}, path={fp}")
        return resp

    ########################################################################
    # JINJA2 FILTERS

    def _get_image_proxy_url(self, url):
        return (
            # f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={unquote(url)}"
            f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={quote_plus(url)}"
        )
        # return f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={unquote(url)}"

    def _convert_date_time(self, date_time_str, in_format, out_format):
        date_time_obj = datetime.strptime(date_time_str, in_format)
        return date_time_obj.strftime(out_format)

    def _today(self, input, out_format="%Y-%m-%d", offset_days=0):
        date_time = datetime.now() + timedelta(days=offset_days)
        return date_time.strftime(out_format)

    ########################################################################

    async def _widget_handler(self, request):
        """
        Handles requests to initialise a widget
        """

        data_dict = await request.json()
        logger.info(f"Message received: {data_dict}")

        if "data-widget" not in data_dict:
            logger.warning("No data-widget entry in msg data.")
            return
        if "target" not in data_dict:
            logger.warning("No target entry in msg data.")
            return
        if "subscription_id" not in data_dict:
            logger.warning("No subscription_id entry in msg data.")
            return

        # lazy load widget module
        widget_module = importlib.import_module(
            f".{data_dict['data-widget']}.{data_dict['data-widget']}",
            package="src.widgets",
        )

        # get queue
        queue = request.app["subscriptions"][data_dict["subscription_id"]]["queue"]
        # add widget instance to session widgets
        request.app["subscriptions"][data_dict["subscription_id"]]["widgets"].append(
            asyncio.create_task(
                widget_module.Widget(
                    request=request,
                    queue=queue,
                    protocol=self.protocol,
                    host=self.host,
                    port=self.port,
                    **data_dict,
                ).start()
            )
        )
        return web.Response(status=200)

    async def _widget_handler_old(self, request):
        """
        Handles requests to initialise a widget
        """

        data_dict = await request.json()
        logger.info(f"Message received: {data_dict}")

        if "data-widget" not in data_dict:
            logger.warning("No data-widget entry in msg data.")
            return
        if "target" not in data_dict:
            logger.warning("No target entry in msg data.")
            return
        if "subscription_id" not in data_dict:
            logger.warning("No subscription_id entry in msg data.")
            return

        # lazy load widget module
        widget_module = importlib.import_module(
            f".{data_dict['data-widget']}.{data_dict['data-widget']}",
            package="src.widgets",
        )

        # get queue
        queue = request.app["subscriptions"][data_dict["subscription_id"]]["queue"]
        # add widget instance to session widgets
        request.app["subscriptions"][data_dict["subscription_id"]]["widgets"].append(
            asyncio.create_task(
                widget_module.Widget(request=request, queue=queue, **data_dict).start()
            )
        )
        return web.Response(status=200)
