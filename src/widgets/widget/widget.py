import asyncio
import json
import logging
import aiopubsub
import aiohttp_jinja2
import traceback

logger = logging.getLogger(__name__)


class Widget:
    #######################
    widget_name = "WIDGET"
    #######################
    worker_is_needed = True
    worker_is_running = False
    worker_msg_queue = aiopubsub.Hub()
    worker_prev_update = {}

    def __init__(self, request, queue, target, **kwargs):
        self._request = request
        self._queue = queue
        self._target = target
        self._channel = (
            kwargs["data-channel"]
            if "data-channel" in kwargs
            else type(self).widget_name.upper()
        )
        self._template = (
            f"{kwargs['data-widget']}_{kwargs['data-template']}"
            if "data-template" in kwargs
            else kwargs["data-widget"]
        )
        self._kwargs = kwargs
        self._subscriber = None
        logger.info(f"{type(self).widget_name} widget created.")
        logger.info(f"Kwargs: {self._kwargs}")

    async def start(self):
        try:
            tasks = []
            if type(self).worker_is_needed:
                tasks.append(asyncio.create_task(self._start_class_worker()))
            tasks.append(asyncio.create_task(self._start_instance()))
            # gathering = await asyncio.gather(tasks)
            # print(gathering.count())
            while True:
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            logger.info(f"{type(self).widget_name} stopping widget")
            for task in tasks:
                task.cancel()
            if self._subscriber:
                await self._subscriber.remove_all_listeners()
        except Exception as e:
            print("main exception: ", e)

    async def _start_instance(self):
        try:

            async def listener(key: aiopubsub.Key, arg: dict):
                logger.info(f"{type(self).widget_name} instance listener: {key}, {arg}")
                await self._render_widget_html_and_send_to_queue(arg)

            self._subscriber = aiopubsub.Subscriber(
                type(self).worker_msg_queue, type(self).widget_name
            )
            subscribe_key = aiopubsub.Key(type(self).widget_name, self._channel)
            self._subscriber.add_async_listener(subscribe_key, listener)

            while True:
                await asyncio.sleep(0)
        except asyncio.CancelledError:
            logger.info(f"{type(self).widget_name} stopping widget instance")

    async def _render_widget_html_and_send_to_queue(self, arg):
        logger.info(f"Rendering context: {arg}")
        try:
            html = aiohttp_jinja2.render_string(
                f"widget_{self._template}.html", self._request, arg
            )
        except Exception as e:
            html = "<p>Widget could not be rendered!</p>"
            traceback.print_exc()
            logger.error("Widget could not be rendered!")
        payload = {
            "target": self._target,
            "widget": type(self).widget_name.lower(),
            "html": html,
        }
        logger.info(
            f"{type(self).widget_name} instance sending payload to subscription queue."
        )
        await self._queue.put(json.dumps(payload))

    async def _start_class_worker(self):
        if type(self).worker_is_running:
            return
        type(self).worker_is_running = True

        publisher = aiopubsub.Publisher(
            type(self).worker_msg_queue, prefix=aiopubsub.Key(type(self).widget_name)
        )
        await self._start_worker_publishers(publisher)
        await self._start_worker_listener(publisher)

        while True:
            await asyncio.sleep(0.01)

    async def _start_worker_listener(self, publisher):
        """
        Creates a listener to hear SubscriberCount events and repeat last message.
        This means new widget instances immediately receive an update message.
        """

        async def listener(key: aiopubsub.Key, arg: dict):
            logger.info(f"{type(self).widget_name} worker listener: {key}, {arg}")
            try:
                if "currentSubscriberCount" in arg:
                    # Remove 1st element from key, as this is publisher prefix
                    publisher.publish(
                        arg["key"][1:], type(self).worker_prev_update[str(arg["key"])]
                    )
                    logger.info(
                        f"SubscriberCount changed. Repeated last message. key={str(arg['key'])}, msg={type(self).worker_prev_update[str(arg['key'])]}"
                    )
            except KeyError as e:
                logger.warning(f"KeyError: {str(arg['key'])}")

        self._subscriber = aiopubsub.Subscriber(
            type(self).worker_msg_queue, type(self).widget_name
        )
        subscribe_key = aiopubsub.Key("Hub", "*")
        self._subscriber.add_async_listener(subscribe_key, listener)
        logger.info(f"{type(self).widget_name} added worker listener")

    async def _start_worker_publishers(self, publisher):
        ######################################################
        # Below depends on the number of publishers
        asyncio.create_task(self._start_publishing(publisher))

    async def _start_publishing(self, publisher):
        ###############################################
        # Below depends on the publisher details
        publish_key = aiopubsub.Key(type(self).widget_name)
        count = 0
        while True:
            count += 1
            msg = {"count": count}
            publisher.publish(publish_key, msg)
            logger.debug(f"worker publishing: {msg}")
            type(self).worker_prev_update[str(publisher.prefix + publish_key)] = msg
            await asyncio.sleep(20)
