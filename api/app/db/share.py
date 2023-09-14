import json
from app.db.sparql import shares_db
from app import model as m
from datetime import datetime


def get_request_forms(user_id: str):
    query_results = shares_db.run_query("get_for_user", user_id=user_id)
    forms = {r["assetId"]: json.loads(r["sharedata"]) for r in query_results}
    return forms


def upsert_sharedata(user_id: str, sharedata: m.ShareData):
    sharedata_string = json.dumps(sharedata.model_dump_json())
    query_results = shares_db.run_update(
        "upsert",
        id=sharedata.requestId,
        user_id=user_id,
        asset_id=sharedata.dataAsset,
        sharedata=sharedata_string,
        current_time=datetime.now().isoformat(),
        status=sharedata.status,
    )
    return query_results


def received_requests(org: str):
    results = shares_db.run_query("get_by_org", org=org)
    return results


def received_request(requestId: str):
    results = shares_db.run_query("get_by_id", requestId=requestId)

    assert len(results) <= 1, "Found multiple share requests with the same ID"
    if not results:
        return None

    return results[0]


def upsert_request_notes(request_id: str, notes: str):
    results = shares_db.run_update("upsert_notes", request_id=request_id, notes=notes)
    return results


def upsert_decision(request_id: str, status: m.ShareRequestStatus, decisionNotes: str):
    results = shares_db.run_update(
        "upsert_decision",
        request_id=request_id,
        status=status,
        decisionNotes=decisionNotes,
        decisionDate=datetime.now().date(),
    )
    return results
