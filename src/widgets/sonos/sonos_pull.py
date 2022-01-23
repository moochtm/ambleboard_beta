import soco
from soco.music_services import MusicService
import logging
import aiohttp_jinja2

logger = logging.getLogger(__name__)


async def handle_message(data_dict, request, ws_identifier):
    if "action" not in data_dict:
        logger.warning("No action entry in msg data.")
        return ""
    action = data_dict["action"]
    if action == "refresh":
        if "sonos_name" not in data_dict["widget_params"]:
            return
        context = await _get_sonos_status(
            request, ws_identifier, data_dict["widget_params"]["sonos_name"]
        )
        html = aiohttp_jinja2.render_string("sonos.html", request, context)
        print(html)
        return html
    return ""


async def _get_sonos_status(request, ws_identifier, sonos_name):
    """
    Sends Sonos info to web socket.
    """
    logger.info(f"Responding to client {ws_identifier}")
    try:
        # get Sonos device and general info
        device = soco.discovery.by_name(sonos_name)
        transport_info = device.get_current_transport_info()
        logger.debug(f"transport info: {transport_info}")
        track_info = device.get_current_track_info()
        logger.debug(f"track info: {track_info}")
        media_info = device.get_current_media_info()
        logger.debug(f"media info: {media_info}")
    except Exception:
        raise
    # start getting the info we're interested in
    transport = transport_info["current_transport_state"]
    img_src = track_info["album_art"]
    if img_src != "":
        title = track_info["title"]
        artist = track_info["artist"]
        album = track_info["album"]
    # if there's no img_src in track info, we might be playing a radio station
    else:
        channel = media_info["channel"]
        tunein = MusicService("TuneIn")
        # search Tunein for value of channel
        results = tunein.search(category="stations", term=channel)
        if len(results) > 0:
            result = results[0]
            img_src = result.metadata["stream_metadata"].metadata["logo"]
        title = channel
        artist = ""
        album = ""
    # Return context dict
    return {
        "transport": transport,
        "title": title,
        "artist": artist,
        "album": album,
        "img_src": img_src,
    }
