import asyncio
from datetime import datetime, timedelta
import importlib
from urllib.parse import quote_plus

from gmqtt import Client as MQTTClient
from src.utils.mqtt_client import MQTTClient
import jinja2
import json
import logging
import logging.handlers
import nest_asyncio
import os
import copy
import re
import sys
import traceback
import arrow
import uuid
from bs4 import BeautifulSoup

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

nest_asyncio.apply()

####################################################################################################
####################################################################################################


class Widget:
    #######################
    type = "base_widget"
    update_on_mqtt_message = True
    update_on_refresh_interval = False

    def __init__(self, queue, target, protocol, host, port, **kwargs):

        # Setup things common to all Widgets
        self._queue = queue
        self._target = target
        self.protocol = protocol
        self.host = host
        self.port = port
        new_keys = {key: key.replace("-", "_") for key in kwargs.keys()}
        self._kwargs = {new_keys[key]: value for key, value in kwargs.items()}

        self._refresh_interval = (
            self._kwargs["data_refresh_interval"]
            if "data_refresh_interval" in self._kwargs
            else 0
        )
        self._first_message_sent = False

        # Find and load the template HTML for the Widget
        m = importlib.import_module(self.__module__)
        # print(os.getcwd())
        # print(os.path.dirname(m.__file__))
        # print(os.path.dirname(__file__))
        # print(os.path.relpath(os.path.dirname(m.__file__), os.getcwd()))

        self._template_html_path = os.path.splitext(m.__file__)[0] + ".html"
        if not os.path.exists(self._template_html_path):
            logger.error("Template HTML file doesn't exist")
            msg = {
                "msg": f"Template HTML file doesn't exist: {self._template_html_path}"
            }
            logger.warning(msg)
            self.__render_widget_html_and_send_to_server_queue(msg)
            return
        else:
            # JINJA INIT
            jinja2_filters = {
                "image_proxy": self._get_image_proxy_url,
                "convert_date_time": self._convert_date_time,
                "today": self._today,
                "delta_days": self._delta_days,
                "max": self._max,
                "min": self._min,
            }
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(
                    os.path.relpath(os.path.dirname(m.__file__), os.getcwd())
                ),
                autoescape=True,
                enable_async=True,
            )
            # print(os.path.splitext(os.path.basename(m.__file__))[0] + ".html")
            env.filters = jinja2_filters
            with open(self._template_html_path, "r") as f:
                self.jinja2_template = env.get_template(
                    os.path.splitext(os.path.basename(m.__file__))[0] + ".html"
                )

        self.data = {}
        self.context = {}

    async def start(self):
        tasks = []
        queue = asyncio.Queue()
        try:
            # Create MQTT clients if there are any data-source-topics
            ds_topics = [arg for arg in self._kwargs if "data_source_topic" in arg]
            for ds_topic in ds_topics:
                client = MQTTClient(
                    name=ds_topic,
                    topic=self._kwargs[ds_topic],
                    queue=queue,
                )
                tasks.append(asyncio.create_task(client.connect()))
            if len(ds_topics) > 0:
                tasks.append(
                    asyncio.create_task(self.__mqtt_client_queue_worker(queue=queue))
                )

            while True:
                if self.update_on_refresh_interval and self.data is not {}:
                    self.update_context()
                    await self.__render_widget_html_and_send_to_server_queue()
                await asyncio.sleep(int(self._refresh_interval))
        except asyncio.CancelledError:
            logger.info(f"{type(self).type} stopping widget")
            # for client in self.mqtt_clients:
            #     await client.disconnect()
            for task in tasks:
                task.cancel()
        except Exception as e:
            print("main exception: ", e)

    async def __mqtt_client_queue_worker(self, queue):

        while True:
            # Get a "work item" out of the queue.
            payload = await queue.get()

            # do the work
            logger.info(f"widget worker received message: {payload}")
            self.data[payload["data_source_id"]] = payload
            if self.update_on_mqtt_message or self._first_message_sent == False:
                self.update_context()
                await self.__render_widget_html_and_send_to_server_queue()

            # Notify the queue that the "work item" has been processed.
            queue.task_done()

    def update_context(self):
        self.context = self.data["data_source_topic"]

    async def __render_widget_html_and_send_to_server_queue(self):
        logger.info(f"Rendering context: {self.context}")
        try:
            html = self.jinja2_template.render(self.context)
            # remove comments
            html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
            # remove new lines
            # html = html.strip("\n")
            # html = re.sub(r"[\n\t\s]*", "", html)
            # prettify
            # soup = BeautifulSoup(html, features="lxml")
            # html = soup.prettify()
        except Exception as e:
            html = "<p>Widget could not be rendered!</p>"
            traceback.print_exc()
            logger.error("Widget could not be rendered!")
        payload = {
            "target": self._target,
            "widget": type(self).type.lower(),
            "html": html,
        }
        logger.info(
            f"{type(self).type} instance sending payload to subscription queue: {payload}"
        )
        await self._queue.put(json.dumps(payload))
        self._first_message_sent = True

    ########################################################################
    # JINJA2 FILTERS

    def _get_image_proxy_url(self, url):
        return (
            # f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={unquote(url)}"
            f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={quote_plus(url)}"
        )
        # return f"{self.protocol}://{self.host}:{self.port}/image_proxy?url={unquote(url)}"

    def _convert_date_time(self, date_time_str, in_format, out_format):
        date_time_obj = datetime.fromisoformat(date_time_str)
        return date_time_obj.strftime(out_format)

    def _today(self, input, out_format="%Y-%m-%d", offset_days=0):
        date_time = datetime.now() + timedelta(days=offset_days)
        return date_time.strftime(out_format)

    def _delta_days(self, first_date, second_date):
        return (arrow.get(first_date) - arrow.get(second_date)).days

    def _max(self, a, b):
        return max(a, b)

    def _min(self, a, b):
        return min(a, b)


####################################################################################################
####################################################################################################

if __name__ == "__main__":

    async def main():
        queue = asyncio.Queue()
        target = "test target"
        protocol = "http"
        host = "localhost"
        port = "8080"
        tasks = []
        for i in range(1):
            kwargs = {
                "data-refresh-interval": 0,
                "data-source-topic": "data sources/counter/None",
            }
            datasource = Widget(queue, target, protocol, host, port, **kwargs)
            tasks.append(asyncio.create_task(datasource.start()))

        async def queue_worker():
            try:
                while True:
                    payload = await queue.get()
                    logger.info(f"test server received message: {payload}")
                    queue.task_done()
                    await asyncio.sleep(0)
            except asyncio.CancelledError:
                logger.info(f"queue_worker task cancelled")
            except Exception as e:
                print("main exception: ", e)

        tasks.append(asyncio.create_task(queue_worker()))

        # for task in tasks:
        #     asyncio.ensure_future(task)

        # for i in range(5):
        #     print(i)
        #     await asyncio.sleep(1)
        #
        # for task in tasks:
        #     print("cancelling task")
        #     task.cancel()
        #     await task

        while True:
            await asyncio.sleep(0)

    asyncio.run(main())
