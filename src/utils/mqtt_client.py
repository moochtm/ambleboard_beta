import asyncio
from gmqtt import Client as GmqttMqttClient
import json
import logging
import logging.handlers
import nest_asyncio
import sys
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


class MQTTClient:
    def __init__(self, name, topic, queue=None):
        self.name = name
        self.topic = topic
        self.queue = queue
        self.mqtt_client = GmqttMqttClient(uuid.uuid4().__str__()[:4])
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
            self.log(logging.INFO, f"Stopping mqtt client")
            self.mqtt_client.unsubscribe(self.topic)
            await self.mqtt_client.disconnect()
        except Exception as e:
            print("main exception: ", e)

    async def disconnect(self):
        await self.mqtt_client.disconnect()

    def on_connect(self, client, flags, rc, properties):
        self.log(logging.INFO, f"Connected")
        self.mqtt_client.subscribe(f"{self.topic}", qos=0)

    def on_message_received(self, client, topic, payload, qos, properties):
        payload = json.loads(payload)
        self.log(logging.INFO, f"Message Received: {payload}")
        payload["data_source_id"] = self.name
        if self.queue is not None:
            self.queue.put_nowait(payload)

    def on_disconnect(self, client, packet, exc=None):
        self.log(logging.INFO, f"Disconnected")

    def on_subscribe(self, client, mid, qos, properties):
        self.log(logging.INFO, f"Subscribed.")

    def send_message(self, payload):
        self.log(logging.INFO, f"Sending Message: {payload}")
        self.mqtt_client.publish(f"{self.topic}", payload=payload, qos=1, retain=True)

    def log(self, log_level, msg):
        logger.log(level=log_level, msg=f"{self.topic}/mqtt_client[{self.name}]: {msg}")
