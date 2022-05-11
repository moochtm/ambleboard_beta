import aiopubsub
import asyncio
from src.widgets.widget.widget import Widget as BaseWidget
from src.oauth.microsoft_oauth import MicrosoftAsyncOauthClient
from datetime import datetime, timedelta
from dateutil import parser, relativedelta

import logging

logger = logging.getLogger(__name__)


class Widget(BaseWidget):
    widget_name = "CALENDAR"
    worker_is_needed = False
    worker_is_running = False
    worker_msg_queue = aiopubsub.Hub()
    worker_prev_update = {}

    async def _start_instance(self):
        # try:
        # Check required args
        async def send_please_authenticate(provider):
            msg = {"msg": f"Please authenticate '{provider}' and refresh the webpage."}
            logger.warning(msg)
            await self._render_widget_html_and_send_to_queue(msg)
            await asyncio.sleep(0)
            return

        calendars = self._build_calendars_config()
        required_args = ["data-template", "data-timezone-offset"]
        for c in calendars:
            for k in c:
                required_args.append(c[k])
        missing_args = [arg for arg in required_args if arg not in self._kwargs]
        if missing_args:
            msg = {"msg": f"Missing attributes: {missing_args}"}
            logger.warning(msg)
            await self._render_widget_html_and_send_to_queue(msg)
            await asyncio.sleep(0)
            return

        # Try and create clients for each calendar
        for calendar in calendars:
            provider = self._kwargs[calendar["provider"]]
            user = self._kwargs[calendar["user"]]
            name = self._kwargs[calendar["name"]]
            color = self._kwargs[calendar["color"]]
            if provider == "microsoft":
                calendar["client"] = client = MicrosoftAsyncOauthClient(user_id=user)
                if not client.load_token():
                    await send_please_authenticate(provider)
                    return
                calendar["id"] = await self._get_calendar_id_microsoft(calendar)
                calendar["get_events"] = self._get_calendar_events_microsoft
            else:
                msg = {
                    "msg": f"Unsupported provider: {calendar['provider']}={provider}"
                }
                logger.warning(msg)
                await self._render_widget_html_and_send_to_queue(msg)
                await asyncio.sleep(0)
                return

        # Start the loop
        while True:
            context = {"events": []}
            for cal in calendars:
                context["events"].extend(await cal["get_events"](cal))
            context["events"] = sorted(
                context["events"], key=lambda d: d["start_date_time"]
            )
            for e in context["events"]:
                logger.debug(e)
            # ###################################
            await self._render_widget_html_and_send_to_queue(context)
            # ###################################
            await asyncio.sleep(1000)

        # except asyncio.CancelledError:
        #     for calendar in calendars:
        #         await calendar["client"].close_session()

    ############################################################################
    # MICROSOFT
    ############################################################################

    async def _get_calendar_id_microsoft(self, calendar):
        result = await self.async_request(
            calendar, "get", f"https://graph.microsoft.com/v1.0/me/calendars"
        )
        print(result)
        calendar = [
            cal
            for cal in result["value"]
            if cal["name"] == self._kwargs[calendar["name"]]
        ]
        logger.debug(f"Calendar name={calendar[0]['name']}, id={calendar[0]['id']}")
        return calendar[0]["id"]

    async def async_request(self, calendar, method, url, **kwargs):
        result = await calendar["client"].async_request(method, url, **kwargs)
        return result

    async def _get_calendar_events_microsoft(self, calendar):
        """
        /messages?$filter=ReceivedDateTime ge 2017-04-01 and receivedDateTime lt 2017-05-01
        """
        now = datetime.now()
        from_date = (now - timedelta(days=31)).strftime("%Y-%m-%d")
        to_date = (now + timedelta(days=90)).strftime("%Y-%m-%d")
        results = []
        params = {"startDateTime": from_date, "endDateTime": to_date}
        result = await self.async_request(
            calendar,
            "get",
            f"https://graph.microsoft.com/v1.0/me/calendars/{calendar['id']}/calendarView",
            params=params,
        )
        results.extend(result["value"])
        while "@odata.nextLink" in result:
            result = await self.async_request(
                calendar,
                "get",
                result["@odata.nextLink"],
            )
            results.extend(result["value"])

        # apply timezone offset to start and end times
        timezone_offset = self._kwargs["data-timezone-offset"]
        dt_format = "%Y-%m-%dT%H:%M:%S.%f0"
        for event in results:
            # start datetime
            current_dt = parser.parse(event["start"]["dateTime"])
            current_dt = current_dt + relativedelta.relativedelta(
                minutes=int(timezone_offset)
            )
            event["start"]["dateTime"] = current_dt.strftime(dt_format)
            # end datetime
            current_dt = parser.parse(event["end"]["dateTime"])
            current_dt = current_dt + relativedelta.relativedelta(
                minutes=int(timezone_offset)
            )
            event["end"]["dateTime"] = current_dt.strftime(dt_format)

        return [
            {
                "calendar": self._kwargs[calendar["name"]],
                "color": self._kwargs[calendar["color"]],
                "subject": event["subject"],
                "is_all_day": event["isAllDay"],
                "start_date_time": event["start"]["dateTime"],
                "end_date_time": event["end"]["dateTime"],
                "end_time_zone": event["end"]["timeZone"],
                "location": event["location"]["displayName"],
            }
            for event in results
        ]

        ############################################################################

    def _build_calendars_config(self):
        providers = [arg for arg in self._kwargs if "data-provider" in arg]
        return [
            {
                "provider": provider,
                "user": f"data-user{provider[13:]}",
                "name": f"data-name{provider[13:]}",
                "color": f"data-color{provider[13:]}",
            }
            for provider in providers
        ]

    async def _start_worker_publishers(self, publisher):
        ######################################################
        # Below depends on the number of publishers
        return

    async def _start_publishing(self, publisher):
        ###############################################
        # Below depends on the publisher details
        return


