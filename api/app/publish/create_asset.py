from app import model as m
from app.db.model import asset_to_triples, triples_to_sparql
from app.db.sparql import assets_db
from typing import List
from app import utils
from datetime import datetime
import uuid


def _add_organisations(asset):
    creator = utils.lookup_organisation(asset["creatorID"])
    org = utils.lookup_organisation(asset["organisationID"])
    asset = utils.remove_keys(asset, ["creatorID", "organisationID"])
    asset["creator"] = dict(creator)
    asset["organisation"] = dict(org)
    return asset


def _add_uuid(asset_or_distribution):
    return {**asset_or_distribution, "identifier": uuid.uuid4()}


def _create_asset(asset):
    asset = _add_uuid(asset)
    asset["catalogueCreated"] = datetime.now()
    asset["catalogueModified"] = datetime.now()
    asset["identifier"] = uuid.uuid4()
    if asset["type"] == m.assetType.dataset:
        asset["distributions"] = [_add_uuid(d) for d in asset["distributions"]]
    return asset


# TODO actual errors
def create_assets(assets: List[m.CreateDatasetBody | m.CreateDataServiceBody]):
    assets = [_add_organisations(a) for a in assets]
    assets = [_create_asset(a) for a in assets]
    triples = []
    for a in assets:
        try:
            triples = triples + asset_to_triples(a)
        except Exception as e:
            print("ERROR with asset")
            print(e)
            return {"errors": [], "data": []}
    sparql = triples_to_sparql(triples)
    response = assets_db.run_update("create_asset", triples=sparql)
    return {"errors": [], "data": assets}
