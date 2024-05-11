import asyncio
from ds_base import BaseDataSource

import logging

logger = logging.getLogger(__name__)


class DataSource(BaseDataSource):
    type = "counter"
    wait_time = 5
    count = 0

    async def get_data(self):
        self.count = self.count + 1
        return self.count


if __name__ == "__main__":

    async def main():
        ds = DataSource()
        ds_task = asyncio.create_task(ds.start())
        await ds_task

    asyncio.run(main())
