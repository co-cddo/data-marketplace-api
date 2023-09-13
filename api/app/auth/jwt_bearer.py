from typing import Annotated, List

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app import utils
from app import model as m
from app.db import user as user_db
from .utils import decodeJWT, ops_user


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
    return m.RegisteredUser.model_validate(local_user)


# Return either a user, general public memer, or ops user
async def any_type_of_user(
    is_ops: Annotated[bool, Depends(ops_user)],
    jwt: Annotated[JWTBearer(auto_error=False), Depends()] = None,
):
    if is_ops:
        return m.AnyUser.model_validate({"permission": [m.userPermisison.ops_admin]})
    if jwt:
        user_id = utils.user_id_from_email(jwt.get("email", None))
        local_user = user_db.get_by_id(user_id)
        if local_user:
            return m.RegisteredUser.model_validate(local_user)
        else:
            raise HTTPException(401, "Invalid JWT")
    else:
        return m.AnyUser.model_validate({"permission": []})
