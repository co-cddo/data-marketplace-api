from app import model as m
from typing import List
from app.db.utils import lookup_organisation
from app import utils
from datetime import datetime
import uuid


def _add_organisations(asset):
    creator = lookup_organisation(asset["creatorID"])
    org = lookup_organisation(asset["organisationID"])
    asset = utils.remove_keys(asset, ["creatorID", "organisationID"])
    asset["creator"] = creator
    asset["organisation"] = org
    return asset


def _create_asset(asset):
    asset = _add_organisations(asset)
    asset["catalogueCreated"] = datetime.now()
    asset["catalogueModified"] = datetime.now()
    asset["identifier"] = uuid.uuid4()
    return asset


def create_assets(assets: List[m.CreateDatasetBody | m.CreateDataServiceBody]):
    return {"errors": [], "data": [_create_asset(a) for a in assets]}
