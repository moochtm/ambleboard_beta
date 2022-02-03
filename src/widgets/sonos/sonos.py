import aiopubsub
import asyncio
from src.widgets.widget.widget import Widget as BaseWidget

import soco
from soco import events_asyncio
from soco.music_services import MusicService
from soco.exceptions import SoCoException

import logging

logger = logging.getLogger(__name__)

soco.config.EVENTS_MODULE = events_asyncio


class Widget(BaseWidget):
    widget_name = "SONOS"
    worker_is_running = False
    worker_msg_queue = aiopubsub.Hub()
    worker_prev_update = {}

    async def _start_worker_publishers(self, publisher):
        ######################################################
        # Below depends on the number of publishers
        for device in soco.discovery.discover():
            asyncio.ensure_future(self._start_publishing(publisher, device))
        # while True:
        #    await asyncio.sleep(0)

    async def _start_publishing(self, publisher, device):
        ###############################################
        # Below depends on the publisher details
        publish_key = aiopubsub.Key(device.player_name)

        context = {"av_transport": {}, "rendering_control": {}}

        def av_transport_event_handler(event):
            logger.info(
                f"SONOS av_transport event received: device={device.player_name}, event.variables={event.variables}"
            )
            context["av_transport"] = event.variables
            # convert values that are soco.data_structures (e.g. music track metadata) to dicts
            for key, value in context["av_transport"].items():
                if "soco.data_structures" in str(type(value)):
                    context["av_transport"][key] = value.to_dict()
                    # create FULL uri for album art
                    if "album_art_uri" in context["av_transport"][key]:
                        context["av_transport"][key][
                            "album_art_uri"
                        ] = f"http://{device.ip_address}:1400{context['av_transport'][key]['album_art_uri']}"

            # helper: add current_track_exists:
            context["av_transport"]["current_track_exists"] = (
                False
                if context["av_transport"]["current_track_meta_data"]["title"] == " "
                else True
            )

            # helper: add next_track_exists:
            context["av_transport"]["next_track_exists"] = (
                False if context["av_transport"]["next_track_meta_data"] == "" else True
            )

            print(context)

            publisher.publish(publish_key, context)
            type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context

        def rendering_control_event_handler(event):
            logger.info(
                f"SONOS rendering_control event received: device={device.player_name}, event.variables={event.variables}"
            )
            context["rendering_control"] = event.variables
            logging.debug(f"Created context: {context}")

            publisher.publish(publish_key, context)
            type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context

        sub = await device.avTransport.subscribe(auto_renew=True)
        sub.callback = av_transport_event_handler
        rendering_sub = await device.renderingControl.subscribe(auto_renew=True)
        rendering_sub.callback = rendering_control_event_handler

        while True:
            await asyncio.sleep(0)
