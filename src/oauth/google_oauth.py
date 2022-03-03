from src.oauth.async_oauth import AsyncOauthClient
from requests_oauthlib import OAuth2Session
import asyncio

import logging

logger = logging.getLogger(__name__)


class GoogleAsyncOauthClient(AsyncOauthClient):
    provider = "google"
    client_id = (
        "485012684882-37k8c45biebfl1dn372sj9ftop1q63m3.apps.googleusercontent.com"
    )
    client_secret = "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"
    scope = ["https://www.googleapis.com/auth/photoslibrary"]
    authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_uri = "https://www.googleapis.com/oauth2/v4/token"
    extra = {
        "client_id": client_id,
        "client_secret": client_secret,
    }

    def parse_token(self):
        try:
            self.bearer_token = self.token["access_token"]
            self.refresh_token = self.token["refresh_token"]
        except KeyError:
            return False
        return True

    def authenticate_from_flow(self):
        app = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
            auto_refresh_url=self.token_uri,
            auto_refresh_kwargs=self.extra,
        )
        authorization_url, _ = app.authorization_url(
            self.authorization_base_url, access_type="offline", prompt="consent"
        )
        print(
            f"Please go to the URL below and sign in as {self.user_id}\n{authorization_url}\n",
        )

        # Get the authorization verifier code from the callback url
        code = input("Paste the code string here:\n")

        token = app.fetch_token(
            self.token_uri, client_secret=self.client_secret, code=code
        )
        print(token)
        self.save_token(token)

    def authenticate_from_refresh_token(self):
        logger.info("Trying to auth using refresh token.")
        app = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
            auto_refresh_url=self.token_uri,
            auto_refresh_kwargs=self.extra,
            token=self.token,
        )
        token = app.refresh_token(self.token_uri)
        logger.info(f"Token: {token}")
        if "error" in token:
            return False
        self.save_token(token)
        return True

    def set_provider_headers(self, method, **kwargs):
        if method == "get":
            kwargs.setdefault("allow_redirects", True)
        elif method in ["post", "put", "patch"]:
            kwargs["headers"]["Content-type"] = "application/json"
        return kwargs


async def main():
    user_id = input("Enter the email address you will use when logging in:\n")
    client = GoogleAsyncOauthClient(user_id=user_id)
    need_to_auth_flow = False
    if not client.load_token():
        print("PLEASE AUTHENTICATE")
        need_to_auth_flow = (
            True  # In a widget this would be a return as auth is done by separate tool
        )
    else:
        print("TOKEN LOADED")

    if need_to_auth_flow:
        client.authenticate_from_flow()


if __name__ == "__main__":
    asyncio.run(main())
