import asyncio

import logging
import aiohttp_jinja2

logger = logging.getLogger(__name__)

NAME = "clock"


class Widget:
    def __init__(self):
        self._data_dict = None
        self._request = None
        self._ws_identifier = None
        self._callback = None

    async def init(self, data_dict, request, ws_identifier, callback):
        logger.info(f"Initialising {NAME} widget:")
        logger.info(data_dict)
        self._data_dict = data_dict
        self._request = request
        self._ws_identifier = ws_identifier
        self._callback = callback

        refresh_timer = await self._get_param("data-refresh-timer", required=False)
        if refresh_timer is not None:
            asyncio.ensure_future(self._refresh_timer(refresh_timer))
        else:
            asyncio.ensure_future(self._refresh())

    async def _get_param(self, param, required=True):
        if param in self._data_dict:
            return self._data_dict[param]
        elif not required:
            return None
        logger.error(f"{param} required and not in config data:")
        logger.error(self._data_dict)

    async def _refresh_timer(self, refresh_timer):
        logging.info(f"Starting refresh timer ({refresh_timer} seconds).")
        refresh_timer = int(refresh_timer)
        while True:
            await self._refresh()
            await asyncio.sleep(refresh_timer)

    async def _refresh(self):
        # logging.info("Refreshing.")

        # create context dict
        context = {"time": 0}
        html = aiohttp_jinja2.render_string("clock.html", self._request, context)
        await self._callback(self._data_dict, self._request, self._ws_identifier, html)
        await asyncio.sleep(0)

    def __del__(self):
        logger.info(f"{NAME} widget deleted.")
