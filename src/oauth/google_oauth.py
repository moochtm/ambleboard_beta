from src.oauth.async_oauth import AsyncOauthClient
from requests_oauthlib import OAuth2Session
import asyncio

# OAuth endpoints given in the Google API documentation


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

    def authenticate(self, user_id=None):
        self.user_id = user_id or self.user_id
        if self.user_id:
            self.token = self.load_token(self.user_id)
            if self.token:
                return

        app = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
            auto_refresh_url=self.token_uri,
            auto_refresh_kwargs=self.extra,
        )
        authorization_url, _ = app.authorization_url(
            self.authorization_base_url, access_type="offline", prompt="select_account"
        )
        print(
            f"Please go here and sign in: {authorization_url}\n",
        )

        # Get the authorization verifier code from the callback url
        code = input("Paste the code string here:\n")
        user_id = input("Enter the email address you used when logging in:\n")

        token = app.fetch_token(
            self.token_uri, client_secret=self.client_secret, code=code
        )
        print(token)
        self.save_token(user_id, token["access_token"])

    def set_provider_headers(self, method, **kwargs):
        if method == "get":
            kwargs.setdefault("allow_redirects", True)
        elif method in ["post", "put", "patch"]:
            kwargs["headers"]["Content-type"] = "application/json"
        return kwargs


async def main():
    client = GoogleAsyncOauthClient()
    client.authenticate()
    await client.close_session()


if __name__ == "__main__":
    asyncio.run(main())
