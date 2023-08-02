from uuid import UUID
import json
from typing import Annotated, List, Union
from fastapi import FastAPI, Body, Query, HTTPException
from fastapi.responses import JSONResponse
from . import model as m
from . import db

app = FastAPI(title="CDDO Data Marketplace API", version="0.1.0")


# TODO: in order to find out what filters are available, we need
# and endpoint to return all of the available organisations, themes, and types.
# Something like this, except we'll need to figure out how themes work.
# May not need it for types seeing as we only have 2


@app.get("/organisations")
async def list_organisations() -> List[m.Organisation]:
    return [m.Organisation.parse_obj(o) for o in m.organisations.values()]


# TODO: add theme query param
@app.get("/catalogue")
async def search_catalogue(
    query: str = "",
    topic: Annotated[List[str], Query()] = [],
    organisation: Annotated[List[m.organisationID], Query()] = [],
    assetType: Annotated[List[m.assetType], Query()] = [],
    limit: int = 100,
    offset: int = 0,
) -> list[m.SearchAssetsResponse]:
    data = db.search(query)
    facets = {"topics": [], "organisations": [], "assetTypes": []}

    response = {"data": data, "facets": facets}
    # print(json.dumps(response, indent=4))

    r = m.SearchAssetsResponse.model_validate(response)
    return r


@app.get("/catalogue/{asset_id}", response_model=Union[m.DataService, m.Dataset])
async def catalogue_entry_detail(asset_id: UUID):
    # Obviously, this would return the asset if it existed!
    raise HTTPException(status_code=404, detail="Item not found")