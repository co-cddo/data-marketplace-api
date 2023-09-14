import datetime

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException

from app import utils
from app import model as m
from app.db import share as share_db
from app.auth.jwt_bearer import authenticated_user

router = APIRouter(prefix="/manage-shares", tags=["data share"])


def enrich_share_request(r: dict, org: m.Organisation = None) -> dict:
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
    publisherSlug = r.get("assetPublisher", None) or org.slug
    publisher = utils.lookup_organisation(publisherSlug)
    r["assetPublisher"] = publisher

    requestingOrg = utils.lookup_organisation(r["requestingOrg"])
    r["requestingOrg"] = requestingOrg.title
    r["neededBy"] = neededBy
    r["sharedata"] = sharedata
    return r


@router.get("/received-requests")
async def received_requests(
    user: Annotated[m.RegisteredUser, Depends(authenticated_user)]
) -> List[m.ShareRequest]:
    org = user.org
    if not org:
        return []
    share_requests = share_db.received_requests(org.slug)
    result = [
        m.ShareRequest.model_validate(enrich_share_request(r, org))
        for r in share_requests
    ]
    return result


@router.get("/received-requests/{request_id}")
async def received_request(
    request_id: str, user: Annotated[m.RegisteredUser, Depends(authenticated_user)]
) -> m.ShareRequest | m.ShareRequestWithExtras:
    share_request = share_db.received_request(request_id)
    if not share_request:
        raise HTTPException(404, f"Request {request_id} not found.")

    share_request["requestId"] = request_id
    share_request = enrich_share_request(share_request)

    # If the logged-in user is the requester don't return the notes
    if user.email == share_request["requesterEmail"]:
        return m.ShareRequest.model_validate(share_request)

    # If user's org is the same as the publisher org, return the share request with the notes field
    if share_request["assetPublisher"].slug == user.org.slug:
        return m.ShareRequestWithExtras.model_validate(share_request)

    raise HTTPException(403, "You are not authorised to see this request")


@router.put("/received-requests/{request_id}/review")
async def review_request(
    request_id: str,
    body: m.ReviewRequest,
    user: Annotated[m.RegisteredUser, Depends(authenticated_user)],
) -> m.SPARQLUpdate:
    share_request = share_db.received_request(request_id)
    if not share_request:
        raise HTTPException(404, f"Request {request_id} not found.")

    share_request["requestId"] = request_id
    share_request = enrich_share_request(share_request)

    if share_request["assetPublisher"].slug != user.org.slug:
        raise HTTPException(403, "You are not authorised to review this request")

    result = share_db.upsert_request_notes(request_id, body.notes)

    return m.SPARQLUpdate.model_validate(result)


@router.put("/received-requests/{request_id}/decision")
async def request_decision(
    request_id: str,
    body: m.DecisionRequest,
    user: Annotated[m.RegisteredUser, Depends(authenticated_user)],
) -> m.SPARQLUpdate:
    share_request = share_db.received_request(request_id)
    if not share_request:
        raise HTTPException(404, f"Request {request_id} not found.")

    share_request["requestId"] = request_id
    share_request = enrich_share_request(share_request)

    if share_request["assetPublisher"].slug != user.org.slug:
        raise HTTPException(403, "You are not authorised to review this request")

    print

    result = share_db.upsert_decision(
        request_id, status=body.status, decisionNotes=body.decisionNotes
    )
    return m.SPARQLUpdate.model_validate(result)
