from src.oauth.async_oauth import AsyncOauthClient
from msal import ConfidentialClientApplication, SerializableTokenCache
import asyncio

import logging

logger = logging.getLogger(__name__)


class MicrosoftAsyncOauthClient(AsyncOauthClient):
    provider = "microsoft"
    client_id = "6999faa8-1bd2-4804-89fd-9cb5341ddc56"
    client_secret = "H0o7Q~0xWSGQc7Ks5teP9dGOIpsgxObyG~RcA"
    scope = ["User.Read", "User.Read.All", "Calendars.Read", "Group.Read.All"]
    authority = None

    def parse_token(self):
        try:
            self.bearer_token = self.token["access_token"]
            self.refresh_token = self.token["refresh_token"]
        except KeyError:
            return False
        return True

    def authenticate_from_flow(self):
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            validate_authority=False,
        )
        auth_code_flow = app.initiate_auth_code_flow(
            self.scope,
            redirect_uri=self.redirect_uri,
        )
        authorization_url = auth_code_flow["auth_uri"]

        print(
            f"Please go to the URL below and sign in as {self.user_id}\n{authorization_url}\n",
        )

        # Get the authorization verifier code from the callback url
        client_info = input("Paste the client_info string here:\n")
        code = input("Paste the code string here:\n")
        state = input("Paste the state string here:\n")
        # user_id = input("Enter the email address you used when logging in:\n")

        auth_response = {"client_info": client_info, "code": code, "state": state}

        token = app.acquire_token_by_auth_code_flow(
            auth_code_flow=auth_code_flow, auth_response=auth_response
        )
        print(token)
        self.save_token(token)

    def authenticate_from_refresh_token(self):
        logger.info("Trying to auth using refresh token.")
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            validate_authority=False,
        )
        token = app.acquire_token_by_refresh_token(
            refresh_token=self.token["refresh_token"], scopes=self.scope
        )
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

    def set_bearer_token(self):
        self.bearer_token = self.token["access_token"]


async def main():
    user_id = input("Enter the email address you used when logging in:\n")
    client = MicrosoftAsyncOauthClient(user_id=user_id)
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

    response = await client.async_request("get", "https://graph.microsoft.com/v1.0/me")
    if not response:
        print("PLEASE AUTHENTICATE")
    else:
        print(response)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
