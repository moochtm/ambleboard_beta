import asyncio
import aioftp
from ds_base import BaseDataSource
import json


class DataSource(BaseDataSource):
    type = "ftp watcher"
    wait_time = 30
    mqtt_broker_host = "192.168.1.210"
    user = "ambleboard"
    password = "ambleboard"
    path = "/family/ambleboard"

    async def get_data(self):
        # Create client
        client = aioftp.Client()
        # Connect to host
        await client.connect("192.168.1.210")
        # Login
        await client.login(user="ambleboard", password="ambleboard")
        # Go to target folder
        await client.change_directory("/family/ambleboard")
        # Get list of files
        files = await client.list()
        # Create list of files (converting PosixPaths to strings)
        files = [str(f[0]) for f in files]
        return files


if __name__ == "__main__":

    async def main():
        ds = DataSource()
        ds_task = asyncio.create_task(ds.start())
        await ds_task

    asyncio.run(main())
