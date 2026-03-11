import configparser
import login.server as server
import asyncio # So we can loop

config_parser = configparser.ConfigParser()
config_parser.read('config.cfg')
token_limits_enabled = bool(config_parser.get('TOKEN_LIMIT', 'enable').strip('"'))
max_tokens = int(config_parser.get('TOKEN_LIMIT', 'max_tokens').strip('"'))

def init_users():
    user_ids = server.listUserIds()
    for user_id in user_ids:
        if server.getUserTokenCount(user_id) is None:
            # If there are any cases, put them here, like VIP users with more tokens, etc.
            server.setUserTokenCount(user_id, max_tokens)

def reset_daily_tokens():
    if token_limits_enabled:
        user_ids = server.listUserIds()
        for user_id in user_ids:
            # Also put a case for VIP users here, if they have daily tokens instead of a static token count
            server.setUserTokenCount(user_id, max_tokens)

def add_tokens(user_id: str, tokens: int) -> None:
    if token_limits_enabled:
        current_tokens = server.getUserTokenCount(user_id)
        if current_tokens is not None:
            server.setUserTokenCount(user_id, current_tokens + tokens)

