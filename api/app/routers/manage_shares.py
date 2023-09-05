import json
import datetime

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException

from app import utils
from app import model as m
from app.db import user as user_db
from app.db import share as share_db
from app.auth.jwt_bearer import JWTBearer, authenticated_user
from app.auth.utils import ops_user

router = APIRouter(prefix="/manage-shares")


def enrich_share_request(r) -> m.ShareRequest:
    sharedata = m.ShareData.model_validate_json(r["sharedata"])
    neededBy = sharedata.steps["date"].value
    if not (neededBy["day"] and neededBy["month"] and neededBy["year"]):
        neededBy = "UNREQUESTED"
    else:
        neededBy = datetime.date(
            year=int(neededBy["year"]),
            month=int(neededBy["month"]),
            day=int(neededBy["day"]),
        )
    r["neededBy"] = neededBy
    r["sharedata"] = sharedata
    return m.ShareRequest.model_validate(r)


@router.get("/received-requests")
async def received_requests(
    user: Annotated[m.User, Depends(authenticated_user)]
) -> List[m.ShareRequest]:
    org = user.get("org", None)
    if not org:
        return []

    result = [enrich_share_request(r) for r in share_db.received_requests(org)]
    return result


@router.get("/received-requests/{request_id}")
async def received_request(
    request_id: str, user: Annotated[m.User, Depends(authenticated_user)]
) -> m.ShareRequest:
    share_request = share_db.received_request(request_id)
    share_request["requestId"] = request_id

    if share_request["requestingOrg"] != user.get("org", None):
        raise HTTPException(403, "You are not authorised to see this request")

    return enrich_share_request(share_request)
