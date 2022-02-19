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

oc = AsyncOauthClient('provider', 'user ID')
if not oc.authenticate():
    do something
"""
import asyncio
import json
from functools import partial, wraps

from aiohttp import web
from aiohttp.client import ClientSession, _RequestContextManager
import src.oauth.token_storage as token_storage


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


def async_wrap(func):
    """Wrap a function doing I/O to run in an executor thread."""

    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


class AsyncOauthClient:
    provider = None
    client_id = None
    client_secret = None
    scope = None
    redirect_uri = "https://www.httpbin.org/anything"

    def __init__(self, user_id=None):
        self.user_id = user_id
        self.session = ClientSession()
        self.token = None

    async def __aexit__(self):
        await self.session.close()

    def load_token(self, user_id):
        if not token_storage.token_exists(self.provider, user_id):
            return
        self.token = token_storage.load_token(self.provider, user_id)
        return self.token

    def save_token(self, user_id, token):
        token_storage.save_token(self.provider, user_id, token)
        self.token = token

    def delete_token(self, user_id):
        token_storage.delete_token(self.provider, user_id)

    def authenticate(self, user_id):
        """
        Initiates OAuth2 authentication and authorization flow.
        Sets self.token
        """
        # do something

    def set_provider_headers(self, method, **kwargs):
        return kwargs

    async def async_request(self, method, url, **kwargs):
        assert method in HTTP_ALLOWED, "Method must be one of the allowed ones"
        if not self.token:
            self.authenticate()

        kwargs = kwargs.copy()
        # Ensure headers exist & make a copy
        kwargs["headers"] = headers = dict(kwargs.get("headers", {}))
        headers["Authorization"] = "Bearer " + self.token

        kwargs = self.set_provider_headers(method, **kwargs)
        if "data" in kwargs:
            kwargs["data"] = json.dumps(kwargs["data"])  # auto convert to json
        result = await self.session.request(method, url, **kwargs)
        if result.status == 401:
            self.delete_token(self.user_id)
        return await result.json()

    async def close_session(self):
        await self.session.close()
