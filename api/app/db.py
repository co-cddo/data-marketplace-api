from . import utils
from . import model as m
from . import sparql


def search(q: str = ""):
    if q == "":
        q = "*"

    # TODO What else do we need to do to sanitise the query string?
    q = utils.sanitise_search_query(q)
    query_results = sparql.run_query("asset_search.sparql", q=q)
    result_dicts = sparql.aggregate_query_results_by_key(query_results, group_key="identifier")
    result_dicts = [utils.enrich_query_result_dict(r) for r in result_dicts]
    result_dicts = [utils.munge_asset_summary_response(r) for r in result_dicts]

    return result_dicts


def fetch_distribution_details(distribution_ids):
    distribution_ids = [f"<{i}>" for i in distribution_ids]
    results = sparql.run_query("distribution_detail.sparql", distribution=distribution_ids)
    return sparql.aggregate_query_results_by_key(results, group_key="distribution")

def asset_detail(asset_id: str):
    query_results = sparql.run_query("asset_detail.sparql", asset_id=asset_id)
    asset_result_dicts = sparql.aggregate_query_results_by_key(query_results, group_key="resourceUri")
    result_dicts = [utils.enrich_query_result_dict(r) for r in asset_result_dicts]
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
        distributions = [utils.remove_keys(r, ["distribution"]) for r in
                         fetch_distribution_details(asset["distribution"])]
        asset["distributions"] = [m.DistributionSummary.model_validate(d)
                                  for d in distributions]
    return asset
