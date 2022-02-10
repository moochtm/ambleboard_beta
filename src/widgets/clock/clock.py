import asyncio
import aiopubsub
from src.widgets.widget.widget import Widget as BaseWidget
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class Widget(BaseWidget):
    widget_name = "CLOCK"
    worker_is_needed = False
    worker_is_running = False
    worker_msg_queue = None
    worker_prev_update = {}

    async def _start_instance(self):
        while True:
            msg = {"date_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
            ###################################
            await self._render_widget_html_and_send_to_queue(msg)
            ###################################
            await asyncio.sleep(1)


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
