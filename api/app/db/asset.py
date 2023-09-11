from typing import List
from app.db.sparql import assets_db
from app.db import utils as dbutils
from app import utils
from app import model as m


def _resolve_media_type_label(db_result_dict):
    if "mediaTypeLabel" in db_result_dict:
        db_result_dict["mediaType"] = db_result_dict["mediaTypeLabel"]
        db_result_dict.pop("mediaTypeLabel")


def _construct_OR_terms(property: str, vals: List[str]):
    if len(vals) == 0:
        return None
    terms = " || ".join([f'STR({property}) = "{v}"' for v in vals])
    return f"({terms})"


def _construct_AND_terms(terms: List[str]):
    terms = [t for t in terms if t]  # Remove Nones
    terms = " && ".join(terms)
    return f"({terms})"


def _construct_filter(*filter_groups):
    """A filter_group is a set of filters to apply to a particular property.
    It has this shape: ["?theme", ["Mapping", "Defence"]]
    We need to use an OR for values in the same filter group and
    an AND between different filter groups."""
    if len(filter_groups) == 0:
        return ""
    if all(len(v) == 0 for _, v in filter_groups):
        return ""
    or_terms = [_construct_OR_terms(p, v) for p, v in filter_groups]
    anded_terms = _construct_AND_terms(or_terms)
    return f"FILTER ({anded_terms})"


def search(q: str = "", organisations: List[str] = [], themes: List[str] = []):
    if q == "":
        q = "*"
    else:
        q = f"{q}*"

    # TODO What else do we need to do to sanitise the query string?
    q = utils.sanitise_search_query(q)

    filters = _construct_filter(["?organisation", organisations], ["?theme", themes])

    query_results = assets_db.run_query("asset_search", q=q, filters=filters)
    for r in query_results:
        _resolve_media_type_label(r)
    result_dicts = dbutils.aggregate_query_results_by_key(
        query_results, group_key="resourceUri"
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
        distributions = _fetch_distribution_details(asset["distribution"])
        asset["distributions"] = [
            m.DistributionResponse.model_validate(d) for d in distributions
        ]
    return asset
