import asyncio
from aiohttp import ClientSession
from ds_base import BaseDataSource
from icalendar import Calendar
import recurring_ical_events
from datetime import datetime, timedelta
import arrow
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class DataSource(BaseDataSource):
    type = "google_photos"
    url = ""
    count = 0
    wait_time = 60

    async def get_data(self):

        client = ClientSession()
        response = await client.get(self.url)
        result = await response.text()
        await client.close()

        soup = BeautifulSoup(result, "html.parser")
        imgs = soup.find_all("img", class_="hKgQud")

        data = []
        for img in imgs:
            src = img.get("src")
            src = src.rpartition("=")[0]
            src = src + "=w2160"

            data.append(
                {
                    "url": src,
                }
            )

        return data


if __name__ == "__main__":

    async def main():
        albums = [
            {
                "name": "ambleboard",
                "url": "https://photos.app.goo.gl/uubsW1pvsPXpUtyv9",
            },
        ]
        tasks = []
        for item in albums:
            ds = DataSource(name=item["name"])
            ds.url = item["url"]
            tasks.append(asyncio.create_task(ds.start()))
        await asyncio.gather(*tasks)

    asyncio.run(main())
