import json
from app.db.sparql import shares_db
from app import model as m
from datetime import datetime


def get_request_forms(user_id: str):
    query_results = shares_db.run_query("get_share_request_forms", user_id=user_id)
    forms = {r["assetId"]: json.loads(r["sharedata"]) for r in query_results}
    return forms


def upsert_sharedata(user_id: str, sharedata: m.ShareData):
    shares_db.run_update("delete_share_request_data", id=sharedata.requestId)
    sharedata_string = json.dumps(sharedata.model_dump_json())
    query_results = shares_db.run_update(
        "create_share_request_data",
        id=sharedata.requestId,
        user_id=user_id,
        asset_id=sharedata.dataAsset,
        sharedata=sharedata_string,
        current_time=datetime.now().isoformat(),
        status=sharedata.status,
    )
    return query_results
