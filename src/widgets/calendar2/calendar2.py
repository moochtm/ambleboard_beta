from src.widgets.widget2.widget2 import Widget as BaseWidget
import sys
import pprint
import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)-7s | %(module)-20s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

####################################################################################################
####################################################################################################


class Widget(BaseWidget):
    type = "calendar"

    def update_context(self):

        # print(self.data)
        self.context = {"events": []}
        for cal in [cal for cal in self.data.keys() if "calendar" in cal]:
            events = self.data[cal]["data"]
            if events is not None:
                postfix = cal[-2:]
                color_key = "data_color" + postfix
                print(self._kwargs[color_key])
                color = (
                    self._kwargs[color_key]
                    if color_key in self._kwargs.keys()
                    else "#ffffff"
                )
                print("???????????????????????????????????")
                print(cal)
                print(events)
                for event in events:
                    event["calendar"] = self._kwargs[cal]
                    event["color"] = color
                self.context["events"].extend(events)

        self.context["events"] = sorted(
            self.context["events"], key=lambda x: x["begin"]
        )

        for w in [w for w in self.data.keys() if "weather" in w]:
            self.context["weather"] = self.data[w]["data"]


####################################################################################################
####################################################################################################

if __name__ == "__main__":

    import asyncio

    async def main():
        queue = asyncio.Queue()
        target = "test target"
        protocol = "http"
        host = "localhost"
        port = "8080"
        tasks = []
        for i in range(1):
            kwargs = {
                "data-source-topic": "data sources/calendar/cubs",
                "data-source-topic-1": "data sources/calendar/family",
                "data-source-topic-2": "data sources/calendar/rondo music",
            }
            datasource = Widget(queue, target, protocol, host, port, **kwargs)
            tasks.append(asyncio.create_task(datasource.start()))

        async def queue_worker():
            try:
                while True:
                    payload = await queue.get()
                    logger.info(f"test server received message: {payload}")
                    queue.task_done()
                    await asyncio.sleep(0)
            except asyncio.CancelledError:
                logger.info(f"queue_worker task cancelled")
            except Exception as e:
                print("main exception: ", e)

        tasks.append(asyncio.create_task(queue_worker()))

        # for task in tasks:
        #     asyncio.ensure_future(task)

        # for i in range(5):
        #     print(i)
        #     await asyncio.sleep(1)
        #
        # for task in tasks:
        #     print("cancelling task")
        #     task.cancel()
        #     await task

        while True:
            await asyncio.sleep(0)

    asyncio.run(main())


