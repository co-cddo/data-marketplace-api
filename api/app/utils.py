from datetime import datetime

from . import model as m

organisations = {
    "department-for-work-pensions": {
        "id": "department-for-work-pensions",
        "title": "Department for Work & Pensions",
        "acronym": "DWP",
        "homepage": "https://www.gov.uk/government/organisations/department-for-work-pensions",
    },
    "food-standards-agency": {
        "id": "food-standards-agency",
        "title": "Food Standards Agency",
        "acronym": "FSA",
        "homepage": "https://www.food.gov.uk/",
    },
    "nhs-digital": {
        "id": "nhs-digital",
        "title": "NHS Digital",
        "acronym": "NHS Digital",
        "homepage": "https://digital.nhs.uk/",
    },
    "ordnance-survey": {
        "id": "ordnance-survey",
        "title": "Ordnance Survey",
        "acronym": "OS",
        "homepage": "https://www.gov.uk/government/organisations/ordnance-survey",
    },
}


def lookup_organisation(org_id: m.organisationID) -> m.Organisation:
    try:
        org_data = organisations[org_id]
    except:
        raise ValueError("Organisation does not exist")
    return m.Organisation.model_validate(org_data)

def _convert_multival_fields_to_lists(asset_result_dict):
    for k in ["creator",
              "keyword",
              "alternativeTitle",
              "relatedResource",
              "theme",
              "servesData",
              "distribution",
              "mediaType"]:
        current_val = asset_result_dict.get(k)
        if current_val is None:
            pass
        elif isinstance(current_val, set):
            asset_result_dict[k] = sorted(list(current_val))
        else:
            asset_result_dict[k] = [current_val]

def enrich_query_result_dict(asset_result_dict):
    enriched = {k: v for k, v in asset_result_dict.items() if k != "resourceUri"}
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


def sanitise_search_query(q: str):
    return q.strip('"')

def select_keys(d: dict, keys: list):
    """Similar to select-keys in Clojure.
    Returns a new dictionary only containing the specified keys"""
    return {k: d[k] for k in keys}

def remove_keys(d: dict, keys: list):
    """Similar to remove-keys in Clojure.
    Returns a new dictionary with the specified keys removed"""
    return {k: d[k] for k in d.keys() if k not in keys}
