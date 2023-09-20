from itertools import groupby
from app.utils import lookup_organisation


def aggregate_results(result_dicts):
    """Assuming all results relate to a single item, aggregate them to include a list of values for
    any key with multiple values"""
    match len(result_dicts):
        case 0:
            return {}
        case 1:
            return result_dicts[0]
        case _:
            out = {}
            for r in result_dicts:
                for k, v in r.items():
                    if k not in out:
                        out[k] = v
                    elif out[k] != v:
                        if not isinstance(out[k], set):
                            out[k] = {out[k]}
                        out[k].add(v)
            return out


def aggregate_query_results_by_key(results, group_key="resourceUri"):
    """Groups the result by given key and aggregates the groups into a single dictionary for each"""
    return [
        aggregate_results(list(results_for_resource))
        for _, results_for_resource in groupby(results, lambda r: r[group_key])
    ]


def _convert_multival_fields_to_lists(asset_result_dict):
    for k in [
        "keyword",
        "alternativeTitle",
        "relatedAssets",
        "theme",
        "servesDataset",
        "distribution",
        "mediaType",
        "creator",
    ]:
        current_val = asset_result_dict.get(k)
        if current_val is None:
            pass
        elif isinstance(current_val, set):
            asset_result_dict[k] = sorted(list(current_val))
        else:
            asset_result_dict[k] = [current_val]


def enrich_query_result_dict(asset_result_dict):
    enriched = {k: v for k, v in asset_result_dict.items()}
    _convert_multival_fields_to_lists(enriched)
    if "organisation" in enriched:
        enriched["organisation"] = lookup_organisation(enriched["organisation"])
    if "creator" in enriched:
        enriched["creator"] = [lookup_organisation(o) for o in enriched["creator"]]
    return enriched


def munge_asset_summary_response(result_dict):
    r = result_dict.copy()
    # If summary doesn't exist, set it to be a truncated description
    if "summary" not in r:
        r["summary"] = r["description"][:100]
    del r["description"]

    return r


def enrich_user_org(user):
    u = user.copy()
    org = u.get("org", None)
    if org:
        u["org"] = lookup_organisation(org)
    return u


def wrap_markdown(markdown_str):
    content = markdown_str.replace("\\", "\\\\").replace('"', '\\"')
    return "\\n".join(l for l in content.splitlines() if l)


def unwrap_markdown(description):
    if isinstance(description, str):
        return description.replace('\\"', '"').replace("\\\\", "\\")
    return description
