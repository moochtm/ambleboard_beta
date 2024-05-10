import asyncio
from gmqtt import Client as MQTTClient
import logging
from logging.handlers import TimedRotatingFileHandler
from queue import Queue
import sys, os
import arrow

# SET UP LOGGING
logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # TimedRotatingFileHandler(
        #     filename=os.path.splitext(os.path.basename(__file__))[0] + ".log",
        #     when="H",
        #     interval=6,
        #     backupCount=12,
        # ),
    ],
)
logger = logging.getLogger(__name__)

import nest_asyncio

nest_asyncio.apply()

import socket


def internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


class BaseDataSource:
    #######################
    type = "base"
    wait_time = 5
    mqtt_connected = False
    local_network_required = True

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
            while True:
                await asyncio.sleep(0)
        except asyncio.CancelledError:
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
            if internet():
                data = await self.get_data()
                logger.debug("received data")
                payload = {"data": data}
                logger.debug(payload)
                self.send_message(payload)
            else:
                logger.warning("no internet, will try again next time...")
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
