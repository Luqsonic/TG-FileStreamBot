# Taken from megadlbot_oss <https://github.com/eyaadh/megadlbot_oss/blob/master/mega/webserver/routes.py>
# Thanks to Eyaadh <https://github.com/eyaadh>
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import json
import math
import os
import time
import requests
from PIL import Image
import telebot
import time
from helper_funcs.display_progress import humanbytes
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image

import re
import secrets
import mimetypes
from aiohttp import web
from WebStreamer.vars import Var
from WebStreamer.bot import StreamBot
from WebStreamer import StartTime, __version__, bot_info
from WebStreamer.utils.time_format import get_readable_time
from WebStreamer.utils.custom_dl import TGCustomYield, chunk_size, offset_fix

routes = web.RouteTableDef()
bot_token = "1412992512:AAHb8GUexB17g_v9O990SLRWM4OPf64QhnU"
bot = telebot.TeleBot(token=bot_token)

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

async def ddl_call_back(bot,file_string,link,update):
    cb_data = file_string

    # youtube_dl exteactors
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")
    thumb_image_path = "./DOWNLOADS" + \
        "/" + str(6828282) + ".jpg"
    youtube_dl_url = link
    custom_file_name = os.path.basename(youtube_dl_url)
    if "http" in youtube_dl_url:
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        logger.info(youtube_dl_url)
        logger.info(custom_file_name)
        
    description = ""
    start = datetime.now()

    tmp_directory_for_each_user = "./DOWNLOADS" + "/" + str(update.from_user.id)
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    command_to_exec = []
    async with aiohttp.ClientSession() as session:
        c_time = time.time()
        try:
            await download_coroutine(
                session,
                youtube_dl_url,
                download_directory,
                c_time
            )
        except asyncio.TimeoutError:
            return False
            
    if os.path.exists(download_directory):
        end_one = datetime.now()

        file_size = 2097152000 + 1
        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError as exc:
            download_directory = os.path.splitext(download_directory)[0] + "." + "mkv"
            # https://stackoverflow.com/a/678242/4723940
            file_size = os.stat(download_directory).st_size
        if file_size > 2097152000:
			return
        else:
            # get the correct width, height, and duration for videos greater than 10MB
            # ref: message from @BotSupport
            width = 0
            height = 0
            duration = 0
            if tg_send_type != "file":
                metadata = extractMetadata(createParser(download_directory))
                if metadata is not None:
                    if metadata.has("duration"):
                        duration = metadata.get('duration').seconds
            # get the correct width, height, and duration for videos greater than 10MB
            if os.path.exists(thumb_image_path):
                width = 0
                height = 0
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                if tg_send_type == "vm":
                    height = width
                # resize image
                # ref: https://t.me/PyrogramChat/44663
                # https://stackoverflow.com/a/21669827/4723940
                Image.open(thumb_image_path).convert(
                    "RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                # https://stackoverflow.com/a/37631799/4723940
                # img.thumbnail((90, 90))
                if tg_send_type == "file":
                    img.resize((320, height))
                else:
                    img.resize((90, height))
                img.save(thumb_image_path, "JPEG")
                # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#create-thumbnails
            else:
                thumb_image_path = None
            start_time = time.time()
            # try to upload file
            if tg_send_type == "file":
                await bot.send_document(
                    update.chat.id,
                    download_directory)
            else:
                logger.info("Did this happen? :\\")
            end_two = datetime.now()
            try:
                os.remove(download_directory)
                os.remove(thumb_image_path)
            except:
                pass
            """
            time_taken_for_download = (end_one - start).seconds
            time_taken_for_upload = (end_two - end_one).seconds
            )"""



async def download_coroutine(session, url, file_name, start):
    downloaded = 0
    display_message = ""
    async with session.get(url, timeout=3600) as response:
        total_length = int(response.headers["Content-Length"])
        content_type = response.headers["Content-Type"]
        if "text" in content_type and total_length < 500:
            return await response.release()

        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(128)
                if not chunk:
                    break
                f_handle.write(chunk)
                downloaded += 128
                now = time.time()
                diff = now - start
                if round(diff % 5.00) == 0 or downloaded == total_length:
                    percentage = downloaded * 100 / total_length
                    speed = downloaded / diff
                    elapsed_time = round(diff) * 1000
                    time_to_completion = round(
                        (total_length - downloaded) / speed) * 1000
                    estimated_total_time = elapsed_time + time_to_completion
                    try:
                        current_message = """**Download Status**
URL: {}
File Size: {}
Downloaded: {}
ETA: {}""".format(
    os.path.basename(url),
    humanbytes(total_length),
    humanbytes(downloaded),
    TimeFormatter(time_to_completion)
)
                        if current_message != display_message:
                            display_message = current_message
                    except Exception as e:
                        logger.info(str(e))
                        pass
        return await response.release()
        
        
#dd
def DownLoadFile(url, file_name, chunk_size, client, ud_type, message_id, chat_id):
    if os.path.exists(file_name):
        os.remove(file_name)
    if not url:
        return file_name
    r = requests.get(url, allow_redirects=True, stream=True)
    # https://stackoverflow.com/a/47342052/4723940
    total_size = int(r.headers.get("content-length", 0))
    downloaded_size = 0
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
                downloaded_size += chunk_size
            if client is not None:
                if ((total_size // downloaded_size) % 5) == 0:
                    time.sleep(0.3)
                    try:
                        client.edit_message_text(
                            chat_id,
                            message_id,
                            text="{}: {} of {}".format(
                                ud_type,
                                humanbytes(downloaded_size),
                                humanbytes(total_size)
                            )
                        )
                    except:
                        pass
    return file_name

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"server_status": "running",
                              "uptime": get_readable_time(time.time() - StartTime),
                              "telegram_bot": '@'+ bot_info.username,
                              "version": __version__})


@routes.get(r"/{link:\S+}")
async def stream_handler(request):
    link = request.match_info['link']
    url = link
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    jk = "hsh"
    if jk is not None:
        if url is not None:
            url = url.strip()
        if file_name is not None:
            file_name = file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(url)
        logger.info(file_name)
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]
    proxy = ""            
    if proxy != "":
        command_to_exec = [
            "youtube-dl",
            "--no-warnings",
            "--youtube-skip-dash-manifest",
            "-j",
            url,
            "--proxy", proxy
        ]
    else:
        command_to_exec = [
            "youtube-dl",
            "--no-warnings",
            "--youtube-skip-dash-manifest",
            "-j",
            url
        ]
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)
    # logger.info(command_to_exec)
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    # logger.info(e_response)
    t_response = stdout.decode().strip()
    # logger.info(t_response)
    # https://github.com/rg3/youtube-dl/issues/2630#issuecomment-38635239
    if e_response and "nonnumeric port" not in e_response:
        # logger.warn("Status : FAIL", exc.returncode, exc.output)
        error_message = e_response.replace("please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.", "")
        if "This video is only available for registered users." in error_message:
            error_message += "Boom"
        return False
    if t_response:
        # logger.info(t_response)
        x_reponse = t_response
        if "\n" in x_reponse:
            x_reponse, _ = x_reponse.split("\n")
        response_json = json.loads(x_reponse)
        save_ytdl_json_path = "./DOWNLOADS" + \
            "/" + str(update.from_user.id) + ".json"
        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)
        # logger.info(response_json)
        inline_keyboard = []
        duration = None
        if "duration" in response_json:
            duration = response_json["duration"]
        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note")
                if format_string is None:
                    format_string = formats.get("format")
                format_ext = formats.get("ext")
                approx_file_size = ""
                if "filesize" in formats:
                    approx_file_size = humanbytes(formats["filesize"])
                cb_string_video = "{}|{}|{}".format(
                    "video", format_id, format_ext)
                cb_string_file = "{}|{}|{}".format(
                    "file", format_id, format_ext)

            if duration is not None:
                cb_string_64 = "{}|{}|{}".format("audio", "64k", "mp3")
                cb_string_128 = "{}|{}|{}".format("audio", "128k", "mp3")
                cb_string = "{}|{}|{}".format("audio", "320k", "mp3")
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "MP3 " + "(" + "64 kbps" + ")", callback_data=cb_string_64.encode("UTF-8")),
                    InlineKeyboardButton(
                        "MP3 " + "(" + "128 kbps" + ")", callback_data=cb_string_128.encode("UTF-8"))
                ])
                inline_keyboard.append([
                    InlineKeyboardButton(
                        "MP3 " + "(" + "320 kbps" + ")", callback_data=cb_string.encode("UTF-8"))
                ])
        else:
            format_id = response_json["format_id"]
            format_ext = response_json["ext"]
            cb_string_file = "{}|{}|{}".format(
                "file", format_id, format_ext)
            cb_string_video = "{}|{}|{}".format(
                "video", format_id, format_ext)
           cb_string_file = "{}={}={}".format(
                "file", format_id, format_ext)
            cb_string_video = "{}={}={}".format(
                "video", format_id, format_ext)
        # logger.info(reply_markup)
        thumbnail = "https://placehold.it/90x90"
        thumbnail_image = "https://placehold.it/90x90"
        if "thumbnail" in response_json:
            if response_json["thumbnail"] is not None:
                thumbnail = response_json["thumbnail"]
                thumbnail_image = response_json["thumbnail"]
        thumb_image_path = DownLoadFile(
            thumbnail_image,
            "./DOWNLOADS" + "/" +
            str(update.from_user.id) + ".webp",
            128,
            None,  # bot,
            "Start Download",
            update.message_id,
            update.chat.id
        )
        if os.path.exists(thumb_image_path):
            im = Image.open(thumb_image_path).convert("RGB")
            im.save(thumb_image_path.replace(".webp", ".jpg"), "jpeg")
        else:
            thumb_image_path = None
        
        
            k = await bot.send_message(
            -559454773,
            "Download",
        )

        await ddl_call_back(bot,cb_string_file,k)
