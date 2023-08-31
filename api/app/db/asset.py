from app.db.sparql import assets_db
from app.db import utils as dbutils
from app import utils
from app import model as m


def _resolve_media_type_label(db_result_dict):
    if "mediaTypeLabel" in db_result_dict:
        db_result_dict["mediaType"] = db_result_dict["mediaTypeLabel"]
        db_result_dict.pop("mediaTypeLabel")


def search(q: str = ""):
    if q == "":
        q = "*"

    # TODO What else do we need to do to sanitise the query string?
    q = utils.sanitise_search_query(q)
    query_results = assets_db.run_query("asset_search", q=q)
    for r in query_results:
        _resolve_media_type_label(r)
    result_dicts = dbutils.aggregate_query_results_by_key(
        query_results, group_key="identifier"
    )
    result_dicts = [dbutils.enrich_query_result_dict(r) for r in result_dicts]
    result_dicts = [dbutils.munge_asset_summary_response(r) for r in result_dicts]

    return result_dicts


def _fetch_distribution_details(distribution_ids):
    distribution_ids = [f"<{i}>" for i in distribution_ids]
    results = assets_db.run_query("distribution_detail", distribution=distribution_ids)
    for r in results:
        _resolve_media_type_label(r)
    return dbutils.aggregate_query_results_by_key(results, group_key="distribution")


def detail(asset_id: str):
    query_results = assets_db.run_query("asset_detail", asset_id=asset_id)
    asset_result_dicts = dbutils.aggregate_query_results_by_key(
        query_results, group_key="resourceUri"
    )
    result_dicts = [dbutils.enrich_query_result_dict(r) for r in asset_result_dicts]
    assert len(result_dicts) == 1
    asset = result_dicts[0]

    asset["identifier"] = asset_id

    contactPoint = {
        "name": asset["contactName"],
        "email": asset["contactEmail"],
        "contactTelephone": asset.get("contentTelephone", None),
        "contactAddress": asset.get("contentAddress", None),
    }

    asset["contactPoint"] = m.ContactPoint.model_validate(contactPoint)

    if asset["type"] == m.assetType.dataset:
        distributions = [
            utils.remove_keys(r, ["distribution"])
            for r in _fetch_distribution_details(asset["distribution"])
        ]
        asset["distributions"] = [
            m.DistributionResponse.model_validate(d) for d in distributions
        ]
    return asset
