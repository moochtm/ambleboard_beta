import asyncio
import soco
from soco import events_asyncio
from soco.music_services import MusicService
from soco.exceptions import SoCoException

import logging
import aiohttp_jinja2

logger = logging.getLogger(__name__)

soco.config.EVENTS_MODULE = events_asyncio


class Widget:
    def __init__(self):
        self._data_dict = None
        self._request = None
        self._ws_identifier = None
        self._callback = None
        self._sonos = None
        self._sonos_name = None

    async def init(self, data_dict, request, ws_identifier, callback):
        logger.info("Initialising sonos widget:")
        logger.info(data_dict)
        self._data_dict = data_dict
        self._request = request
        self._ws_identifier = ws_identifier
        self._callback = callback

        self._sonos_name = await self._get_param("data-sonos-name")
        self._sonos = await self._get_sonos()
        refresh_timer = await self._get_param("data-refresh-timer", required=False)
        if refresh_timer is not None:
            asyncio.ensure_future(self._refresh_timer(refresh_timer))
        else:
            asyncio.ensure_future(self._subscribe())

    async def _get_param(self, param, required=True):
        if param in self._data_dict:
            return self._data_dict[param]
        elif not required:
            return None
        logger.error(f"{param} required and not in config data:")
        logger.error(self._data_dict)

    async def _get_sonos(self):
        try:
            return soco.discovery.by_name(self._sonos_name)
        except SoCoException:
            logger.error(f"Cannot get Sonos called {self._sonos_name}.")

    async def _refresh_timer(self, refresh_timer):
        logging.info(f"Starting refresh timer ({refresh_timer} seconds).")
        refresh_timer = int(refresh_timer)
        while True:
            await self._refresh()
            await asyncio.sleep(refresh_timer)

    async def _refresh(self):
        # logging.info("Refreshing.")
        try:
            transport_info = self._sonos.get_current_transport_info()
            logger.debug(f"transport info: {transport_info}")
            track_info = self._sonos.get_current_track_info()
            logger.debug(f"track info: {track_info}")
            media_info = self._sonos.get_current_media_info()
            logger.debug(f"media info: {media_info}")
            volume = self._sonos.volume
            logger.debug(f"volume: {volume}")
        except SoCoException:
            logger.error(f"Cannot get info from Sonos")
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
        html = aiohttp_jinja2.render_string("sonos.html", self._request, context)
        await self._callback(self._data_dict, self._request, self._ws_identifier, html)
        await asyncio.sleep(0)

    async def _subscribe(self):
        sonos_name = self._sonos_name
        logging.info(f"Subscribing to Sonos ({sonos_name})")

        def event_handler(event):
            logging.info(f"Event from Sonos ({sonos_name}): {event.variables}")
            # logging.info(event.variables)
            asyncio.get_event_loop().create_task(self._refresh())

        transport_sub = await self._sonos.avTransport.subscribe()
        transport_sub.callback = event_handler
        rendering_sub = await self._sonos.renderingControl.subscribe()
        rendering_sub.callback = event_handler

        while True:
            await asyncio.sleep(0)

    def __del__(self):
        logger.info("Sonos widget deleted.")
