import asyncio
from aiohttp import ClientSession
from ds_base import BaseDataSource

import logging

logger = logging.getLogger(__name__)


class DataSource(BaseDataSource):
    type = "weather"
    wait_time = 300
    url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/W5%201AZ?unitGroup=us&key=9V95BA9RMBRB3FJQNJRG6KHW9&contentType=json"

    async def get_data(self):
        client = ClientSession()
        response = await client.get(self.url)
        result = await response.json()
        await client.close()
        return result


if __name__ == "__main__":

    async def main():
        ds = DataSource(name="home")
        ds_task = asyncio.create_task(ds.start())
        await ds_task

    asyncio.run(main())
