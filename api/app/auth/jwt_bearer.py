from typing import Annotated, List

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app import utils
from app import model as m
from app.db import user as user_db
from .utils import decodeJWT


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            decoded_jwt = decodeJWT(credentials.credentials)
            if not decoded_jwt:
                if self.auto_error:
                    raise HTTPException(
                        status_code=401, detail="Invalid or expired token."
                    )
                else:
                    return None
            return decoded_jwt
        else:
            if self.auto_error:
                raise HTTPException(status_code=401, detail="Unauthorised")
            else:
                return None


async def authenticated_user(jwt: Annotated[JWTBearer(), Depends()]):
    user_id = utils.user_id_from_email(jwt.get("email", None))
    local_user = user_db.get_by_id(user_id)
    if not local_user:
        raise HTTPException(401, "Invalid JWT")
    return m.User.model_validate(local_user)
