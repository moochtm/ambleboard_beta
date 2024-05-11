import asyncio
from utils.mqtt_client import MQTTClient
import logging
from logging.handlers import TimedRotatingFileHandler
from queue import Queue
import sys, os
import arrow
import uuid

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
        logger.error(ex)
        return False


class BaseDataSource:
    #######################
    type = "base"
    wait_time = 5
    mqtt_connected = False
    local_network_required = True

    def __init__(self, name=None):
        self.mqtt_client = None
        self.name = name
        self.mqtt_topic = f"data sources/{self.type}/{self.name}"

    async def start(self):
        tasks = []
        try:
            self.log(
                logging.INFO,
                f"Starting main loop. Wait time between cycles: {self.wait_time}s",
            )
            self.mqtt_client = MQTTClient(
                name=uuid.uuid4().__str__()[:4], topic=self.mqtt_topic
            )
            tasks = [
                asyncio.create_task(self.mqtt_client.connect()),
                # asyncio.create_task(self.main()),
            ]
            while True:
                if internet():
                    data = await self.get_data()
                    self.log(logging.DEBUG, "received data")
                    payload = {"data": data, "timestamp": arrow.utcnow().format()}
                    self.log(logging.DEBUG, payload)
                    try:
                        self.mqtt_client.send_message(payload)
                        self.log(logging.DEBUG, "published data")
                    except Exception as e:
                        self.log(logging.ERROR, type(e))
                        self.log(logging.ERROR, e)
                else:
                    self.log(
                        logging.WARNING, "no internet, will try again next time..."
                    )
                await asyncio.sleep(self.wait_time)
        except asyncio.CancelledError:
            self.log(logging.INFO, "Widget task cancelled. Stopping sub-tasks.")
            for task in tasks:
                task.cancel()
        except Exception as e:
            self.log(logging.ERROR, type(e))
            self.log(logging.ERROR, e)

    async def get_data(self):
        return "data"

    def log(self, log_level, msg):
        logger.log(
            level=log_level, msg=f"{self.mqtt_topic}/mqtt_client[{self.name}]: {msg}"
        )


if __name__ == "__main__":

    async def main():
        tasks = []
        for i in range(5):
            datasource = BaseDataSource(name=i)
            tasks.append(asyncio.create_task(datasource.start()))
        await asyncio.sleep(5)
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks)

    asyncio.run(main())
