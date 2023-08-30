import json
from app.db.sparql import shares_db
from datetime import datetime


def get_request_forms(user_id: str):
    query_results = shares_db.run_query("get_share_request_forms", user_id=user_id)
    forms = {r["assetId"]: r["sharedata"] for r in query_results}
    return forms


def upsert_sharedata(user_id: str, form_str: str):
    form_dict = json.loads(form_str)
    query_results = shares_db.run_update(
        "update_share_request_form",
        id=form_dict["requestId"],
        user_id=user_id,
        asset_id=form_dict["dataAsset"],
        sharedata=form_str,
        current_time=datetime.now().isoformat(),
        status=form_dict["status"],
    )
    return query_results
