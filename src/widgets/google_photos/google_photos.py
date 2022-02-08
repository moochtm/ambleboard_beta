import aiopubsub
from src.widgets.widget.widget import Widget as BaseWidget
from src.widgets.google_photos.gphotos_sync.authorize import Authorize
import os
from pathlib import Path
import asyncio

import logging

logger = logging.getLogger(__name__)

# GOOGLE CONFIG
AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://www.googleapis.com/oauth2/v4/token"
SCOPE = ["https://www.googleapis.com/auth/photoslibrary"]
PHOTOS_API_URL = "https://photoslibrary.googleapis.com/$discovery" "/rest?version=v1"
# LOCAL FILES CONFIG
SECRETS_FILEPATH = os.path.join(os.path.split(__file__)[0], "client_secret.json")
TOKEN_FILEPATH = os.path.join(os.path.split(__file__)[0], "auth.token")

auth = Authorize(
    scope=SCOPE,
    token_file=Path(TOKEN_FILEPATH).absolute(),
    secrets_file=Path(SECRETS_FILEPATH).absolute(),
)
auth.authorize()

############################################################################
# WIDGET
############################################################################


class Widget(BaseWidget):
    widget_name = "GOOGLE PHOTOS"
    worker_is_running = False
    worker_msg_queue = aiopubsub.Hub()
    worker_prev_update = {}

    async def _start_instance(self):
        if "data-channel" not in self._kwargs:
            msg = {"msg": "data-channel attribute missing."}
            await self._render_widget_html_and_send_to_queue(msg)
            await asyncio.sleep(0)
            return

        if "data-refresh-interval" not in self._kwargs:
            msg = {"msg": "data-refresh-interval attribute missing."}
            await self._render_widget_html_and_send_to_queue(msg)
            await asyncio.sleep(0)
            return

        album_title = self._kwargs["data-channel"]

        # Get all Albums to find ID
        params = {"pageSize": 50, "pageToken": ""}
        result = []
        response = auth.session.get(
            "https://photoslibrary.googleapis.com/v1/albums", params=params
        ).json()
        result += response["albums"]
        while "nextPageToken" in response:
            params = {"pageSize": 50, "pageToken": response["nextPageToken"]}
            response = auth.session.get(
                "https://photoslibrary.googleapis.com/v1/albums", params=params
            ).json()
            result += response["albums"]

        album = [item for item in result if item["title"] == album_title][0]

        # Get all mediaItems in Album
        body = {"albumId": album["id"], "pageSize": 100, "pageToken": ""}
        media_items = []
        response = auth.session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:search", data=body
        ).json()
        media_items += response["mediaItems"]
        while "nextPageToken" in response:
            body = {
                "albumId": album["id"],
                "pageSize": 100,
                "pageToken": response["nextPageToken"],
            }
            response = auth.session.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search", data=body
            ).json()
            media_items += response["mediaItems"]

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
            await asyncio.sleep(int(self._kwargs["data-refresh-interval"]))
            current_i = next_i

    async def _start_worker_publishers(self, publisher):
        ######################################################
        # Below depends on the number of publishers
        return

    async def _start_publishing(self, publisher):
        ###############################################
        # Below depends on the publisher details
        return


############################################################################
# WHEN MODULE RUNS IT PERFORMS A SETUP
############################################################################

if __name__ == "__main__":
    params = {"pageSize": 50, "pageToken": ""}
    result = []
    response = auth.session.get(
        "https://photoslibrary.googleapis.com/v1/albums", params=params
    ).json()
    result += response["albums"]
    while "nextPageToken" in response:
        params = {"pageSize": 50, "pageToken": response["nextPageToken"]}
        response = auth.session.get(
            "https://photoslibrary.googleapis.com/v1/albums", params=params
        ).json()
        result += response["albums"]
    print("Google Photos - Album Titles")
    print("----------------------------")
    for album in result:
        if "title" in album:
            print(album["title"])
