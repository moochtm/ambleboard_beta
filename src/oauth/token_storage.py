"""
handles retrieving and storing tokens
"""
import os
import pathlib
from json import load, dump, JSONDecodeError

# GET PATH TO THIS FILE
PATH_TO_THIS_FILE = pathlib.Path(__file__).parent

PATH_TO_TOKENS = PATH_TO_THIS_FILE / "tokens"
if not PATH_TO_TOKENS.exists():
    os.mkdir(PATH_TO_TOKENS)


def __get_token_path(provider, user_id):
    return PATH_TO_TOKENS / f"{provider}_{user_id}.token"


def token_exists(provider, user_id):
    return __get_token_path(provider, user_id).exists()


def save_token(provider, user_id, token):
    with __get_token_path(provider, user_id).open("w") as stream:
        dump(token, stream)


def load_token(provider, user_id):
    try:
        with __get_token_path(provider, user_id).open("r") as stream:
            token = load(stream)
    except (JSONDecodeError, IOError):
        return None
    return token


def delete_token(provider, user_id):
    os.remove(__get_token_path(provider, user_id))
