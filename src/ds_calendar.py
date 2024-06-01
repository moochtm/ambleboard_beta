import asyncio
from aiohttp import ClientSession
from ds_base import BaseDataSource
from icalendar import Calendar
import recurring_ical_events
from datetime import datetime, timedelta
import arrow
import logging

logger = logging.getLogger(__name__)


class DataSource(BaseDataSource):
    type = "calendar"
    url = ""
    count = 0
    wait_time = 30

    async def get_data(self):

        client = ClientSession()
        response = await client.get(self.url)
        result = await response.text()

        calendar = Calendar.from_ical(result)
        # Get a list of events, including recurrences
        events = recurring_ical_events.of(calendar).between(
            datetime(2024, 1, 1), datetime(2025, 1, 1)
        )

        data = []
        for event in events:
            summary = event.get("SUMMARY")
            start = arrow.get(str(event.get("DTSTART").dt))
            end = arrow.get(str(event.get("DTEND").dt))
            description = event.get("DESCRIPTION")
            location = event.get("LOCATION")
            all_day = (
                True
                if start.format("YYYY-MM-DD") != end.format("YYYY-MM-DD")
                else False
            )
            active_days = [start.format("YYYY-MM-DD")]
            if all_day:
                current_d = start
                while current_d.format("YYYY-MM-DD") != end.format("YYYY-MM-DD"):
                    current_d = current_d.shift(days=+1)
                    active_days.append(current_d.format("YYYY-MM-DD"))

            data.append(
                {
                    "name": summary,
                    "begin": start.format(),
                    "end": end.format(),
                    "all-day": all_day,
                    "duration_days": (end - start).days,
                    "active_days": active_days,
                    "description": description,
                    "location": location,
                }
            )

        await client.close()
        return data


if __name__ == "__main__":

    async def main():
        calendars = [
            {
                "name": "family",
                "url": "https://outlook.live.com/owa/calendar/0686be5b-9e3d-4bc3-a8f4-f67fb87ce1fa/e1d66387-f97f-49ed-958a-880210d7f82b/cid-3F57A247E69F0DC3/calendar.ics",
            },
            {
                "name": "rondo music",
                "url": "https://app.mymusicstaff.com/CalendarFeed.ashx?User=prt_FLx8JV.D61e902v0gNpGClMy5ppgps5lthuT0NUlxKQb0+8qRw=",
            },
            {
                "name": "cubs",
                "url": "https://www.onlinescoutmanager.co.uk/ext/cal/?f=334576.NzMwOWMyMjFlYmZlNjE3ZDExM2UwYjY1NWU1YmFjZjJhYjE1MGUwMmI1ZjlmYThjZTllMTczMzk1NmI0YjczNWRhMWMyYjU0NTYyN2YyODNmN2E1MDI4YTI3OTA5MzdlNGMyMDViYmFmOTI5MTZmNWNiZmI2MWE4NzY2N2E5NDA%3D.5ShbUIFHCu",
            },
        ]
        tasks = []
        for item in calendars:
            ds = DataSource(name=item["name"])
            ds.url = item["url"]
            tasks.append(asyncio.create_task(ds.start()))
        await asyncio.gather(*tasks)

    asyncio.run(main())
