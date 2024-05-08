import asyncio
from ds_base import BaseDataSource
import soco
from soco import events_asyncio

soco.config.EVENTS_MODULE = events_asyncio
import json
import arrow
import logging

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class DataSource(BaseDataSource):
    type = "sonos"
    wait_time = 1

    def __init__(self, device):
        self.device = device
        self.name = device.player_name

    async def get_data(self):
        context = {"av_transport": {}, "rendering_control": {}}

        def av_transport_event_handler(event):
            logger.info(
                f"SONOS av_transport event received: device={self.device.player_name}, event.variables={event.variables}"
            )
            context["av_transport"] = event.variables
            # convert values that are soco.data_structures (e.g. music track metadata) to dicts
            for key, value in context["av_transport"].items():
                if "soco.data_structures" in str(type(value)):
                    context["av_transport"][key] = value.to_dict()
                    # create FULL uri for album art (if 'http' not found in current value).
                    if "album_art_uri" in context["av_transport"][key]:
                        if (
                            context["av_transport"][key]["album_art_uri"][:4] != "http"
                            and context["av_transport"][key]["album_art_uri"].strip()
                            != ""
                        ):
                            context["av_transport"][key][
                                "album_art_uri"
                            ] = f"http://{self.device.ip_address}:1400{context['av_transport'][key]['album_art_uri']}"

            # helper: add current_track_exists:
            context["av_transport"]["current_track_exists"] = (
                False
                if context["av_transport"]["current_track_meta_data"] == ""
                or context["av_transport"]["current_track_meta_data"]["title"].strip()
                == ""
                else True
            )

            # helper: add next_track_exists:
            context["av_transport"]["next_track_exists"] = (
                False
                if context["av_transport"]["next_track_meta_data"] == ""
                or context["av_transport"]["next_track_meta_data"]["title"].strip()
                == ""
                else True
            )

            # add device info to context
            # https://docs.python-soco.com/en/latest/api/soco.core.html
            # this code is duplicated below
            context["device_info"] = {
                "player_name": self.device.player_name,
                "ip_address": self.device.ip_address,
                "play_mode": self.device.play_mode,
                "shuffle": self.device.shuffle,
                "repeat": self.device.repeat,
                "mute": self.device.mute,
                "volume": self.device.volume,
                "is_playing_radio": self.device.is_playing_radio,
                "is_playing_tv": self.device.is_playing_tv,
                "music_source": self.device.music_source,
            }

            logger.info(f"Sonos Created context: {context}")

            # publisher.publish(publish_key, context)
            # type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context
            payload = context
            self.send_message(payload)

        def rendering_control_event_handler(event):
            logger.info(
                f"SONOS rendering_control event received: device={self.device.player_name}, event.variables={event.variables}"
            )
            context["rendering_control"] = event.variables

            # add device info to context
            # https://docs.python-soco.com/en/latest/api/soco.core.html
            # this code is duplicated above
            context["device_info"] = {
                "player_name": self.device.player_name,
                "ip_address": self.device.ip_address,
                "play_mode": self.device.play_mode,
                "shuffle": self.device.shuffle,
                "repeat": self.device.repeat,
                "mute": self.device.mute,
                "volume": self.device.volume,
                "is_playing_radio": self.device.is_playing_radio,
                "is_playing_tv": self.device.is_playing_tv,
                "music_source": self.device.music_source,
            }

            logger.debug(f"Created context: {json.dumps(context, indent=4)}")

            # publisher.publish(publish_key, context)
            # type(self).worker_prev_update[str(publisher.prefix + publish_key)] = context
            payload = context
            self.send_message(payload)

        sub = await self.device.avTransport.subscribe(
            requested_timeout=600, auto_renew=True
        )
        sub.callback = av_transport_event_handler
        rendering_sub = await self.device.renderingControl.subscribe(
            requested_timeout=600, auto_renew=True
        )
        rendering_sub.callback = rendering_control_event_handler

        while True:

            # renew subscriptions every 5 minutes
            # print(sub.time_left)
            await asyncio.sleep(0)
            # continue
            # await sub.renew()
            # sub.callback = av_transport_event_handler
            # await rendering_sub.renew()
            # rendering_sub.callback = rendering_control_event_handler


async def main():

    tasks = []
    for device in soco.discovery.discover():
        print(device.player_name)
        ds = DataSource(device=device)
        tasks.append(asyncio.create_task(ds.start()))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
