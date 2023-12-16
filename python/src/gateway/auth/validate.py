import os
import requests

def token(request):
    """
    Validate token. This is a docstring.
    """
    # correct header information?
    if not "Authorization" in request.headers:
        return None, ("Missing credentials", 401)

    auth_token = request.headers["Authorization"]
    if not auth_token:
        return None, ("Missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": auth_token},
        timeout=20,
    )

    if response.status_code == 200:
        return response.text, None

    return None, (response.text, response.status_code)
