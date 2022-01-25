from os import path
from instaloader import InvalidArgumentException, BadCredentialsException, ConnectionException, TwoFactorAuthRequiredException


def login_2fa(instaloader, username, code):
    # Only call this after login asked for
    # 2fa authentication
    try:
        instaloader.two_factor_login(code)
        instaloader.save_session_to_file(
            f"{path.dirname(path.dirname(__file__))}/sessions/{username}")
    except InvalidArgumentException as err:
        return [str(err), 400]
    except BadCredentialsException as err:
        return [str(err), 401]

    return True


def login_standard(instaloader, username, password):
    # Login and save a session to /sessions/your_session
    try:
        instaloader.login(username, password)
        instaloader.save_session_to_file(
            f"{path.dirname(path.dirname(__file__))}/sessions/{username}")
    except InvalidArgumentException as err:
        return [str(err), 404]
    except (BadCredentialsException, ConnectionException) as err:
        return [str(err), 401]
    except TwoFactorAuthRequiredException as err:
        return [str(err), 200]
