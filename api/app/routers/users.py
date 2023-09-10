from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException

from app import utils
from app import model as m
from app.db import user as user_db
from app.auth.jwt_bearer import JWTBearer, authenticated_user
from app.auth.utils import ops_user

router = APIRouter(prefix="/users")


@router.get("")
async def list_users(is_ops: Annotated[bool, Depends(ops_user)]) -> List[m.User]:
    if not is_ops:
        raise HTTPException(status_code=401, detail="Unauthorised")
    result = user_db.list_users()
    return [m.User.model_validate(u) for u in result]


@router.get("/me")
async def show_self(user: Annotated[m.User, Depends(authenticated_user)]) -> m.User:
    return user_db.get_by_id(user.id)


@router.put("/complete-profile")
async def complete_profile(
    user: Annotated[m.User, Depends(authenticated_user)],
    profile: m.CompleteProfileRequest,
) -> m.User:
    if user.org:
        raise HTTPException(400, "Organisation already set")

    if profile.org not in utils.orgs.keys():
        raise HTTPException(
            status_code=400, detail=f"Invalid organisation: {profile.org}"
        )

    user_db.complete_profile(user.id, profile.org, profile.role)

    return user_db.get_by_id(user.id)


@router.get("/{user_id}")
async def show_user(
    user_id: str,
    is_ops: Annotated[bool, Depends(ops_user)],
    jwt: Annotated[JWTBearer(auto_error=False), Depends()] = None,
):
    # If an email address has been provided, turn it into an ID
    if "@" in user_id:
        user_id = utils.user_id_from_email(user_id)

    # If you've passed the OPS_KEY, return the user
    if is_ops:
        return user_db.get_by_id(user_id)

    # If you're not OPS, you need to have sent a JWT and can only see yourself
    if jwt is not None:
        authed_user_id = utils.user_id_from_email(jwt.get("email"))
        if authed_user_id == user_id:
            return user_db.get_by_id(authed_user_id)

    raise HTTPException(401, "Unauthorised")


@router.put("/{user_id}/org")
async def edit_user_org(
    is_ops: Annotated[bool, Depends(ops_user)], user_id: str, req: m.EditUserOrgRequest
) -> m.SPARQLUpdate:
    if not is_ops:
        raise HTTPException(status_code=401, detail="Unauthorised")

    # If an email address has been provided, turn it into an ID
    if "@" in user_id:
        user_id = utils.user_id_from_email(user_id)

    user = user_db.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"Invalid user id: {user_id}")

    if req.org not in utils.orgs.keys():
        raise HTTPException(status_code=400, detail=f"Invalid organisation: {req.org}")

    return m.SPARQLUpdate.model_validate(user_db.edit_org(user_id, req.org))
