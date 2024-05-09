import asyncio
from gmqtt import Client as MQTTClient
import jinja2
import json
import logging
import logging.handlers
import nest_asyncio
import os
import sys
import traceback
import uuid

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

nest_asyncio.apply()


class WidgetMQTTClient:
    def __init__(self, name, topic, queue):
        self.name = name
        self.topic = topic
        self.queue = queue
        self.mqtt_client = MQTTClient(uuid.uuid4().__str__()[:4])
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message_received
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_broker_host = "localhost"

    async def connect(self):
        try:
            await self.mqtt_client.connect(self.mqtt_broker_host)
            while True:
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            logger.info(f"Stopping mqtt client")
            self.mqtt_client.unsubscribe(self.topic)
            await self.mqtt_client.disconnect()
        except Exception as e:
            print("main exception: ", e)

    async def disconnect(self):
        await self.mqtt_client.disconnect()

    def on_connect(self, client, flags, rc, properties):
        logger.info(f"Connected")
        self.mqtt_client.subscribe(f"{self.topic}", qos=0)

    def on_message_received(self, client, topic, payload, qos, properties):
        payload = json.loads(payload)
        logger.info(f"Message Received: {payload}")
        payload["data_source_id"] = self.name
        self.queue.put_nowait(payload)

    def on_disconnect(self, client, packet, exc=None):
        logger.info(f"Disconnected")

    def on_subscribe(self, client, mid, qos, properties):
        logger.info(f"Subscribed.")


class Widget:
    #######################
    type = "base_widget"
    update_on_mqtt_message = True
    update_on_refresh_interval = False

    def __init__(self, queue, target, **kwargs):

        # Setup things common to all Widgets
        self._queue = queue
        self._target = target
        self._kwargs = kwargs
        self._refresh_interval = (
            kwargs["data-refresh-interval"] if "data-refresh-interval" in kwargs else 0
        )

        # Find and load the template HTML for the Widget
        self._template_html_path = os.path.splitext(__file__)[0] + ".html"
        if not os.path.exists(self._template_html_path):
            logger.error("Template HTML file doesn't exist")
            msg = {
                "msg": f"Template HTML file doesn't exist: {self._template_html_path}"
            }
            logger.warning(msg)
            self.__render_widget_html_and_send_to_server_queue(msg)
            return
        else:
            with open(self._template_html_path, "r") as f:
                self.jinja2_template = jinja2.Template(f.read(), enable_async=True)

        self.data = {}
        self.context = {}

    async def start(self):
        tasks = []
        queue = asyncio.Queue()
        try:
            # Create MQTT clients if there are any data-source-topics
            ds_topics = [arg for arg in self._kwargs if "data-source-topic" in arg]
            for ds_topic in ds_topics:
                client = WidgetMQTTClient(
                    name=ds_topic.replace("-", "_"),
                    topic=self._kwargs[ds_topic],
                    queue=queue,
                )
                tasks.append(asyncio.create_task(client.connect()))
            if len(ds_topics) > 0:
                tasks.append(
                    asyncio.create_task(self.__mqtt_client_queue_worker(queue=queue))
                )

            while True:
                await asyncio.sleep(0)
            # while True:
            #     if self.update_on_refresh_interval:
            #         self.update_context()
            #         await self.__render_widget_html_and_send_to_server_queue()
            #     await asyncio.sleep(self._refresh_interval)
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
            if self.update_on_mqtt_message:
                self.update_context()
                await self.__render_widget_html_and_send_to_server_queue()

            # Notify the queue that the "work item" has been processed.
            queue.task_done()

    def update_context(self):
        self.context = self.data

    async def __render_widget_html_and_send_to_server_queue(self):
        logger.info(f"Rendering context: {self.context}")
        try:
            html = self.jinja2_template.render(self.context)
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


if __name__ == "__main__":

    async def main():
        queue = asyncio.Queue()
        target = "test target"
        tasks = []
        for i in range(1):
            kwargs = {
                "data-refresh-interval": 0,
                "data-source-topic": "data sources/counter/None",
            }
            datasource = Widget(queue, target, **kwargs)
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

        for i in range(5):
            print(i)
            await asyncio.sleep(1)

        for task in tasks:
            print("cancelling task")
            task.cancel()
            await task

        while True:
            continue

    asyncio.run(main())
