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


def queryResultToDict(result):
    d = {}
    for k, v in result.items():
        if k in [
            "catalogueCreated",
            "catalogueModified",
            "created",
            "modified",
            "issued",
        ]:
            d[k] = datetime.fromisoformat(v["value"])
        elif k == "organisation":
            d[k] = lookup_organisation(v["value"])
        else:
            d[k] = v["value"]
    return d


def normaliseValues(result_dict):
    r = result_dict.copy()
    # Choose summary instead of description, if summary exists
    if "summary" in r:
        r["description"] = r["summary"]
        del r["summary"]
    else:
        r["description"] = r["description"][:100]

    return r
