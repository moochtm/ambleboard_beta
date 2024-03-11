import aiopubsub
from src.widgets.widget.widget import Widget as BaseWidget
import asyncio
import aioftp
import random

import logging

logger = logging.getLogger(__name__)

############################################################################
# WIDGET
############################################################################


class Widget(BaseWidget):
    widget_name = "FTP PHOTOS"
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

            required_args = ["data-host", "data-refresh-interval", "data-user", "data-password", "data-path"]
            missing_args = [arg for arg in required_args if arg not in self._kwargs]
            if missing_args:
                msg = {"msg": f"Missing attributes: {missing_args}"}
                logger.warning(msg)
                await self._render_widget_html_and_send_to_queue(msg)
                await asyncio.sleep(0)
                return

            host = self._kwargs["data-host"]
            user = self._kwargs["data-user"]
            password = self._kwargs["data-password"]
            path = self._kwargs["data-path"]
            refresh_interval = self._kwargs["data-refresh-interval"]

            # Login to FTP server
            client = aioftp.Client()
            await client.connect(host)
            if user != '':
                await client.login(user, password)

            # Goto path
            await client.change_directory(path)

            # Get list of files
            files = await client.list()

            # Shuffle files
            random.shuffle(files)

            #for f in files:
            #    print(f[0])
            #    await client.download(f[0], f[0], write_into=True)

            # GET an initial current_item
            current_item = f"ftp://{user}:{password}@{host}{path}/{files[0][0]}"

            # GET an initial next_item
            next_item = f"ftp://{user}:{password}@{host}{path}/{files[1][0]}"

            preload_i = 2
            while True:
                # GET photo to preload. Doing this each time triggers token refresh if needed.
                preload_item = f"ftp://{user}:{password}@{host}{path}/{files[preload_i][0]}"
                msg = {
                    "album": path,
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
                preload_i = preload_i + 1 if preload_i + 1 < len(files) else 0
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
