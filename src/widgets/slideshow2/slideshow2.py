from src.widgets.widget2.widget2 import Widget as BaseWidget
import sys
import random

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
    update_on_mqtt_message = True
    update_on_refresh_interval = True

    def update_context(self):
        if "current_item" not in self.context.keys():
            self.context["current_item"] = {"url": None}
        if "next_item" not in self.context.keys():
            self.context["next_item"] = {"url": None}
        print(self.context)

        try:
            data = self.data["data_source_topic"]["data"]
            print(data)
            if self.context["next_item"]["url"] is not None:
                self.context["current_item"]["url"] = self.context["next_item"]["url"]
            else:
                n = random.randrange(0, len(data))
                self.context["current_item"]["url"] = data[n]["url"]

            n = random.randrange(0, len(data))
            self.context["next_item"]["url"] = data[n]["url"]
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
