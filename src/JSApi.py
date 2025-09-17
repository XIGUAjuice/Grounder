# %%
import base64
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from TokenGetter import TokenGetter
from Verification import Verification

# %%
logger = logging.getLogger(__name__)


class JSApi:
    headers = {
        "Connection": "keep-alive",
        "os_type": "wechat_mini",
        "os_version": "Windows 11 x64",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13)XWEB/14185",
        "Content-Type": "application/json",
        "xweb_xhr": "1",
        "device_type": "microsoft",
        "gw_channel": "api",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxbd4ec54a9e9ce6dd/137/page-frame.html",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    appid_get = "80bf61101d10feb1bd0229416ec73a26"
    appid_post = "0ff444f417de34c1352af3b3ffc30348"
    url_book_time = "https://jsapp.jussyun.com/jiushi-core/venue/getVenueBookTime"
    url_venue = "https://jsapp.jussyun.com/jiushi-core/venue/list"
    url_user = "https://jsapp.jussyun.com/jiushi-core/user/getUserInfo"
    url_contact = "https://jsapp.jussyun.com/jiushi-core/user/contact/v2-get/query-list-user-contact"
    url_ground = "https://jsapp.jussyun.com/jiushi-core/venue/getVenueGround"
    url_book = "https://jsapp.jussyun.com/jiushi-core/venue/bookVenue/v2"
    sign_key = "527093093C418483029EEC61F70E9DD1"
    sign_secret = "EB70CBAE71094894EE5BD30A68A3C548"
    aes_key1 = "jsVenueV20240101".encode()
    aes_key2 = "Bangdao01bangdao".encode()
    iv = "1234567890123456".encode()

    def __init__(self):
        self.token_getter = TokenGetter()
        self.headers["token"] = self.token_getter.read_token()
        self.assets_path = Path(__file__).parents[1] / "assets"
        self.verification = Verification(self.assets_path / "trace.json")

    def get_token(self):
        if self.token_getter.get_token() is True:
            token = self.token_getter.read_token()
            if token is not None:
                self.headers["token"] = self.token_getter.read_token()
                return True
        return False

    def post_sign(self, payload_str):
        sign_str = f"{payload_str}{self.sign_key}"
        payload_bytes = sign_str.encode("utf-8")
        md5_hash = hashlib.md5(payload_bytes).hexdigest()
        sign = base64.b64encode(md5_hash.encode("utf-8")).decode("utf-8")
        return sign

    def get_sign(self, params):
        sign_str = "".join([f"&{k}={v}" for k, v in sorted(params.items())])
        sign_str += self.sign_secret
        sign_str = sign_str.lstrip("&")
        params_bytes = sign_str.encode("utf-8")
        md5_hash = hashlib.md5(params_bytes).hexdigest().upper()
        sign = base64.b64encode(md5_hash.encode("utf-8")).decode("utf-8")
        return sign

    def get_cipher_text(self, payload):
        payload_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        logger.info(f"Payload str: {payload_str}")
        cipher_text = self.aes_encrypt(payload_str)
        return cipher_text

    def aes_encrypt(self, data, key=aes_key1, iv=iv):
        cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
        padded_data = pad(data.encode("utf-8"), cipher.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode("utf-8")

    def aes_decrypt(self, cipher_text, key=aes_key1, iv=iv):
        cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
        encrypted_data = base64.b64decode(cipher_text)
        decrypted = cipher.decrypt(encrypted_data).decode("utf-8")
        return decrypted

    async def js_post(self, url, payload, params=None):
        payload_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        logger.debug(f"Payload: {payload_str}")
        js_sign = self.post_sign(payload_str)

        self.headers["js_sign"] = js_sign
        self.headers["app_id"] = self.appid_post
        if hasattr(self, "phone"):
            self.headers["fullMobile"] = self.phone

        async with httpx.AsyncClient() as client:
            if params is not None:
                response = await client.post(
                    url, headers=self.headers, params=params, data=payload_str
                )
            else:
                response = await client.post(
                    url, headers=self.headers, data=payload_str
                )

        logger.debug(f"headers: {response.request.headers}")
        logger.debug(f"url: {response.request.url}")
        logger.debug(f"content: {response.request.content}")
        logger.debug(response.text)

        if "token.device.invalid" in response.text:
            logger.error("token 过期，请重新登录")
            raise Exception("token is expired")

        if response.status_code == 200:
            return response
        else:
            logger.error(f"HTTP Error: {response.status_code}")
            raise httpx.HTTPStatusError(f"HTTP Error: {response.status_code}")

    async def js_get(self, url, params):
        sign = self.get_sign(params)
        params["sign"] = sign
        self.headers["app_id"] = self.appid_get
        if hasattr(self, "phone"):
            self.headers["fullMobile"] = self.phone

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)

        logger.debug(f"headers: {response.request.headers}")
        logger.debug(f"url: {response.request.url}")
        logger.debug(f"content: {response.request.content}")
        logger.info(response.text)

        if "token.device.invalid" in response.text:
            logger.error("token 过期，请重新登录")
            raise Exception("token is expired")

        if response.status_code == 200:
            return response
        else:
            raise httpx.HTTPStatusError(f"HTTP Error: {response.status_code}")

    async def get_ground(self, venue_id, timestamp):
        payload = {
            "venueId": venue_id,
            "bookTime": str(timestamp),
        }
        resp = await self.js_post(self.url_ground, payload)
        data = resp.json()
        ground_list = data["data"]["statusList"]
        return ground_list

    async def get_venue_list(self, sports_name):
        payload = {
            "sportName": sports_name,
            "userLatitude": "",
            "userLongitude": "",
        }
        resp = await self.js_post(self.url_venue, payload)
        data = resp.json()
        venue_list = data["data"]
        return venue_list

    async def get_user_info(self):
        resp = await self.js_post(self.url_user, {})
        data = resp.json()
        user_info = data["data"]
        self.user_info = user_info
        phone = self.aes_decrypt(user_info["fullMobile"], key=self.aes_key2)
        self.phone = self.remove_non_printable(phone)
        return user_info

    async def get_contact(self):
        params = {
            "inWhite": "false",
            "os_type": "wechat_mini",
            "uid": self.user_info["uid"],
        }
        resp = await self.js_get(self.url_contact, params)
        data = resp.json()
        cantacts = data["data"][1]["contacts"]
        self.contacts = cantacts
        return cantacts

    def datetime_to_midnight_timestamp(self, dt: datetime):
        """Convert a datetime object to a timestamp at midnight."""
        dt_midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(dt_midnight.timestamp()) * 1000

    def get_timestamps_from_now(self, days=9):
        now = datetime.now()
        dts = [now + timedelta(days=_days) for _days in range(days)]
        timestamps = [self.datetime_to_midnight_timestamp(dt) for dt in dts]
        return timestamps

    async def post_book(
        self,
        contact_id,
        venue_id,
        venue_name,
        agency_id,
        agency_name,
        sports_name,
        ground_list,
    ):
        payload = {
            "contactId": contact_id,
            "venueId": venue_id,
            "venueName": venue_name,
            "agencyId": agency_id,
            "agencyName": agency_name,
            "sportsName": sports_name,
            "venueBookGroundModelList": ground_list,
            "voucherFlowId": None,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        logger.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        payload = {"ciphertext": self.get_cipher_text(payload)}
        resp = await self.js_post(self.url_book, payload)
        html = resp.text
        self.save_html(html)
        url_verified = self.verification.solve("v2.html")
        url_parsed = urlparse(url_verified)
        query_params = parse_qs(url_parsed.query)
        query_params["u_aref"] = "wxCaptcha"
        response = await self.js_post(self.url_book, payload, params=query_params)
        return response

    def save_html(self, html_content: str, filename: str = "v2.html"):
        url_pattern = re.compile(r"(src ?= ?['\"])//")
        html_content = url_pattern.sub(r"\1https://", html_content)
        html_content = html_content.replace("form.submit();", "")
        with open(self.assets_path / filename, "w", encoding="utf-8") as f:
            f.write(html_content)

    def remove_non_printable(self, str: str):
        return "".join(ch for ch in str if ch.isprintable())
