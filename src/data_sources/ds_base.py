import asyncio
from gmqtt import Client as MQTTClient
import logging
import logging.handlers
from queue import Queue
import sys
import arrow

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

import nest_asyncio

nest_asyncio.apply()


def setup_logging_queue() -> None:
    """Move log handlers to a separate thread.

    Replace handlers on the root logger with a LocalQueueHandler,
    and start a logging.QueueListener holding the original
    handlers.

    """
    queue = Queue()
    root = logging.getLogger()

    handlers = []

    handler = logging.handlers.QueueHandler(queue)
    root.addHandler(handler)
    for h in root.handlers[:]:
        if h is not handler:
            root.removeHandler(h)
            handlers.append(h)

    listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    listener.start()


class BaseDataSource:
    #######################
    type = "base"
    wait_time = 1
    mqtt_connected = False

    def __init__(self, name=None):
        self.name = name

    async def start(self):
        self.mqtt_broker_host = None
        self.mqtt_client = None
        self.mqtt_topic = f"{self.type}/{self.name}"
        self.logger_prefix = f"data sources/{self.mqtt_topic}"
        self.mqtt_client = MQTTClient(self.mqtt_topic)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message_received
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_broker_host = "localhost"

        tasks = []
        try:
            tasks = [asyncio.create_task(self.main(self.mqtt_broker_host))]
            # gathering = await asyncio.gather(tasks)
            # print(gathering.count())
            while True:
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            # logger.info(f"{self.name} stopping datasource")
            for task in tasks:
                task.cancel()
        except Exception as e:
            print("main exception: ", e)

    async def get_data(self):
        return "data"

    async def main(self, broker_host):
        logger.info(
            f"{self.logger_prefix}: Starting main loop. Wait time between cycles: {self.wait_time}s"
        )

        await self.mqtt_client.connect(broker_host)
        while True:
            data = await self.get_data()
            logger.debug("received data")
            payload = {"data": data}
            logger.debug(payload)
            self.send_message(payload)
            await asyncio.sleep(self.wait_time)

    def send_message(self, payload):
        if self.mqtt_connected:
            payload["timestamp"] = arrow.utcnow().format()
            self.mqtt_client.publish(
                f"data sources/{self.mqtt_topic}", payload=payload, qos=1, retain=True
            )
            logger.debug("published data")
            self.on_message_sent(payload=payload)
        else:
            logger.warning(f"{self.logger_prefix}: Cannot send message. Disconnected.")

    def on_connect(self, client, flags, rc, properties):
        logger.info(f"{self.logger_prefix}: Connected")
        self.mqtt_connected = True
        self.mqtt_client.subscribe(f"data sources/{self.mqtt_topic}", qos=0)

    def on_message_received(self, client, topic, payload, qos, properties):
        return
        logger.info(f"{self.logger_prefix}: Message Received: {payload}")

    def on_message_sent(self, payload):
        logger.info(f"{self.logger_prefix}: Message Sent: {payload}")

    def on_disconnect(self, client, packet, exc=None):
        logger.info(f"{self.logger_prefix}: Disconnected")
        self.mqtt_connected = False

    def on_subscribe(self, client, mid, qos, properties):
        logger.info(f"{self.logger_prefix}: Subscribed...")


if __name__ == "__main__":

    async def main():
        tasks = []
        for i in range(5):
            datasource = BaseDataSource(name=i)
            tasks.append(asyncio.create_task(datasource.start()))
        await asyncio.gather(*tasks)

    asyncio.run(main())
