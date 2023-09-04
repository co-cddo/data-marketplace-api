from uuid import UUID
from typing import Annotated, List, Union, Optional
from fastapi import (
    FastAPI,
    Body,
    Query,
    HTTPException,
    File,
    UploadFile,
    Header,
    Depends,
)
from fastapi.responses import JSONResponse
from app import model as m
from app import config
from app.db import asset as asset_db, user as user_db, share as share_db
from app.publish import csv as pubcsv, response as pubres
from app.auth.auth_bearer import JWTBearer
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


async def ops_user(x_api_key: str = Header(None)):
    if not x_api_key:
        return False
    return x_api_key == config.OPS_API_KEY


@app.get("/users")
async def list_users(is_ops: Annotated[bool, Depends(ops_user)]):
    if not is_ops:
        raise HTTPException(status_code=401, detail="Unauthorised")
    return user_db.list_users()


@app.put("/users/{user_id}/org")
async def edit_user_org(
    is_ops: Annotated[bool, Depends(ops_user)], user_id: str, req: m.EditUserOrgRequest
):
    if not is_ops:
        raise HTTPException(status_code=401, detail="Unauthorised")

    if "@" in user_id:
        user_id = utils.user_id_from_email(user_id)

    user = user_db.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=400, detail=f"Invalid user id: {user_id}")

    if req.org not in utils.orgs.keys():
        raise HTTPException(status_code=400, detail=f"Invalid organisation: {req.org}")

    return user_db.edit_org(user_id, req.org)


@app.get("/managed-shared/received-requests")
async def received_requests(jwt: Annotated[JWTBearer(), Depends()]):
    user_email = jwt.get("email", None)
    user_id = utils.user_id_from_email(user_email)
    local_user = user_db.get_by_id(user_id)
    if not local_user:
        raise HTTPException(400, "Invalid user")
    return


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
    assets = asset_db.search(query)
    facets = {"topics": [], "organisations": [], "assetTypes": []}

    response = {"data": assets, "facets": facets}

    r = m.SearchAssetsResponse.model_validate(response)
    return r


@app.get("/catalogue/{asset_id}")
async def catalogue_entry_detail(asset_id: UUID) -> m.AssetDetailResponse:
    asset = asset_db.detail(asset_id)
    if asset["type"] == m.assetType.dataset:
        asset = m.DatasetResponse.model_validate(asset)
    elif asset["type"] == m.assetType.service:
        asset = m.DataServiceResponse.model_validate(asset)
    else:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"asset": asset}


@app.get("/login")
async def login(jwt: Annotated[JWTBearer(), Depends()]):
    user_email = jwt.get("email", None)
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorised")

    user_id = utils.user_id_from_email(user_email)

    local_user = user_db.get_by_id(user_id)

    if not local_user:
        user_db.new_user(user_id, user_email)
        return {"user_id": user_id, "sharedata": {}}

    share_request_forms = share_db.get_request_forms(user_id)
    return {"user_id": user_id, "sharedata": share_request_forms}


@app.put("/sharedata")
async def upsert_sharedata(
    jwt: Annotated[JWTBearer(), Depends()], req: m.UpsertShareDataRequest
):
    user_id = utils.user_id_from_email(jwt.get("email"))
    res = share_db.upsert_sharedata(user_id, req.sharedata)
    return res


@app.post("/publish")
async def publish_assets(
    body: pubres.CreateAssetsRequestBody,
) -> pubres.CreateAssetsResponseBody:
    return


# multipart/form-data endpoint
# curl -F "datasets=@dataset.csv" -F "dataservices=@dataservice.csv" localhost:8000/publish/verify
@app.post("/publish/verify")
async def prepare_batch_publish_request(
    datasets: Annotated[
        UploadFile,
        File(description="The Dataset tab from the spreadsheet template in CSV format"),
    ],
    dataservices: Annotated[
        UploadFile,
        File(
            description="The DataService tab from the spreadsheet template in CSV format"
        ),
    ],
) -> pubres.ParseFilesResponseBody:
    parsed = pubcsv.parse_input_files(
        datasets_file=datasets.file, services_file=dataservices.file
    )
    response = pubres.format_response(parsed)
    if response.ok:
        return response
    # Annoyingly, the API specification for 422 response is hard-coded in openAPI so we can't override it
    # here with the response specification. Maybe we can return 400 and include a flag for success/error state
    else:
        return JSONResponse(status_code=422, content=response)
