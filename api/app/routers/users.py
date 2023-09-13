from typing import Annotated, List, Literal
from fastapi import APIRouter, Depends, HTTPException, Path
from app import utils
from app import model as m
from app.db import user as user_db, asset as asset_db
from app.auth.jwt_bearer import JWTBearer, authenticated_user, any_type_of_user
from app.auth.utils import ops_user
from app.auth import access_control

router = APIRouter(prefix="/users", tags=["user"])


@router.get("")
async def list_users(
    is_ops: Annotated[bool, Depends(ops_user)]
) -> List[m.RegisteredUser]:
    if not is_ops:
        raise HTTPException(status_code=401, detail="Unauthorised")
    users = user_db.list_users()
    return users


@router.get("/me", summary="Show the currently logged-in user")
async def show_self(
    user: Annotated[m.RegisteredUser, Depends(authenticated_user)]
) -> m.RegisteredUser:
    return user_db.get_by_id(user.id)


@router.get(
    "/permission/{target_type}/{target_id}/{action}",
    summary="Check if the current user has permission to execute a given action on the given entity",
)
async def check_permission(
    user: Annotated[m.AnyUser, Depends(any_type_of_user)],
    target_type: Annotated[
        Literal["asset", "organisation"],
        Path(title="The type of entity that the permission relates to"),
    ],
    target_id: Annotated[
        str,
        Path(
            title="The ID of the asset or organisation that the permission relates to"
        ),
    ],
    action: Annotated[
        access_control.assetAction | access_control.organisationAction,
        Path(title="The action that you are looking for permission to do"),
    ],
) -> bool:
    user_perms = access_control.UserWithAccessRights(user)
    match target_type:
        case "asset":
            if not isinstance(action, access_control.assetAction):
                raise HTTPException(
                    status_code=400, detail=f"Invalid action for asset: {action}"
                )
            try:
                asset = asset_db.detail(target_id)
            except:
                raise HTTPException(
                    status_code=404, detail=f"Asset not found for ID {target_id}"
                )
            asset = (
                m.DatasetResponse.model_validate(asset)
                if asset["type"] == m.assetType.dataset
                else m.DataServiceResponse.model_validate(asset)
            )
            return user_perms.has_asset_permission(action, asset)
        case "organisation":
            if not isinstance(action, access_control.organisationAction):
                raise HTTPException(
                    status_code=400, detail=f"Invalid action for organisation: {action}"
                )
            try:
                organisation = utils.lookup_organisation(target_id)
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
            return user_perms.has_org_permission(action, organisation)


@router.put(
    "/complete-profile", summary="Add organisation and job title for the current user"
)
async def complete_profile(
    user: Annotated[m.RegisteredUser, Depends(authenticated_user)],
    profile: m.CompleteProfileRequest,
) -> m.RegisteredUser:
    if user.org:
        raise HTTPException(400, "Organisation already set")

    if profile.organisation not in utils.orgs.keys():
        raise HTTPException(
            status_code=400, detail=f"Invalid organisation: {profile.organisation}"
        )

    user_db.complete_profile(user.id, profile.organisation, profile.jobTitle)

    return user_db.get_by_id(user.id)


@router.get("/{user_id}")
async def show_user(
    user_id: str,
    is_ops: Annotated[bool, Depends(ops_user)],
    jwt: Annotated[JWTBearer(auto_error=False), Depends()] = None,
) -> m.RegisteredUser:
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


@router.delete("/{user_id}")
async def delete_user(
    user_id: str, is_ops: Annotated[bool, Depends(ops_user)]
) -> m.SPARQLUpdate:
    if not is_ops:
        raise HTTPException(401, "Unauthorised")

    # If an email address has been provided, turn it into an ID
    if "@" in user_id:
        user_id = utils.user_id_from_email(user_id)

    return user_db.delete_by_id(user_id)


@router.put(
    "/{user_id}/org",
    summary="Edit a users organisation as ops admin (for development and debug use only)",
)
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


@router.put("/{user_id}/permissions", summary="Add or remove permissions from a user")
async def edit_user_permissions(
    is_ops: Annotated[bool, Depends(ops_user)],
    user_id: str,
    req: m.EditUserPermissionRequest,
):
    # If an email address has been provided, turn it into an ID
    if "@" in user_id:
        user_id = utils.user_id_from_email(user_id)

    user = user_db.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"Invalid user id: {user_id}")
    return m.SPARQLUpdate.model_validate(
        user_db.edit_permissions(user_id, req.add, req.remove)
    )
