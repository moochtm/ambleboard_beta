import aiopubsub
from src.widgets.widget.widget import Widget as BaseWidget
from src.oauth.google_oauth import GoogleAsyncOauthClient
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

            async def send_please_authenticate(provider):
                msg = {
                    "msg": f"Please authenticate '{provider}' and refresh the webpage."
                }
                logger.warning(msg)
                await self._render_widget_html_and_send_to_queue(msg)
                await asyncio.sleep(0)
                return

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
            if not self.client.load_token():
                await send_please_authenticate("google")
                return

            # Get all Albums to find ID
            msg = {"msg": f"Finding album: {album_title}"}
            logger.info(f"Finding album: {album_title}")
            await self._render_widget_html_and_send_to_queue(msg)
            params = {"pageSize": 50, "pageToken": ""}
            result = []
            response = await self.client.async_request(
                "get", "https://photoslibrary.googleapis.com/v1/albums", params=params
            )
            result += response["albums"]
            while "nextPageToken" in response:
                logger.info(f"Finding album: {album_title}: Getting next page.")
                params = {"pageSize": 50, "pageToken": response["nextPageToken"]}
                response = await self.client.async_request(
                    "get",
                    "https://photoslibrary.googleapis.com/v1/albums",
                    params=params,
                )
                result += response["albums"]

            album = [item for item in result if item["title"] == album_title][0]

            media_items = await self._get_media_items_in_album(album)

            # GET an initial current_item
            current_item = await self.client.async_request(
                "get",
                f"https://photoslibrary.googleapis.com/v1/mediaItems/{media_items[0]['id']}",
            )
            # GET an initial next_item
            next_item = await self.client.async_request(
                "get",
                f"https://photoslibrary.googleapis.com/v1/mediaItems/{media_items[1]['id']}",
            )
            preload_i = 2
            while True:
                # GET photo to preload. Doing this each time triggers token refresh if needed.
                preload_item = await self.client.async_request(
                    "get",
                    f"https://photoslibrary.googleapis.com/v1/mediaItems/{media_items[preload_i]['id']}",
                )
                msg = {
                    "album": album,
                    "current_item": current_item,
                    "next_item": next_item,
                    "preload_item": preload_item,
                }
                ###################################
                await self._render_widget_html_and_send_to_queue(msg)
                ###################################
                await asyncio.sleep(int(refresh_interval))
                # cycle items
                current_item = next_item
                next_item = preload_item
                # get new preload_i, starting again at 0 if needed
                preload_i = preload_i + 1 if preload_i + 1 < len(media_items) else 0
        except asyncio.CancelledError:
            return

    async def _get_media_items_in_album(self, album):
        # Get all mediaItems in Album
        msg = {"msg": f"Getting photos from album: {album['title']}"}
        await self._render_widget_html_and_send_to_queue(msg)
        logger.info(f"Getting photos from album: {album['title']}")
        body = {"albumId": album["id"], "pageSize": 100, "pageToken": ""}
        media_items = []
        response = await self.client.async_request(
            "post",
            "https://photoslibrary.googleapis.com/v1/mediaItems:search",
            data=body,
        )
        media_items += response["mediaItems"]
        while "nextPageToken" in response:
            logger.info(
                f"Getting photos from album: {album['title']}: Getting next page."
            )
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
            logger.debug(f"mediaItems in calendar: {media_items}")
        return media_items

    async def _start_worker_publishers(self, publisher):
        ######################################################
        # Below depends on the number of publishers
        return

    async def _start_publishing(self, publisher):
        ###############################################
        # Below depends on the publisher details
        return
