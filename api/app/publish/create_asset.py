from app import model as m
from app.db.model import (
    asset_to_triples,
    triples_to_sparql,
    subject_uri,
    distribution_uri,
)
from app.db.sparql import assets_db
from typing import List
from app import utils
from datetime import datetime
import uuid
from app.publish.errors import errorScope


def _add_organisations(asset):
    creators = [
        dict(utils.lookup_organisation(creator_id)) for creator_id in asset["creatorID"]
    ]
    org = utils.lookup_organisation(asset["organisationID"])
    asset = utils.remove_keys(asset, ["creatorID", "organisationID"])
    asset["creator"] = creators
    asset["organisation"] = dict(org)
    return asset


def _add_uuid(asset_or_distribution):
    return {**asset_or_distribution, "identifier": uuid.uuid4()}


def _create_asset(asset):
    asset = _add_uuid(asset)
    asset["catalogueCreated"] = datetime.now()
    asset["catalogueModified"] = datetime.now()
    asset["identifier"] = uuid.uuid4()
    asset["resourceUri"] = subject_uri(asset)
    if asset["type"] == m.assetType.dataset:
        asset["distributions"] = [_add_uuid(d) for d in asset["distributions"]]
        for d in asset["distributions"]:
            d["distribution"] = distribution_uri(d)
    return asset


def create_assets(assets: List[m.CreateDatasetBody | m.CreateDataServiceBody]):
    assets = [_add_organisations(a) for a in assets]
    assets = [_create_asset(a) for a in assets]
    triples = []
    errors = []
    for a in assets:
        try:
            triples = triples + asset_to_triples(a)
        except Exception as e:
            errors.append(
                {
                    "message": "Can't store asset data",
                    "scope": errorScope.asset,
                    "location": a["externalIdentifier"]
                    if a["externalIdentifier"] is not None
                    else a["title"],
                    "extras": {"error": str(e)},
                }
            )
    if errors != []:
        return {"errors": errors, "data": []}
    try:
        sparql = triples_to_sparql(triples)
        response = assets_db.run_update("create_asset", triples=sparql)
        return {"errors": [], "data": assets}
    except Exception as e:
        return {
            "errors": [
                {
                    "message": "Failed to save data to database",
                    "scope": errorScope.batch,
                    "location": "unknown",
                    "extras": {"internal_error": str(e)},
                }
            ],
            "data": [],
        }
