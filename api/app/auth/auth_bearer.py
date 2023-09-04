import requests
import jwt
import json

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app import config


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


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            decoded_jwt = decodeJWT(credentials.credentials)
            if not decoded_jwt:
                raise HTTPException(status_code=401, detail="Invalid or expired token.")
            return decoded_jwt
        else:
            raise HTTPException(status_code=401, detail="Unauthorised")
