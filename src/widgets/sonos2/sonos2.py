from src.widgets.widget2.widget2 import Widget as BaseWidget
import sys

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
    type = "sonos"

    def update_context(self):
        self.context = self.data["data_source_topic"]["data"]


if __name__ == "__main__":

    import asyncio

    async def main():
        queue = asyncio.Queue()
        target = "test target"
        protocol = "http"
        host = "localhost"
        port = "8080"
        tasks = []
        for i in range(5):
            kwargs = {
                "data-source-topic": "data sources/sonos/Kitchen",
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
