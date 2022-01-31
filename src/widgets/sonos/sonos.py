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

# TODO: get metadata for next in queue
# TODO: trigger next image being downloaded using hidden img tag


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

        def event_handler(event):
            logger.info(f"SONOS event received: device={device.player_name}")
            transport_info = device.get_current_transport_info()
            logger.debug(f"transport info: {transport_info}")
            track_info = device.get_current_track_info()
            logger.debug(f"track info: {track_info}")
            media_info = device.get_current_media_info()
            logger.debug(f"media info: {media_info}")
            volume = device.volume
            logger.debug(f"volume: {volume}")

            transport = transport_info["current_transport_state"]
            img_src = track_info["album_art"]
            if img_src != "":
                title = track_info["title"]
                artist = track_info["artist"]
                album = track_info["album"]
            # if there's no img_src in track info, we might be playing a radio station
            else:
                channel = media_info["channel"]
                tunein = MusicService("TuneIn")
                # search Tunein for value of channel
                results = tunein.search(category="stations", term=channel)
                if len(results) > 0:
                    result = results[0]
                    img_src = result.metadata["stream_metadata"].metadata["logo"]
                title = channel
                artist = ""
                album = ""
            # create context dict
            context = {
                "transport": transport,
                "title": title,
                "artist": artist,
                "album": album,
                "img_src": img_src,
                "volume": int(volume),
            }
            publisher.publish(publish_key, context)
            type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context

        sub = await device.avTransport.subscribe()
        sub.callback = event_handler
        rendering_sub = await device.renderingControl.subscribe()
        rendering_sub.callback = event_handler

        while True:
            await asyncio.sleep(0)
