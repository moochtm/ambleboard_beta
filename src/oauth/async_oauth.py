"""
module that handles different oauth

receives:
- third-party provider
- user ID

already knows:
- scopes required by all widgets
- client id and secret of all provider apps

uses:
- token save/retrieve

returns:
- headers dict specific to third-party provider
OR
- object that includes an aiohttp session? Depends if provider headers may need to change depending on request method?

usage:
in external module:

def cannot_authenticate():
    send "need to auth" message

oc = ProviderOauthClient(user_id)
if not oc.load_token()
    cannot_authenticate()
response = os.async_request(...)
if not response:
    cannot_authenticate()

def auth_from_existing_token(user_id)
    if self.token = None:
        self.load_token()
    if self.token = None:
        return False
    set self.bearer_token
    set self.refresh_token

def auth_from_refresh_token(user_id)

def auth_from_flow(user_id)

def response_not_authenticated(response)

"""
import asyncio
from asyncio.exceptions import TimeoutError
import json
from functools import partial, wraps

from aiohttp import web
from aiohttp.client import ClientSession, ClientTimeout
import src.oauth.token_storage as token_storage

import logging

logger = logging.getLogger(__name__)

HTTP_GET = "get"
HTTP_POST = "post"
HTTP_PUT = "put"
HTTP_PATCH = "patch"
HTTP_DELETE = "delete"
HTTP_ALLOWED = [HTTP_GET, HTTP_POST, HTTP_PUT, HTTP_PATCH, HTTP_DELETE]

# These keys will be used on the aiohttp session
TOKEN_CACHE = "token_cache"
FLOW_CACHE = "flow_cache"
USER_EMAIL = "mail"


class AsyncOauthClient:
    provider = None
    client_id = None
    client_secret = None
    scope = None
    redirect_uri = "https://www.httpbin.org/anything"

    def __init__(self, user_id):
        self.user_id = user_id
        # self.session = ClientSession()
        self.token = None
        self.bearer_token = None
        self.refresh_token = None

    #####################################################################
    # These methods may need to be overwritten by inheriting classes

    def parse_token(self):
        self.bearer_token = self.token

    def authenticate_from_refresh_token(self):
        return False

    def authenticate_from_flow(self):
        return False

    def set_provider_headers(self, method, **kwargs):
        return kwargs

    def response_is_authenticated(self, response):
        return response.status != 401

    #####################################################################
    # Methods below this point should be usable by all inheriting classes

    def load_token(self):
        if not token_storage.token_exists(self.provider, self.user_id):
            logger.debug("Could not find token file.")
            return False
        self.token = token_storage.load_token(self.provider, self.user_id)
        if not self.parse_token():
            logger.debug("Could not parse token file.")
            self.delete_token()
            return False
        return True

    def save_token(self, token):
        token_storage.save_token(self.provider, self.user_id, token)
        self.token = token
        self.parse_token()
        return True

    def delete_token(self):
        token_storage.delete_token(self.provider, self.user_id)

    async def async_request(self, method, url, **kwargs):
        if not self.bearer_token:
            logger.warning("No Bearer Token")
            return False

        assert method in HTTP_ALLOWED, "Method must be one of the allowed ones"

        kwargs = kwargs.copy()
        # Ensure headers exist & make a copy
        kwargs["headers"] = headers = dict(kwargs.get("headers", {}))
        headers["Authorization"] = "Bearer " + self.bearer_token

        kwargs = self.set_provider_headers(method, **kwargs)
        if "data" in kwargs:
            kwargs["data"] = json.dumps(kwargs["data"])  # auto convert to json

        session = ClientSession()
        timeout = ClientTimeout(total=5)
        result = False
        timeout_count = 0
        while True:
            try:
                async with session.request(
                    method, url, timeout=timeout, **kwargs
                ) as response:
                    result = await response.json()
                    logger.debug(result)
                    if self.response_is_authenticated(response):
                        logger.debug("Successful response.")
                        break
                    logger.warning("Token didn't work. Deleting token.")
                    self.delete_token()
                    if self.authenticate_from_refresh_token():
                        logger.debug("Successfully authenticated using refresh token.")
                        headers["Authorization"] = "Bearer " + self.bearer_token
                        continue

                # response = await session.request(method, url, timeout=timeout, **kwargs)
            except Exception as e:
                logger.error(e)
                timeout_count += 1
                if timeout_count == 5:
                    break
                continue
            break
        await session.close()
        return result
