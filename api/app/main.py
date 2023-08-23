from uuid import UUID
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
    return [m.Organisation.parse_obj(o) for o in m.organisations.values()]


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
        asset = m.Dataset.model_validate(asset)
    elif asset["type"] == "DataService":
        asset = m.DataService.model_validate(asset)
    else:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"asset": asset}


@app.put("/user")
async def upsert_user(jwt: m.JWT):
    decoded_jwt = utils.decodeJWT(jwt.token)
    user_email = decoded_jwt.get("email", None)
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorised")

    user_id = utils.user_id_from_email(user_email)

    local_user = db.get_user_by_id(user_id)

    if len(local_user) == 0:
        db.new_user(user_id, user_email)
        return {"user_id": user_id, "request_forms": {}}

    share_request_forms = db.get_share_request_forms(user_id)
    return {"user_id": user_id, "request_forms": share_request_forms}


@app.put("/formdata")
async def upsert_form_data(req: m.FormDataRequest):
    decoded_jwt = utils.decodeJWT(req.jwt)
    user_id = utils.user_id_from_email(decoded_jwt.get("email"))
    res = db.upsert_formdata(user_id, req.formdata)
    return res
