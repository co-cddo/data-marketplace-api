from datetime import datetime
import hashlib
import json

import jwt
import requests

from . import model as m
from . import config

MVP_ORGS = [
    "attorney-generals-office",
    "cabinet-office",
    "competition-and-markets-authority",
    "crown-prosecution-service",
    "department-for-business-and-trade",
    "department-for-culture-media-and-sport",
    "department-for-education",
    "department-for-energy-security-and-net-zero",
    "department-for-environment-food-rural-affairs",
    "department-for-levelling-up-housing-and-communities",
    "department-for-science-innovation-and-technology",
    "department-for-transport",
    "department-for-work-pensions",
    "department-of-health-and-social-care",
    "food-standards-agency",
    "foreign-commonwealth-development-office",
    "forestry-commission",
    "government-actuarys-department",
    "government-legal-department",
    "land-registry",
    "hm-revenue-customs",
    "hm-treasury",
    "home-office",
    "ministry-of-defence",
    "ministry-of-justice",
    "national-crime-agency",
    "northern-ireland-office",
    "ns-i",
    "office-of-rail-and-road",
    "office-of-the-advocate-general-for-scotland",
    "the-office-of-the-leader-of-the-house-of-commons",
    "office-of-the-leader-of-the-house-of-lords",
    "office-of-the-secretary-of-state-for-scotland",
    "office-of-the-secretary-of-state-for-wales",
    "ofgem",
    "ofqual",
    "ofsted",
    "prime-ministers-office-10-downing-street",
    "serious-fraud-office",
    "supreme-court-of-the-united-kingdom",
    "charity-commission",
    "the-national-archives",
    "the-water-services-regulation-authority",
    "uk-export-finance",
    "uk-statistics-authority",
]


def initialise_organisations():
    def parse_orgs(org_results):
        return {
            o["details"]["slug"]: {
                "id": o["id"],
                "title": o["title"],
                "abbreviation": o["details"]["abbreviation"],
                "slug": o["details"]["slug"],
                "format": o["format"],
                "web_url": o["web_url"],
            }
            for o in org_results
        }

    response = requests.get("https://www.gov.uk/api/organisations").json()
    orgs = parse_orgs(response["results"])
    while response.get("next_page_url", None):
        response = requests.get(response["next_page_url"]).json()
        orgs = {**orgs, **parse_orgs(response["results"])}
    return orgs


orgs = initialise_organisations()


def lookup_organisation(org_id: m.organisationID) -> m.Organisation:
    try:
        org_data = orgs[org_id]
    except:
        raise ValueError("Organisation does not exist")
    return m.Organisation.model_validate(org_data)


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


def user_id_from_email(email):
    return hashlib.md5(email.encode("utf-8")).hexdigest()


def decodeJWT(token: str):
    try:
        # Extract the JWT's header and payload
        header = jwt.get_unverified_header(token)

        # Find the appropriate key from JWKS based on the key ID (kid) in JWT header
        key_id = header["kid"]
        jwks_data = requests.get(config.JWKS_URL).json()
        keys = jwks_data["keys"]
        matching_keys = [key for key in keys if key["kid"] == key_id]

        assert len(matching_keys) == 1

        secret = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matching_keys[0]))
        decoded = jwt.decode(
            token, key=secret, audience=config.JWT_AUD, algorithms=["RS256"]
        )
        return decoded
    except Exception as err:
        print(err)
        return {}
