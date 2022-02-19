import aiopubsub
from src.widgets.widget.widget import Widget as BaseWidget
from src.oauth.google_oauth import GoogleAsyncOauthClient
import os
from pathlib import Path
import asyncio

import logging

logger = logging.getLogger(__name__)

############################################################################
# WIDGET
############################################################################


class Widget(BaseWidget):
    widget_name = "GOOGLE PHOTOS"
    worker_is_running = False
    worker_msg_queue = aiopubsub.Hub()
    worker_prev_update = {}

    async def _start_instance(self):
        try:
            required_args = ["data-channel", "data-refresh-interval", "data-user"]
            missing_args = [arg for arg in required_args if arg not in self._kwargs]
            if missing_args:
                msg = {"msg": f"Missing attributes: {missing_args}"}
                logger.warning(msg)
                await self._render_widget_html_and_send_to_queue(msg)
                await asyncio.sleep(0)
                return

            user_id = self._kwargs["data-user"]
            album_title = self._kwargs["data-channel"]
            refresh_interval = self._kwargs["data-refresh-interval"]

            self.client = GoogleAsyncOauthClient(user_id=user_id)

            # Get all Albums to find ID
            msg = {"msg": f"Finding album: {album_title}"}
            await self._render_widget_html_and_send_to_queue(msg)
            params = {"pageSize": 50, "pageToken": ""}
            result = []
            response = await self.client.async_request(
                "get", "https://photoslibrary.googleapis.com/v1/albums", params=params
            )
            result += response["albums"]
            while "nextPageToken" in response:
                params = {"pageSize": 50, "pageToken": response["nextPageToken"]}
                response = await self.client.async_request(
                    "get",
                    "https://photoslibrary.googleapis.com/v1/albums",
                    params=params,
                )
                result += response["albums"]

            album = [item for item in result if item["title"] == album_title][0]

            # Get all mediaItems in Album
            msg = {"msg": f"Getting photos from album: {album_title}"}
            await self._render_widget_html_and_send_to_queue(msg)
            body = {"albumId": album["id"], "pageSize": 100, "pageToken": ""}
            media_items = []
            response = await self.client.async_request(
                "post",
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                data=body,
            )
            media_items += response["mediaItems"]
            while "nextPageToken" in response:
                body = {
                    "albumId": album["id"],
                    "pageSize": 100,
                    "pageToken": response["nextPageToken"],
                }
                response = await self.client.async_request(
                    "post",
                    "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                    data=body,
                )
                media_items += response["mediaItems"]

            # Start the loop
            current_i = 0
            while True:
                next_i = current_i + 1 if current_i + 1 < len(media_items) else 0
                msg = {
                    "album": album,
                    "current_item": media_items[current_i],
                    "next_item": media_items[next_i],
                }
                ###################################
                await self._render_widget_html_and_send_to_queue(msg)
                ###################################
                await asyncio.sleep(int(refresh_interval))
                current_i = next_i
        except asyncio.CancelledError:
            await self.client.close_session()

    async def _start_worker_publishers(self, publisher):
        ######################################################
        # Below depends on the number of publishers
        return

    async def _start_publishing(self, publisher):
        ###############################################
        # Below depends on the publisher details
        return
