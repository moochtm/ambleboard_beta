import aiopubsub
import asyncio
from src.widgets.widget.widget import Widget as BaseWidget
import json
import arrow

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
                    # create FULL uri for album art (if 'http' not found in current value).
                    if "album_art_uri" in context["av_transport"][key]:
                        if (
                            context["av_transport"][key]["album_art_uri"][:4] != "http"
                            and context["av_transport"][key]["album_art_uri"].strip()
                            != ""
                        ):
                            context["av_transport"][key][
                                "album_art_uri"
                            ] = f"http://{device.ip_address}:1400{context['av_transport'][key]['album_art_uri']}"

            # helper: add current_track_exists:
            context["av_transport"]["current_track_exists"] = (
                False
                if context["av_transport"]["current_track_meta_data"] == ""
                or context["av_transport"]["current_track_meta_data"]["title"].strip()
                == ""
                else True
            )

            # helper: add next_track_exists:
            context["av_transport"]["next_track_exists"] = (
                False
                if context["av_transport"]["next_track_meta_data"] == ""
                or context["av_transport"]["next_track_meta_data"]["title"].strip()
                == ""
                else True
            )

            # add device info to context
            # https://docs.python-soco.com/en/latest/api/soco.core.html
            # this code is duplicated below
            context["device_info"] = {
                "player_name": device.player_name,
                "ip_address": device.ip_address,
                "play_mode": device.play_mode,
                "shuffle": device.shuffle,
                "repeat": device.repeat,
                "mute": device.mute,
                "volume": device.volume,
                "is_playing_radio": device.is_playing_radio,
                "is_playing_tv": device.is_playing_tv,
                "music_source": device.music_source,
            }

            logger.info(f"Sonos Created context: {context}")

            publisher.publish(publish_key, context)
            type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context

        def rendering_control_event_handler(event):
            logger.info(
                f"SONOS rendering_control event received: device={device.player_name}, event.variables={event.variables}"
            )
            context["rendering_control"] = event.variables

            # add device info to context
            # https://docs.python-soco.com/en/latest/api/soco.core.html
            # this code is duplicated above
            context["device_info"] = {
                "player_name": device.player_name,
                "ip_address": device.ip_address,
                "play_mode": device.play_mode,
                "shuffle": device.shuffle,
                "repeat": device.repeat,
                "mute": device.mute,
                "volume": device.volume,
                "is_playing_radio": device.is_playing_radio,
                "is_playing_tv": device.is_playing_tv,
                "music_source": device.music_source,
            }

            logging.debug(f"Created context: {json.dumps(context, indent=4)}")

            publisher.publish(publish_key, context)
            type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context

        sub = await device.avTransport.subscribe(auto_renew=True)
        sub.callback = av_transport_event_handler
        rendering_sub = await device.renderingControl.subscribe(auto_renew=True)
        rendering_sub.callback = rendering_control_event_handler

        while True:
            await asyncio.sleep(0)
