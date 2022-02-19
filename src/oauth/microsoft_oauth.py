from async_oauth import AsyncOauthClient
from msal import ConfidentialClientApplication, SerializableTokenCache
import asyncio


class MicrosoftAsyncOauthClient(AsyncOauthClient):
    provider = "microsoft"
    client_id = "6999faa8-1bd2-4804-89fd-9cb5341ddc56"
    client_secret = "H0o7Q~0xWSGQc7Ks5teP9dGOIpsgxObyG~RcA"
    scope = ["User.Read", "User.Read.All", "Calendars.Read", "Group.Read.All"]
    authority = None

    def authenticate(self, user_id=None):
        self.user_id = user_id or self.user_id
        if self.user_id:
            self.token = self.load_token(self.user_id)
            if self.token:
                return

        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            validate_authority=False,
            token_cache=None,
        )
        auth_code_flow = app.initiate_auth_code_flow(
            self.scope,
            redirect_uri=self.redirect_uri,
        )
        authorization_url = auth_code_flow["auth_uri"]

        print(
            f"Please go here and sign in: {authorization_url}\n",
        )

        # Get the authorization verifier code from the callback url
        client_info = input("Paste the client_info string here:\n")
        code = input("Paste the code string here:\n")
        state = input("Paste the state string here:\n")
        user_id = input("Enter the email address you used when logging in:\n")

        auth_response = {"client_info": client_info, "code": code, "state": state}

        token = app.acquire_token_by_auth_code_flow(
            auth_code_flow=auth_code_flow, auth_response=auth_response
        )
        self.save_token(user_id, token["access_token"])

    def set_provider_headers(self, method, **kwargs):
        if method == "get":
            kwargs.setdefault("allow_redirects", True)
        elif method in ["post", "put", "patch"]:
            kwargs["headers"]["Content-type"] = "application/json"
        return kwargs


async def main():
    client = MicrosoftAsyncOauthClient()
    client.authenticate()
    await client.close_session()


if __name__ == "__main__":
    from async_oauth import AsyncOauthClient

    asyncio.run(main())
