from uuid import UUID
import json
from typing import Annotated, List, Union
from fastapi import FastAPI, Body, Query, HTTPException
from fastapi.responses import JSONResponse
from . import model as m
from . import db
from . import utils

app = FastAPI(title="CDDO Data Marketplace API", version="0.1.0")


# TODO: in order to find out what filters are available, we need
# and endpoint to return all of the available organisations, themes, and types.
# Something like this, except we'll need to figure out how themes work.
# May not need it for types seeing as we only have 2


@app.get("/organisations")
async def list_organisations() -> List[m.Organisation]:
    return sorted(
        [m.Organisation.model_validate(utils.orgs[o]) for o in utils.MVP_ORGS],
        key=lambda o: o.title,
    )


# TODO: add theme query param
@app.get("/catalogue")
def search_catalogue(
    query: str = "",
    topic: Annotated[List[str], Query()] = [],
    organisation: Annotated[List[m.organisationID], Query()] = [],
    assetType: Annotated[List[m.assetType], Query()] = [],
    limit: int = 100,
    offset: int = 0,
) -> m.SearchAssetsResponse:
    assets = db.search(query)
    facets = {"topics": [], "organisations": [], "assetTypes": []}

    response = {"data": assets, "facets": facets}

    r = m.SearchAssetsResponse.model_validate(response)
    return r


@app.get("/catalogue/{asset_id}")
async def catalogue_entry_detail(asset_id: UUID) -> m.AssetDetailResponse:
    asset = db.asset_detail(asset_id)
    if asset["type"] == "Dataset":
        asset = m.DatasetResponse.model_validate(asset)
    elif asset["type"] == "DataService":
        asset = m.DataServiceResponse.model_validate(asset)
    else:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"asset": asset}
