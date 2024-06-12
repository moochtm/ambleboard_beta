from src.widgets.widget2.widget2 import Widget as BaseWidget
import sys
import random
import urllib.parse

import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class Widget(BaseWidget):
    type = "slideshow"
    update_on_refresh_interval = False
    update_on_mqtt_message = True

    def update_context(self):
        try:
            data = self.data["data_source_topic"]["data"]

            for item in ["current_item", "next_item", "preload_item"]:
                if item not in self.context.keys():
                    n = random.randrange(0, len(data))
                    self.context[item] = {
                        "url": f"http://{self.host}:8888/unsafe/2160x1600/smart/{data[n]['url']}"
                    }

            self.context["current_item"] = self.context["next_item"]
            self.context["next_item"] = self.context["preload_item"]
            n = random.randrange(0, len(data))
            self.context["preload_item"] = {
                "url": f"http://{self.host}:8888/unsafe/2160x1600/smart/{urllib.parse.quote_plus(data[n]['url'])}"
            }

            print("????????????????????????????????????????????????????????")
            print(self.context)

        except Exception as e:
            print("main exception: ", e)


if __name__ == "__main__":

    import asyncio

    async def main():
        queue = asyncio.Queue()
        target = "test target"
        protocol = "http"
        host = "localhost"
        port = "8080"
        tasks = []
        for i in range(1):
            kwargs = {
                "data-source-topic": "data sources/google_photos/ambleboard",
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
