# Taken from megadlbot_oss <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/webserver/routes.py>
# Thanks to Eyaadh <https://github.com/eyaadh>
import re
import time
import math
import logging
import secrets
import mimetypes
from aiohttp import web
from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot
from WebStreamer import StartTime, __version__, bot_info
from WebStreamer.utils.time_format import get_readable_time
from WebStreamer.utils.custom_dl import TGCustomYield, chunk_size, offset_fix

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"server_status": "running",
                              "uptime": get_readable_time(time.time() - StartTime),
                              "telegram_bot": '@'+ bot_info.username,
                              "version": __version__})


@routes.get(r"/{link:\S+}")
async def stream_handler(request):
    try:
        message_id = request.match_info['link']
        return web.json_response({"server_status": message_id })
    except ValueError as e:
        logging.error(e)
        raise web.HTTPNotFound
    except AttributeError:
        pass

