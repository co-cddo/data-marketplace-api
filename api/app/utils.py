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


def search_query_result_to_dict(result):
    d = {}
    for k, v in result.items():
        match k:
            case "catalogueCreated" | "catalogueModified" | "created" | "modified" | "issued":
                d[k] = datetime.fromisoformat(v["value"])
            case "organisation":
                d[k] = lookup_organisation(v["value"])
            case "creator":
                creators = v["value"]
                if not isinstance(creators, list):
                    creators = [creators]
                d[k] = [lookup_organisation(c) for c in creators]
            case "type":
                if v["value"].startswith("dcat:"):
                    d[k] = v["value"].replace("dcat:", "")
            case _:
                d[k] = v["value"]

    return d


def munge_asset_summary_response(result_dict):
    r = result_dict.copy()
    # If summary doesn't exist, set it to be a truncated description
    if "summary" not in r:
        r["summary"] = r["description"][:100]
    del r["description"]

    return r


def sanitise_search_query(q: str):
    return q.strip('"')


MEDIATYPES = {
    "text/csv": "CSV",
    "application/geopackage+sqlite3": "GeoPackage",
    "application/vnd.ms-excel": "XLS",
}


# TODO What happens if the media type isn't in the dict? We can't make nice names for all types...
def remap_media_type(t: str):
    return MEDIATYPES.get(t, t)