"""
{'data_source_topic': {'data': [{'all-day': False,
                                 'begin': '2023-06-23 17:30:00+01:00',
                                 'description': None,
                                 'end': '2023-06-25 15:00:00+01:00',
                                 'location': 'Longridge Activity Centre, Kings '
                                             'Langley, Herts',
                                 'name': '1EN Cubs - Summer Camp 2023 - '
                                         'Phasels Wood Activity Centre'},
                                {'all-day': False,
                                 'begin': '2023-09-24 08:15:00+01:00',
                                 'description': None,
                                 'end': '2023-09-24 12:30:00+01:00',
                                 'location': 'Walpole Park, Ealing',
                                 'name': '1EN Cubs - Ealing Half Marathon '
                                         'Volunteering'},
                                {'all-day': False,
                                 'begin': '2023-11-12 10:15:00+00:00',
                                 'description': None,
                                 'end': '2023-11-12 11:30:00+00:00',
                                 'location': 'Ealing',
                                 'name': '1EN Scouts - District Remembrance '
                                         'Parade 2023'},
                                {'all-day': False,
                                 'begin': '2023-12-10 10:00:00+00:00',
                                 'description': None,
                                 'end': '2023-12-10 14:15:00+00:00',
                                 'location': 'Ealing',
                                 'name': '1EN Cubs - Day Hike'},
                                {'all-day': False,
                                 'begin': '2024-01-28 10:00:00+00:00',
                                 'description': None,
                                 'end': '2024-01-28 16:00:00+00:00',
                                 'location': 'Scout HQ',
                                 'name': '1EN Cubs - Sixers/Seconders '
                                         'Leadership event 2024'},
                                {'all-day': False,
                                 'begin': '2024-03-23 09:00:00+00:00',
                                 'description': None,
                                 'end': '2024-03-24 14:00:00+00:00',
                                 'location': 'Walter Davies Campsite',
                                 'name': '1EN Group Camp 24 - Cubs'},
                                {'all-day': False,
                                 'begin': '2024-04-21 13:40:00+01:00',
                                 'description': None,
                                 'end': '2024-04-21 16:00:00+01:00',
                                 'location': 'Elthorne Park, W7',
                                 'name': 'St Ben Cubs - St George’s Day Parade '
                                         '2024'},
                                {'all-day': False,
                                 'begin': '2024-06-14 17:30:00+01:00',
                                 'description': None,
                                 'end': '2024-06-16 15:00:00+01:00',
                                 'location': 'PACCAR Scout Camp, Chalfont St '
                                             'Peter',
                                 'name': '1EN Cubs - Joint Summer Camp 2024'},
                                {'all-day': False,
                                 'begin': '2024-07-28 13:00:00+01:00',
                                 'description': None,
                                 'end': '2024-07-30 20:00:00+01:00',
                                 'location': 'Walter Davies Campsite Stoke '
                                             'Poges SL2 4AL',
                                 'name': 'District Cubs Camp - Camporee 2024'}],
                       'data_source_id': 'data_source_topic',
                       'timestamp': '2024-05-17 18:12:22+00:00'},
 'data_source_topic_1': {'data': [{'all-day': False,
                                   'begin': '2024-02-19 17:45:00+00:00',
                                   'description': None,
                                   'end': '2024-02-19 18:45:00+00:00',
                                   'location': None,
                                   'name': 'Lisa swimming 6pm'},
                                  {'all-day': False,
                                   'begin': '2024-02-20 17:30:00+00:00',
                                   'description': None,
                                   'end': '2024-02-20 18:30:00+00:00',
                                   'location': '',
                                   'name': 'Lisa & Holly Tutors'},
                                  {'all-day': False,
                                   'begin': '2024-02-22 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-02-22 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa netball (8.10am)'},
                                  {'all-day': False,
                                   'begin': '2024-02-23 08:15:00+00:00',
                                   'description': '\n',
                                   'end': '2024-02-23 08:45:00+00:00',
                                   'location': '',
                                   'name': 'Lisa at Choir'},
                                  {'all-day': False,
                                   'begin': '2024-02-23 19:00:00+00:00',
                                   'description': 'Phase 10\n'
                                                  'Saboteur\n'
                                                  'Caucassone',
                                   'end': '2024-02-23 20:00:00+00:00',
                                   'location': '',
                                   'name': 'Friday Games Night'},
                                  {'all-day': False,
                                   'begin': '2024-02-24 11:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-02-24 12:00:00+00:00',
                                   'location': '',
                                   'name': 'Go to Pitshanger Lane pharmacy to '
                                           'ask about blood tests'},
                                  {'all-day': False,
                                   'begin': '2024-02-27 19:00:00+00:00',
                                   'description': '\n'
                                                  '\n'
                                                  '\n'
                                                  '\n'
                                                  'From: Lior Duby '
                                                  '<myscout@onlinescoutmanager.co.uk>\n'
                                                  'Date: Friday, 23 February '
                                                  '2024 at 17:40\n'
                                                  'To: helena.barr@live.co.uk '
                                                  '<helena.barr@live.co.uk>, '
                                                  'matt.barr@live.co.uk '
                                                  '<matt.barr@live.co.uk>\n'
                                                  'Subject: St Ben Cubs – T2 '
                                                  'Meeting 06 – 27-Feb-24 - '
                                                  'Virtual Meeting\n'
                                                  '\n'
                                                  'Hi all,\n'
                                                  '\n'
                                                  'Hi all, hope you all had a '
                                                  'good half term.\n'
                                                  '\n'
                                                  'This Sunday it’s the '
                                                  'district cross country '
                                                  'event. If you haven’t yet, '
                                                  'do sign up via this '
                                                  'link<https://docs.google.com/forms/d/e/1FAIpQLSc8Zj-jShwqVDP5C85QpI5D21MMkXLFC-t_yOVuyGEOWQfmdw/viewform?usp=sf_link>, '
                                                  'or see OSM for more '
                                                  'details.\n'
                                                  '\n'
                                                  'Our next meeting will be a '
                                                  'virtual one, we will meet '
                                                  'using Zoom. The Cubs will '
                                                  'have a chance to meet a '
                                                  'real vet and learn a little '
                                                  'about animal care. If you '
                                                  'have a pet at home, you may '
                                                  'well wish to have them '
                                                  'close by.\n'
                                                  '\n'
                                                  'Zoom works on a computer, '
                                                  'tablet or phone. As we have '
                                                  'not held a zoom meeting for '
                                                  'a little while you may wish '
                                                  'to make sure that you have '
                                                  'zoom is installed and '
                                                  'updated on a suitable '
                                                  'device. The joining link '
                                                  'and passcode is below.\n'
                                                  '\n'
                                                  'Guidance on using Zoom & '
                                                  'Virtual meetings\n'
                                                  'We want this to be a safe '
                                                  'and fun, so a little '
                                                  'guidance for everyone:\n'
                                                  '-Please join in on time - '
                                                  'latecomers may not be '
                                                  'admitted\n'
                                                  '-Cubs must use their own '
                                                  'name (no alias) in the '
                                                  'meeting\n'
                                                  '-No one is to join from '
                                                  'their bedroom. Public rooms '
                                                  'only - living room, '
                                                  'kitchen, dining room, etc\n'
                                                  '-Ensure you are in the same '
                                                  'room as your child during '
                                                  'our virtual meeting. This '
                                                  'is both from a safety and '
                                                  'help with technology '
                                                  'perspective\n'
                                                  '-Ensure any other people in '
                                                  'the room are dressed '
                                                  'appropriately and behave '
                                                  'appropriately as they will '
                                                  'be visible to everyone on '
                                                  'the call\n'
                                                  '-Cubs need to be in their '
                                                  'Uniform\n'
                                                  '-We expect the same '
                                                  'standard of behaviour our '
                                                  'Cubs online as we do in our '
                                                  'face to face meetings from\n'
                                                  '\n'
                                                  'Meeting 06 – Virtual '
                                                  'Meeting - Animal Carer\n'
                                                  'Date – Tuesday 27-Feb-2024\n'
                                                  'Time – 19:00\n'
                                                  '\n'
                                                  'Join Zoom Meeting\n'
                                                  'https://zoom.us/j/96567691747\n'
                                                  '\n'
                                                  'Meeting ID: 965 6769 1747\n'
                                                  'Passcode: animalcare\n'
                                                  '\n'
                                                  'Meet at – Online\n'
                                                  'Equipment – None\n'
                                                  '\n'
                                                  'Parent helpers – None\n'
                                                  '\n'
                                                  '2024 term key dates\n'
                                                  '- 25/02/2025 - District '
                                                  'cross country race\n'
                                                  '- 23/03/2024 to 24/03/2024 '
                                                  '- Spring Camp at Stoke '
                                                  'Poges\n'
                                                  '- 14/06/2024 to 16/6/2024 - '
                                                  'Summer camp\n'
                                                  '- 28/07/2024 to 30/07/2024 '
                                                  '- Camporee District Cubs '
                                                  'camp\n'
                                                  '\n'
                                                  'Regards,\n'
                                                  '\n'
                                                  'Lior (AKA Akela)\n'
                                                  '[https://84331c0r.r.eu-west-1.awstrack.me/I0/0102018dd70e4d3b-eeef1a7b-a73e-4ed1-8206-71a7f48b2403-000000/fS0BUzkt-48LG1t0QzEDXEQhAHA=362]\n',
                                   'end': '2024-02-27 20:00:00+00:00',
                                   'location': '',
                                   'name': 'St Ben Cubs – Virtual Meeting with '
                                           'VET'},
                                  {'all-day': False,
                                   'begin': '2024-02-27 19:00:00+00:00',
                                   'description': None,
                                   'end': '2024-02-27 20:30:00+00:00',
                                   'location': None,
                                   'name': 'Lisa cubs'},
                                  {'all-day': True,
                                   'begin': '2024-02-28 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-02-29 00:00:00+00:00',
                                   'location': '',
                                   'name': '20'},
                                  {'all-day': True,
                                   'begin': '2024-02-29 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-01 00:00:00+00:00',
                                   'location': '',
                                   'name': '19'},
                                  {'all-day': True,
                                   'begin': '2024-03-01 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-02 00:00:00+00:00',
                                   'location': '',
                                   'name': '18'},
                                  {'all-day': True,
                                   'begin': '2024-03-02 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-03 00:00:00+00:00',
                                   'location': '',
                                   'name': '17'},
                                  {'all-day': False,
                                   'begin': '2024-03-02 10:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-02 14:00:00+00:00',
                                   'location': None,
                                   'name': 'To Potten end for Lisa birthday '},
                                  {'all-day': True,
                                   'begin': '2024-03-03 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-04 00:00:00+00:00',
                                   'location': '',
                                   'name': '16'},
                                  {'all-day': True,
                                   'begin': '2024-03-04 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-05 00:00:00+00:00',
                                   'location': '',
                                   'name': '15'},
                                  {'all-day': False,
                                   'begin': '2024-03-04 19:45:00+00:00',
                                   'description': None,
                                   'end': '2024-03-04 21:15:00+00:00',
                                   'location': None,
                                   'name': 'Helena pilates'},
                                  {'all-day': True,
                                   'begin': '2024-03-05 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-06 00:00:00+00:00',
                                   'location': '',
                                   'name': '14'},
                                  {'all-day': True,
                                   'begin': '2024-03-06 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-07 00:00:00+00:00',
                                   'location': '',
                                   'name': '13'},
                                  {'all-day': False,
                                   'begin': '2024-03-06 08:30:00+00:00',
                                   'description': '\n'
                                                  '________________________________\n'
                                                  'From: Montpelier Primary '
                                                  'School '
                                                  '<SC3072182a@schoolcomms.com>\n'
                                                  'Sent: Monday, December 18, '
                                                  '2023 3:23:38 PM\n'
                                                  'To: Matt Barr '
                                                  '<matt.barr@live.co.uk>\n'
                                                  'Subject: Eco Committee '
                                                  'Spring dates\n'
                                                  '\n'
                                                  '\n'
                                                  '[https://www.schoolcomms.com/messaging/templates/316994/LOGO.JPG]\n'
                                                  '\n'
                                                  'MONTPELIER PRIMARY SCHOOL\n'
                                                  '\n'
                                                  'PLEASE DO NOT CLICK ‘REPLY’ '
                                                  'TO THIS EMAIL.\n'
                                                  'Replies must go to '
                                                  'admin@montpelier.ealing.sch.uk\n'
                                                  '\n'
                                                  '\n'
                                                  'Monday 18th December 2023\n'
                                                  '\n'
                                                  '\n'
                                                  'Dear parent/carer of Lisa '
                                                  'Barr\n'
                                                  '\n'
                                                  'I am pleased to be '
                                                  'continuing the '
                                                  'Eco-Committee meetings in '
                                                  'the Spring term and I am '
                                                  'writing to share the dates '
                                                  'of our meetings with you. '
                                                  'The topics we have decided '
                                                  'to focus on this year are: '
                                                  'Bio-diversity, Litter and '
                                                  'Water. Please encourage '
                                                  'your child to regularly '
                                                  'access the Eco-Committee '
                                                  'blog on Purple Mash where '
                                                  'they can read information '
                                                  'from our meetings, share '
                                                  'their ideas and be '
                                                  'inspired.\n'
                                                  '\n'
                                                  'Please ensure your child '
                                                  'arrives outside the\u202f'
                                                  'Main Office at\u202f'
                                                  '8.25am\u202fon the correct '
                                                  'Wednesdays where I will '
                                                  'meet the children and '
                                                  'escort them into the '
                                                  'school. Please note that if '
                                                  'your child is late, they '
                                                  'will not be admitted and '
                                                  'will have to enter the '
                                                  'school building at 8.40am '
                                                  'when the gates are open for '
                                                  'all KS2 pupils.\u202f\n'
                                                  '\n'
                                                  'Spring 1: Bio-diversity and '
                                                  'Litter\n'
                                                  '\n'
                                                  'If you have a litter '
                                                  'picker, it would be very '
                                                  'helpful if the Eco '
                                                  'Committee could use it '
                                                  'during Week 4 and 5 when we '
                                                  'will be collecting litter '
                                                  'around the school grounds '
                                                  'during our meeting.\n'
                                                  '\n'
                                                  'Date\n'
                                                  'Year group\n'
                                                  'Week 1 – 10.1.24\n'
                                                  'NO MEETING\n'
                                                  'Week 2 – 17.1.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 3 – 24.1.24\n'
                                                  '4, 5, 6\n'
                                                  'Week 4 – 31.1.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 5 – 07.2.24\u202f\n'
                                                  '4, 5, 6\n'
                                                  'Half Term\n'
                                                  'NO MEETING\n'
                                                  '\n'
                                                  'Spring 2: Biodiversity and '
                                                  'Water\n'
                                                  '\n'
                                                  'Date\n'
                                                  'Year group\n'
                                                  'Week 1 – 21.2.24\n'
                                                  'NO MEETING\n'
                                                  'Week 2 – 28.2.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 3 – 06.3.24\n'
                                                  '4, 5, 6\n'
                                                  'Week 4 – 13.3.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 5 –\u202f20.3.24\n'
                                                  '4, 5, 6\n'
                                                  'Week 6 –\u202f27.3.24\n'
                                                  'NO MEETING\u202f\n'
                                                  '\n'
                                                  'I’ve loved working with all '
                                                  'Eco Committee members so '
                                                  'far, and I hope you and '
                                                  'your family have a '
                                                  'wonderful Christmas '
                                                  'holiday. See you in the New '
                                                  'Year!\n'
                                                  '\n'
                                                  'Kind regards,\n'
                                                  '\n'
                                                  'Miss Mepham\n'
                                                  'Year 3 Teacher\n'
                                                  'Eco Committee Lead\n'
                                                  '\n',
                                   'end': '2024-03-06 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa: Eco Committee 8.25am'},
                                  {'all-day': False,
                                   'begin': '2024-03-06 13:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-06 15:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa netball tournament '},
                                  {'all-day': False,
                                   'begin': '2024-03-06 18:30:00+00:00',
                                   'description': None,
                                   'end': '2024-03-06 20:30:00+00:00',
                                   'location': None,
                                   'name': 'Amber training class 7pm'},
                                  {'all-day': True,
                                   'begin': '2024-03-07 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-08 00:00:00+00:00',
                                   'location': '',
                                   'name': '12'},
                                  {'all-day': True,
                                   'begin': '2024-03-07 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-03-08 00:00:00+00:00',
                                   'location': '',
                                   'name': 'International Book Day'},
                                  {'all-day': True,
                                   'begin': '2024-03-08 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-09 00:00:00+00:00',
                                   'location': '',
                                   'name': '11'},
                                  {'all-day': False,
                                   'begin': '2024-03-08 16:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-08 17:00:00+00:00',
                                   'location': None,
                                   'name': 'CANCELLED - Girls dentist 4.30 '},
                                  {'all-day': True,
                                   'begin': '2024-03-09 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-10 00:00:00+00:00',
                                   'location': '',
                                   'name': '10'},
                                  {'all-day': False,
                                   'begin': '2024-03-09 11:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-09 16:00:00+00:00',
                                   'location': None,
                                   'name': 'Kristina 50th birthday '
                                           'celebration '},
                                  {'all-day': True,
                                   'begin': '2024-03-10 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-11 00:00:00+00:00',
                                   'location': '',
                                   'name': '9'},
                                  {'all-day': True,
                                   'begin': '2024-03-11 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-12 00:00:00+00:00',
                                   'location': '',
                                   'name': '8'},
                                  {'all-day': True,
                                   'begin': '2024-03-12 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-13 00:00:00+00:00',
                                   'location': '',
                                   'name': '7'},
                                  {'all-day': True,
                                   'begin': '2024-03-13 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-14 00:00:00+00:00',
                                   'location': '',
                                   'name': '6'},
                                  {'all-day': True,
                                   'begin': '2024-03-13 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-03-14 00:00:00+00:00',
                                   'location': '',
                                   'name': 'Iva'},
                                  {'all-day': False,
                                   'begin': '2024-03-13 16:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-13 18:00:00+00:00',
                                   'location': None,
                                   'name': 'Emily dance show 4.30'},
                                  {'all-day': True,
                                   'begin': '2024-03-14 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-15 00:00:00+00:00',
                                   'location': '',
                                   'name': '5'},
                                  {'all-day': False,
                                   'begin': '2024-03-14 18:30:00+00:00',
                                   'description': '\n'
                                                  '\n'
                                                  '\n'
                                                  '\n'
                                                  'From: GHiggins '
                                                  '<schoolbase@sapriory.com>\n'
                                                  'Date: Wednesday, 6 March '
                                                  '2024 at 16:03\n'
                                                  'To: matt.barr@live.co.uk '
                                                  '<matt.barr@live.co.uk>\n'
                                                  'Subject: Spring Concert\n'
                                                  '\n'
                                                  'Dear Parents,\n'
                                                  '\n'
                                                  'The Spring Concert will '
                                                  'take place on Thursday 14th '
                                                  'March. Please see details '
                                                  'below.\n'
                                                  '\n'
                                                  '6:30pm - student performers '
                                                  'to arrive back at school in '
                                                  'full uniform and with their '
                                                  'instrument if necessary\n'
                                                  '              - '
                                                  'refreshments in the hall '
                                                  'for parents/guests\n'
                                                  '\n'
                                                  '7pm - the Spring Concert '
                                                  'begins in the Chapel\n'
                                                  '\n'
                                                  'c.8.15 - the concert ends '
                                                  'and students will be '
                                                  'dismissed\n'
                                                  '\n'
                                                  'Please note that students '
                                                  'need to go home after '
                                                  'school as normal as there '
                                                  'will not be any staff to '
                                                  'supervise.\n'
                                                  '\n'
                                                  'The groups performing are:\n'
                                                  '\n'
                                                  '  *   The senior string '
                                                  'orchestra\n'
                                                  '  *   The junior string '
                                                  'orchestra\n'
                                                  '  *   The senior flute '
                                                  'ensemble\n'
                                                  '  *   The chamber choir\n'
                                                  '  *   The prep choir\n'
                                                  '  *   Year 5 students\n'
                                                  '  *   Year 6 students\n'
                                                  '  *   The prep orchestra\n'
                                                  '  *   The senior orchestra\n'
                                                  '  *   The jazz band\n'
                                                  '\n'
                                                  'We look forward to seeing '
                                                  'many of you there!\n'
                                                  '\n'
                                                  'Best wishes,\n'
                                                  '\n'
                                                  'Dr G Higgins\n'
                                                  'Director of Music\n'
                                                  'PABIADYAVwAwADAAOABTAFQARwBNAFUANAAuAEQAQwAyAFYAUQBJAEYAOABIADcARABCADIAQABzAGEAcAByAGkAbwByAHkALgBjAG8AbQA+AA==\n'
                                                  '\n'
                                                  '‘Our Girls Will Change the '
                                                  'World’\n'
                                                  '\n'
                                                  '[https://www.sapriory.com/wp-content/uploads/2023/03/twitter.png]<https://twitter.com/staugustinesp>[https://www.sapriory.com/wp-content/uploads/2023/03/facebook.png]<https://www.facebook.com/St-Augustines-Priory-796102473820452/timeline/>[https://www.sapriory.com/wp-content/uploads/2023/03/instagram.png]<https://instagram.com/st.augustines.priory/?hl=en>[https://www.sapriory.com/wp-content/uploads/2023/03/linkedin.png]<https://uk.linkedin.com/company/st-augustine-s-priory>[https://www.sapriory.com/wp-content/uploads/2023/03/spotify.png]<https://open.spotify.com/show/6BuL1HI0bQ2RKYsRt9ytsk>\n'
                                                  '\n'
                                                  '\n'
                                                  'St Augustine’s Priory is a '
                                                  'Registered Charity, Number '
                                                  '1097781\n'
                                                  'View '
                                                  'Disclaimer<https://www.sapriory.com/disclaimer/>\n',
                                   'end': '2024-03-14 20:15:00+00:00',
                                   'location': '',
                                   'name': "St Augustine's Spring Concert"},
                                  {'all-day': True,
                                   'begin': '2024-03-15 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-16 00:00:00+00:00',
                                   'location': '',
                                   'name': '4'},
                                  {'all-day': True,
                                   'begin': '2024-03-16 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-17 00:00:00+00:00',
                                   'location': '',
                                   'name': '3'},
                                  {'all-day': True,
                                   'begin': '2024-03-17 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-18 00:00:00+00:00',
                                   'location': '',
                                   'name': '2'},
                                  {'all-day': True,
                                   'begin': '2024-03-18 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-19 00:00:00+00:00',
                                   'location': '',
                                   'name': '1'},
                                  {'all-day': False,
                                   'begin': '2024-03-20 08:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-03-20 11:00:00+00:00',
                                   'location': '',
                                   'name': 'Jason - hedges'},
                                  {'all-day': False,
                                   'begin': '2024-03-20 08:30:00+00:00',
                                   'description': '\n'
                                                  '________________________________\n'
                                                  'From: Montpelier Primary '
                                                  'School '
                                                  '<SC3072182a@schoolcomms.com>\n'
                                                  'Sent: Monday, December 18, '
                                                  '2023 3:23:38 PM\n'
                                                  'To: Matt Barr '
                                                  '<matt.barr@live.co.uk>\n'
                                                  'Subject: Eco Committee '
                                                  'Spring dates\n'
                                                  '\n'
                                                  '\n'
                                                  '[https://www.schoolcomms.com/messaging/templates/316994/LOGO.JPG]\n'
                                                  '\n'
                                                  'MONTPELIER PRIMARY SCHOOL\n'
                                                  '\n'
                                                  'PLEASE DO NOT CLICK ‘REPLY’ '
                                                  'TO THIS EMAIL.\n'
                                                  'Replies must go to '
                                                  'admin@montpelier.ealing.sch.uk\n'
                                                  '\n'
                                                  '\n'
                                                  'Monday 18th December 2023\n'
                                                  '\n'
                                                  '\n'
                                                  'Dear parent/carer of Lisa '
                                                  'Barr\n'
                                                  '\n'
                                                  'I am pleased to be '
                                                  'continuing the '
                                                  'Eco-Committee meetings in '
                                                  'the Spring term and I am '
                                                  'writing to share the dates '
                                                  'of our meetings with you. '
                                                  'The topics we have decided '
                                                  'to focus on this year are: '
                                                  'Bio-diversity, Litter and '
                                                  'Water. Please encourage '
                                                  'your child to regularly '
                                                  'access the Eco-Committee '
                                                  'blog on Purple Mash where '
                                                  'they can read information '
                                                  'from our meetings, share '
                                                  'their ideas and be '
                                                  'inspired.\n'
                                                  '\n'
                                                  'Please ensure your child '
                                                  'arrives outside the\u202f'
                                                  'Main Office at\u202f'
                                                  '8.25am\u202fon the correct '
                                                  'Wednesdays where I will '
                                                  'meet the children and '
                                                  'escort them into the '
                                                  'school. Please note that if '
                                                  'your child is late, they '
                                                  'will not be admitted and '
                                                  'will have to enter the '
                                                  'school building at 8.40am '
                                                  'when the gates are open for '
                                                  'all KS2 pupils.\u202f\n'
                                                  '\n'
                                                  'Spring 1: Bio-diversity and '
                                                  'Litter\n'
                                                  '\n'
                                                  'If you have a litter '
                                                  'picker, it would be very '
                                                  'helpful if the Eco '
                                                  'Committee could use it '
                                                  'during Week 4 and 5 when we '
                                                  'will be collecting litter '
                                                  'around the school grounds '
                                                  'during our meeting.\n'
                                                  '\n'
                                                  'Date\n'
                                                  'Year group\n'
                                                  'Week 1 – 10.1.24\n'
                                                  'NO MEETING\n'
                                                  'Week 2 – 17.1.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 3 – 24.1.24\n'
                                                  '4, 5, 6\n'
                                                  'Week 4 – 31.1.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 5 – 07.2.24\u202f\n'
                                                  '4, 5, 6\n'
                                                  'Half Term\n'
                                                  'NO MEETING\n'
                                                  '\n'
                                                  'Spring 2: Biodiversity and '
                                                  'Water\n'
                                                  '\n'
                                                  'Date\n'
                                                  'Year group\n'
                                                  'Week 1 – 21.2.24\n'
                                                  'NO MEETING\n'
                                                  'Week 2 – 28.2.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 3 – 06.3.24\n'
                                                  '4, 5, 6\n'
                                                  'Week 4 – 13.3.24\n'
                                                  '1, 2, 3\n'
                                                  'Week 5 –\u202f20.3.24\n'
                                                  '4, 5, 6\n'
                                                  'Week 6 –\u202f27.3.24\n'
                                                  'NO MEETING\u202f\n'
                                                  '\n'
                                                  'I’ve loved working with all '
                                                  'Eco Committee members so '
                                                  'far, and I hope you and '
                                                  'your family have a '
                                                  'wonderful Christmas '
                                                  'holiday. See you in the New '
                                                  'Year!\n'
                                                  '\n'
                                                  'Kind regards,\n'
                                                  '\n'
                                                  'Miss Mepham\n'
                                                  'Year 3 Teacher\n'
                                                  'Eco Committee Lead\n'
                                                  '\n',
                                   'end': '2024-03-20 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa: Eco Committee 8.25am'},
                                  {'all-day': False,
                                   'begin': '2024-03-22 10:45:00+00:00',
                                   'description': None,
                                   'end': '2024-03-22 12:00:00+00:00',
                                   'location': None,
                                   'name': 'Helena coffee with Katie at 11'},
                                  {'all-day': False,
                                   'begin': '2024-03-22 12:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-22 18:00:00+00:00',
                                   'location': None,
                                   'name': '10 years living in Winscombe Cres'},
                                  {'all-day': False,
                                   'begin': '2024-03-23 10:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-03-24 14:00:00+00:00',
                                   'location': '',
                                   'name': 'Lisa Cubs Camp - Stoke Poges'},
                                  {'all-day': False,
                                   'begin': '2024-03-24 16:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-24 18:00:00+00:00',
                                   'location': None,
                                   'name': 'Register for May Day?'},
                                  {'all-day': False,
                                   'begin': '2024-03-25 19:45:00+00:00',
                                   'description': None,
                                   'end': '2024-03-25 21:15:00+00:00',
                                   'location': None,
                                   'name': 'Helena pilates'},
                                  {'all-day': True,
                                   'begin': '2024-03-27 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-28 00:00:00+00:00',
                                   'location': '',
                                   'name': 'Car dent fixing'},
                                  {'all-day': False,
                                   'begin': '2024-03-28 12:00:00+00:00',
                                   'description': None,
                                   'end': '2024-03-28 13:00:00+00:00',
                                   'location': None,
                                   'name': 'St Augustine term ends 12'},
                                  {'all-day': False,
                                   'begin': '2024-03-28 13:40:00+00:00',
                                   'description': None,
                                   'end': '2024-03-28 14:40:00+00:00',
                                   'location': None,
                                   'name': 'Montpelier term ends 1.40'},
                                  {'all-day': False,
                                   'begin': '2024-03-28 18:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-03-28 20:00:00+00:00',
                                   'location': '',
                                   'name': 'Lambing'},
                                  {'all-day': False,
                                   'begin': '2024-03-30 08:30:00+00:00',
                                   'description': None,
                                   'end': '2024-03-30 12:30:00+00:00',
                                   'location': '',
                                   'name': 'Kew 10k'},
                                  {'all-day': True,
                                   'begin': '2024-03-31 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-04-01 00:00:00+00:00',
                                   'location': '',
                                   'name': 'Easter Sunday'},
                                  {'all-day': False,
                                   'begin': '2024-04-02 08:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-02 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Half term'},
                                  {'all-day': False,
                                   'begin': '2024-04-05 10:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-05 11:15:00+00:00',
                                   'location': None,
                                   'name': 'Girls dentist 10.30 and 10.45'},
                                  {'all-day': False,
                                   'begin': '2024-04-05 10:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-05 11:30:00+00:00',
                                   'location': '',
                                   'name': 'Girls at dentist'},
                                  {'all-day': False,
                                   'begin': '2024-04-05 13:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-05 16:30:00+00:00',
                                   'location': None,
                                   'name': 'Amber groom at 2pm'},
                                  {'all-day': False,
                                   'begin': '2024-04-05 17:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-04-05 22:00:00+00:00',
                                   'location': '',
                                   'name': 'Wembley - ENG vs SWE'},
                                  {'all-day': False,
                                   'begin': '2024-04-14 16:15:00+00:00',
                                   'description': None,
                                   'end': '2024-04-14 17:15:00+00:00',
                                   'location': None,
                                   'name': 'Lisa MayDay rehearsal 4.45'},
                                  {'all-day': False,
                                   'begin': '2024-04-15 18:10:00+00:00',
                                   'description': None,
                                   'end': '2024-04-15 19:15:00+00:00',
                                   'location': None,
                                   'name': 'Lisa swimming 6.30pm'},
                                  {'all-day': False,
                                   'begin': '2024-04-16 09:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-16 09:45:00+00:00',
                                   'location': None,
                                   'name': 'Parents briefing on Isle of Wight '
                                           'trip'},
                                  {'all-day': False,
                                   'begin': '2024-04-16 12:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-16 15:15:00+00:00',
                                   'location': None,
                                   'name': 'Lisa choir concert rehearsal '},
                                  {'all-day': False,
                                   'begin': '2024-04-19 16:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-19 20:00:00+00:00',
                                   'location': None,
                                   'name': 'Emily friends after school '},
                                  {'all-day': False,
                                   'begin': '2024-04-19 19:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-19 21:00:00+00:00',
                                   'location': '',
                                   'name': 'Brentham Club food market'},
                                  {'all-day': False,
                                   'begin': '2024-04-21 13:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-21 16:00:00+00:00',
                                   'location': None,
                                   'name': 'Cubs St George day parade '},
                                  {'all-day': False,
                                   'begin': '2024-04-25 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-25 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa netball 8am'},
                                  {'all-day': False,
                                   'begin': '2024-04-25 14:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-04-25 15:00:00+00:00',
                                   'location': '',
                                   'name': 'Lisa swimming'},
                                  {'all-day': False,
                                   'begin': '2024-04-25 15:15:00+00:00',
                                   'description': None,
                                   'end': '2024-04-25 16:25:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Monstercats'},
                                  {'all-day': False,
                                   'begin': '2024-04-27 09:00:00+00:00',
                                   'description': None,
                                   'end': '2024-04-27 12:00:00+00:00',
                                   'location': None,
                                   'name': 'StAugustine open day'},
                                  {'all-day': False,
                                   'begin': '2024-04-27 13:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-27 17:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa to Sienna Birthday '},
                                  {'all-day': False,
                                   'begin': '2024-04-27 15:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-27 19:30:00+00:00',
                                   'location': None,
                                   'name': 'Emily to Zoe party'},
                                  {'all-day': False,
                                   'begin': '2024-04-28 16:30:00+00:00',
                                   'description': None,
                                   'end': '2024-04-28 16:45:00+00:00',
                                   'location': None,
                                   'name': 'Lisa to May Queen election'},
                                  {'all-day': False,
                                   'begin': '2024-04-30 07:30:00+00:00',
                                   'description': None,
                                   'end': '2024-05-03 13:30:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Isle of Wight trip'},
                                  {'all-day': True,
                                   'begin': '2024-05-01 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-05-02 00:00:00+00:00',
                                   'location': '',
                                   'name': 'Lisa - Eco-Committee (8:25am)'},
                                  {'all-day': False,
                                   'begin': '2024-05-01 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-01 08:30:00+00:00',
                                   'location': None,
                                   'name': 'Take Amber to daycare (returned by '
                                           'ACC)'},
                                  {'all-day': False,
                                   'begin': '2024-05-01 11:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-05-01 14:00:00+00:00',
                                   'location': '',
                                   'name': 'Boiler service'},
                                  {'all-day': False,
                                   'begin': '2024-05-02 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-02 08:30:00+00:00',
                                   'location': None,
                                   'name': 'Take Amber to daycare (returned by '
                                           'ACC)'},
                                  {'all-day': False,
                                   'begin': '2024-05-06 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-06 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Bank holiday '},
                                  {'all-day': False,
                                   'begin': '2024-05-07 12:30:00+00:00',
                                   'description': None,
                                   'end': '2024-05-07 15:45:00+00:00',
                                   'location': None,
                                   'name': 'Lisa choir concert rehearsal '},
                                  {'all-day': False,
                                   'begin': '2024-05-09 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-09 08:45:00+00:00',
                                   'location': None,
                                   'name': 'Lisa netball 8am'},
                                  {'all-day': True,
                                   'begin': '2024-05-10 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-05-11 00:00:00+00:00',
                                   'location': '',
                                   'name': 'Boiler Boys'},
                                  {'all-day': False,
                                   'begin': '2024-05-11 09:30:00+00:00',
                                   'description': None,
                                   'end': '2024-05-11 10:30:00+00:00',
                                   'location': '',
                                   'name': 'Whistlers at home'},
                                  {'all-day': False,
                                   'begin': '2024-05-12 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-12 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Barbro 80th Birthday '},
                                  {'all-day': False,
                                   'begin': '2024-05-12 16:15:00+00:00',
                                   'description': None,
                                   'end': '2024-05-12 17:15:00+00:00',
                                   'location': None,
                                   'name': 'Lisa May Day rehearsal 4.45'},
                                  {'all-day': False,
                                   'begin': '2024-05-13 20:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-13 21:00:00+00:00',
                                   'location': None,
                                   'name': 'Helena Pilates 8pm'},
                                  {'all-day': False,
                                   'begin': '2024-05-15 20:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-16 00:00:00+00:00',
                                   'location': None,
                                   'name': 'Dee to stay before next day fight'},
                                  {'all-day': False,
                                   'begin': '2024-05-16 11:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-16 13:30:00+00:00',
                                   'location': None,
                                   'name': 'Amber collected for lunchtime walk '
                                           'between 11-1.30'},
                                  {'all-day': False,
                                   'begin': '2024-05-16 11:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-20 17:00:00+00:00',
                                   'location': None,
                                   'name': 'Helena girls trip with Katy and '
                                           'Dee (flight out 1.30)'},
                                  {'all-day': False,
                                   'begin': '2024-05-17 09:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-05-17 15:15:00+00:00',
                                   'location': '',
                                   'name': 'Lisa - British Museum trip'},
                                  {'all-day': False,
                                   'begin': '2024-05-17 09:30:00+00:00',
                                   'description': '\n',
                                   'end': '2024-05-17 16:00:00+00:00',
                                   'location': '',
                                   'name': 'Boiler Boys'},
                                  {'all-day': False,
                                   'begin': '2024-05-17 17:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-17 19:00:00+00:00',
                                   'location': None,
                                   'name': 'Make mayday flowers '},
                                  {'all-day': False,
                                   'begin': '2024-05-18 10:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-18 10:30:00+00:00',
                                   'location': None,
                                   'name': '10am May Day rehearsal '},
                                  {'all-day': False,
                                   'begin': '2024-05-18 14:15:00+00:00',
                                   'description': None,
                                   'end': '2024-05-18 18:00:00+00:00',
                                   'location': None,
                                   'name': 'May Day parade '},
                                  {'all-day': False,
                                   'begin': '2024-05-19 13:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-19 15:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa to Ellie’s Birthday 1-3'},
                                  {'all-day': False,
                                   'begin': '2024-05-19 13:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-05-19 16:00:00+00:00',
                                   'location': '',
                                   'name': 'Cubs open day in park 1-4'},
                                  {'all-day': False,
                                   'begin': '2024-05-20 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-20 08:30:00+00:00',
                                   'location': None,
                                   'name': 'Take Amber to daycare (returned by '
                                           'ACC)'},
                                  {'all-day': False,
                                   'begin': '2024-05-20 09:30:00+00:00',
                                   'description': None,
                                   'end': '2024-05-20 15:15:00+00:00',
                                   'location': None,
                                   'name': 'Lisa choir concert rehearsal '},
                                  {'all-day': False,
                                   'begin': '2024-05-20 19:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-20 21:00:00+00:00',
                                   'location': None,
                                   'name': 'Lisa choir concert at st '
                                           'Barnabus '},
                                  {'all-day': False,
                                   'begin': '2024-05-23 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-23 08:30:00+00:00',
                                   'location': None,
                                   'name': 'Amber to daycare (returned by '
                                           'ACC)'},
                                  {'all-day': False,
                                   'begin': '2024-05-24 15:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-28 16:00:00+00:00',
                                   'location': None,
                                   'name': 'Camping in Dorset '},
                                  {'all-day': False,
                                   'begin': '2024-05-28 09:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-28 10:00:00+00:00',
                                   'location': None,
                                   'name': 'Half term '},
                                  {'all-day': False,
                                   'begin': '2024-05-31 19:00:00+00:00',
                                   'description': None,
                                   'end': '2024-05-31 22:00:00+00:00',
                                   'location': None,
                                   'name': 'Nat’s 50th Birthday party'},
                                  {'all-day': False,
                                   'begin': '2024-06-06 08:00:00+00:00',
                                   'description': None,
                                   'end': '2024-06-06 09:00:00+00:00',
                                   'location': None,
                                   'name': 'Amber’s Birthday '},
                                  {'all-day': False,
                                   'begin': '2024-06-07 15:15:00+00:00',
                                   'description': None,
                                   'end': '2024-06-07 16:15:00+00:00',
                                   'location': None,
                                   'name': 'Year 6 Leavers Cake Sale - Save '
                                           'the Date'},
                                  {'all-day': False,
                                   'begin': '2024-06-14 16:30:00+00:00',
                                   'description': '\n',
                                   'end': '2024-06-16 16:00:00+00:00',
                                   'location': '',
                                   'name': 'Cubs summer camp'},
                                  {'all-day': False,
                                   'begin': '2024-06-24 08:15:00+00:00',
                                   'description': None,
                                   'end': '2024-06-24 16:15:00+00:00',
                                   'location': None,
                                   'name': 'Montpelier school closed day'},
                                  {'all-day': True,
                                   'begin': '2024-06-28 00:00:00+00:00',
                                   'description': '\n'
                                                  'Dear Mr Dan Newton\n'
                                                  'We are pleased to confirm '
                                                  'your booking.\n'
                                                  'You are booked at Swiss '
                                                  'Farm with the following '
                                                  'details:\n'
                                                  '\n'
                                                  'Holiday Details for booking '
                                                  'Reference: '
                                                  'SWF/1439233/945190\n'
                                                  '\n'
                                                  'Deluxe Tent Pitch\n'
                                                  '2 nights , 2 x Adult (16+) '
                                                  ', 2 x Children (3-15)\n'
                                                  'Arrival: Fri 28/06/2024\n'
                                                  'Departure: Sun 30/06/2024\n'
                                                  '£114.00\n'
                                                  '\n'
                                                  'Booking Total:\n'
                                                  '£114.00\n'
                                                  'Payment Received:\n'
                                                  '£50.00\n'
                                                  'Balance left to pay:\n'
                                                  '£64.00\n'
                                                  'Balance Due Date:\n'
                                                  '14 Jun 2024\n'
                                                  '\n'
                                                  'Dear Mr Matt Barr\n'
                                                  'Thank you for booking your '
                                                  'holiday online at Swiss '
                                                  'Farm with the following '
                                                  'details:\n'
                                                  '\n'
                                                  'Holiday Details for booking '
                                                  'Reference: '
                                                  'SWF/1439236/945193\n'
                                                  '\n'
                                                  'Deluxe Tent Pitch\n'
                                                  '2 nights , 2 x Adult (16+) '
                                                  ', 2 x Children (3-15)\n'
                                                  'Arrival: Fri 28/06/2024\n'
                                                  'Departure: Sun 30/06/2024\n'
                                                  '£114.00\n'
                                                  'Dogs\n'
                                                  'Qty: 1  for 2 days\n'
                                                  '£4.00\n'
                                                  '\n'
                                                  'Booking Total:\n'
                                                  '£118.00\n'
                                                  'Payment Received:\n'
                                                  '£118.00\n'
                                                  'Balance left to pay:\n'
                                                  '£0.00\n'
                                                  'Balance Due Date:\n'
                                                  '14 Jun 2024\n'
                                                  '\n',
                                   'end': '2024-07-01 00:00:00+00:00',
                                   'location': None,
                                   'name': 'Family camping'},
                                  {'all-day': False,
                                   'begin': '2024-07-06 11:00:00+00:00',
                                   'description': None,
                                   'end': '2024-07-06 15:00:00+00:00',
                                   'location': None,
                                   'name': 'Montpelier school fete'},
                                  {'all-day': False,
                                   'begin': '2024-07-14 09:00:00+00:00',
                                   'description': None,
                                   'end': '2024-07-14 12:00:00+00:00',
                                   'location': None,
                                   'name': 'Helena running ASICS London 10k'},
                                  {'all-day': False,
                                   'begin': '2024-07-15 18:10:00+00:00',
                                   'description': None,
                                   'end': '2024-07-15 19:15:00+00:00',
                                   'location': None,
                                   'name': 'Lisa swimming 6.30pm'},
                                  {'all-day': False,
                                   'begin': '2024-07-19 08:15:00+00:00',
                                   'description': None,
                                   'end': '2024-07-19 08:45:00+00:00',
                                   'location': None,
                                   'name': 'Lisa at Choir'},
                                  {'all-day': False,
                                   'begin': '2024-07-24 09:00:00+00:00',
                                   'description': None,
                                   'end': '2024-07-24 12:00:00+00:00',
                                   'location': None,
                                   'name': 'Helena hospital appointment 10.20'},
                                  {'all-day': False,
                                   'begin': '2024-07-24 13:00:00+00:00',
                                   'description': None,
                                   'end': '2024-07-24 14:00:00+00:00',
                                   'location': None,
                                   'name': 'Montpelier last day of term'},
                                  {'all-day': True,
                                   'begin': '2024-07-26 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-07-27 00:00:00+00:00',
                                   'location': '',
                                   'name': "Rich Davey's Birthday"},
                                  {'all-day': False,
                                   'begin': '2024-07-27 10:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-08-01 14:00:00+00:00',
                                   'location': '',
                                   'name': 'Cubs camp '},
                                  {'all-day': True,
                                   'begin': '2024-07-28 00:00:00+00:00',
                                   'description': '\n',
                                   'end': '2024-07-29 00:00:00+00:00',
                                   'location': '',
                                   'name': "Catherine's Birthday"},
                                  {'all-day': False,
                                   'begin': '2024-08-03 10:00:00+00:00',
                                   'description': None,
                                   'end': '2024-08-10 16:00:00+00:00',
                                   'location': None,
                                   'name': 'Girls to isle of W'},
                                  {'all-day': True,
                                   'begin': '2024-08-12 00:00:00+00:00',
                                   'description': None,
                                   'end': '2024-08-26 00:00:00+00:00',
                                   'location': '',
                                   'name': 'Sweden?'},
                                  {'all-day': False,
                                   'begin': '2024-08-21 16:00:00+00:00',
                                   'description': None,
                                   'end': '2024-08-22 10:45:00+00:00',
                                   'location': None,
                                   'name': 'Ferry Stockholm to Talin'},
                                  {'all-day': False,
                                   'begin': '2024-08-22 11:00:00+00:00',
                                   'description': None,
                                   'end': '2024-08-22 17:00:00+00:00',
                                   'location': None,
                                   'name': 'Talin'},
                                  {'all-day': False,
                                   'begin': '2024-08-22 17:00:00+00:00',
                                   'description': None,
                                   'end': '2024-08-23 10:30:00+00:00',
                                   'location': None,
                                   'name': 'Ferry Talin to Stockholm'},
                                  {'all-day': False,
                                   'begin': '2024-10-04 07:00:00+00:00',
                                   'description': None,
                                   'end': '2024-10-06 21:00:00+00:00',
                                   'location': None,
                                   'name': 'Helena girls weekend away'},
                                  {'all-day': False,
                                   'begin': '2024-11-13 09:00:00+00:00',
                                   'description': None,
                                   'end': '2024-11-13 12:00:00+00:00',
                                   'location': None,
                                   'name': 'Emily eye appointment 9.50'}],
                         'data_source_id': 'data_source_topic_1',
                         'timestamp': '2024-05-17 18:12:15+00:00'},
 'data_source_topic_2': {'data': [{'all-day': False,
                                   'begin': '2024-02-22 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-02-22 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-02-29 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-02-29 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-03-07 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-03-07 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-03-14 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-03-14 09:40:00+00:00',
                                   'location': None,
                                   'name': '(Absent) Lisa Barr (Lesson with '
                                           'Mark Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-03-21 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-03-21 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-03-27 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-03-27 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-04-18 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-04-18 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-04-25 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-04-25 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-05-09 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-05-09 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-05-15 13:20:00+00:00',
                                   'description': '',
                                   'end': '2024-05-15 13:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-05-23 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-05-23 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-06-06 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-06-06 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-06-13 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-06-13 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-06-20 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-06-20 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-06-27 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-06-27 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '},
                                  {'all-day': False,
                                   'begin': '2024-07-04 09:20:00+00:00',
                                   'description': '',
                                   'end': '2024-07-04 09:40:00+00:00',
                                   'location': None,
                                   'name': 'Lisa Barr (Lesson with Mark '
                                           'Walters) '}],
                         'data_source_id': 'data_source_topic_2',
                         'timestamp': '2024-05-17 18:12:16+00:00'}}"""
