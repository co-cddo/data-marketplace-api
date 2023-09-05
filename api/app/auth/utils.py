import requests
import jwt
import json

from fastapi import Header

from app import config


async def ops_user(x_api_key: str = Header(None)):
    if not x_api_key:
        return False
    return x_api_key == config.OPS_API_KEY


def decodeJWT(token: str):
    try:
        # Extract the JWT's header and payload
        header = jwt.get_unverified_header(token)

        # Find the appropriate key from JWKS based on the key ID (kid) in JWT header
        key_id = header["kid"]
        jwks_data = requests.get(config.JWKS_URL).json()
        keys = jwks_data["keys"]
        matching_keys = [key for key in keys if key["kid"] == key_id]

        assert len(matching_keys) == 1

        secret = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matching_keys[0]))
        decoded = jwt.decode(
            token,
            key=secret,
            audience=config.JWT_AUD,
            algorithms=["RS256"],
            leeway=5,
        )
        return decoded
    except Exception as err:
        print(err)
        return None