"""
Format Codes	Description	Example
%d	Day of the month as a zero-padded decimal number	01, 02, 03, 04 …, 31
%a	Weekday as abbreviated name	Sun, Mon, …, Sat
%A	Weekday as full name	Sunday, Monday, …, Saturday
%m	Month as a zero-padded decimal number	01, 02, 03, 04 …, 12
%b	Month as abbreviated name	Jan, Feb, …, Dec
%B	Month as full name	January, February, …, December
%y	Year without century as a zero-padded decimal number	00, 01, …, 99
%Y	Year with century as a decimal number	0001, …, 2018, …, 9999
%H	Hour (24-hour clock) as a zero-padded decimal number	01, 02, 03, 04 …, 23
%M	Minute as a zero-padded decimal number	01, 02, 03, 04 …, 59
%S	Second as a zero-padded decimal number	01, 02, 03, 04 …, 59
%f	Microsecond as a decimal number, zero-padded on the left	000000, 000001, …, 999999
%I	Hour (12-hour clock) as a zero-padded decimal number	01, 02, 03, 04 …, 12
%p	Locale’s equivalent of either AM or PM	AM , PM
%j	Day of the year as a zero-padded decimal number	01, 02, 03, 04 …, 366

Directive	Meaning	Example
%a	Abbreviated weekday name.	Sun, Mon, ...
%A	Full weekday name.	Sunday, Monday, ...
%w	Weekday as a decimal number.	0, 1, ..., 6
%d	Day of the month as a zero-padded decimal.	01, 02, ..., 31
%-d	Day of the month as a decimal number.	1, 2, ..., 30
%b	Abbreviated month name.	Jan, Feb, ..., Dec
%B	Full month name.	January, February, ...
%m	Month as a zero-padded decimal number.	01, 02, ..., 12
%-m	Month as a decimal number.	1, 2, ..., 12
%y	Year without century as a zero-padded decimal number.	00, 01, ..., 99
%-y	Year without century as a decimal number.	0, 1, ..., 99
%Y	Year with century as a decimal number.	2013, 2019 etc.
%H	Hour (24-hour clock) as a zero-padded decimal number.	00, 01, ..., 23
%-H	Hour (24-hour clock) as a decimal number.	0, 1, ..., 23
%I	Hour (12-hour clock) as a zero-padded decimal number.	01, 02, ..., 12
%-I	Hour (12-hour clock) as a decimal number.	1, 2, ... 12
%p	Locale’s AM or PM.	AM, PM
%M	Minute as a zero-padded decimal number.	00, 01, ..., 59
%-M	Minute as a decimal number.	0, 1, ..., 59
%S	Second as a zero-padded decimal number.	00, 01, ..., 59
%-S	Second as a decimal number.	0, 1, ..., 59
%f	Microsecond as a decimal number, zero-padded on the left.	000000 - 999999
%z	UTC offset in the form +HHMM or -HHMM.	 
%Z	Time zone name.	 
%j	Day of the year as a zero-padded decimal number.	001, 002, ..., 366
%-j	Day of the year as a decimal number.	1, 2, ..., 366
%U	Week number of the year (Sunday as the first day of the week). All days in a new year preceding the first Sunday are considered to be in week 0.	00, 01, ..., 53
%W	Week number of the year (Monday as the first day of the week). All days in a new year preceding the first Monday are considered to be in week 0.	00, 01, ..., 53
%c	Locale’s appropriate date and time representation.	Mon Sep 30 07:06:05 2013
%x	Locale’s appropriate date representation.	09/30/13
%X	Locale’s appropriate time representation.	07:06:05
%%	A literal '%' character.	%
"""
