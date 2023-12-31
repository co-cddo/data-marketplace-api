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

from app import utils
from app import model as m
from app.db import asset as asset_db, user as user_db, share as share_db
from app.publish import csv as pubcsv, response as pubres, create_asset as publish
from app.auth.jwt_bearer import JWTBearer, authenticated_user
from app.routers.users import router as users_router
from app.routers.manage_shares import router as shares_router

app = FastAPI(title="CDDO Data Marketplace API", version="0.1.0")

app.include_router(users_router)
app.include_router(shares_router)

# TODO: in order to find out what filters are available, we need
# and endpoint to return all of the available organisations, themes, and types.
# Something like this, except we'll need to figure out how themes work.
# May not need it for types seeing as we only have 2


@app.get("/organisations", tags=["metadata"])
async def list_organisations() -> List[m.Organisation]:
    return sorted(
        [m.Organisation.model_validate(utils.orgs[o]) for o in utils.MVP_ORGS],
        key=lambda o: o.title,
    )


# TODO: add theme query param
@app.get("/catalogue", tags=["data"])
def search_catalogue(
    query: str = "",
    topic: Annotated[List[str], Query()] = [],
    organisation: Annotated[List[str], Query()] = [],
    assetType: Annotated[List[m.assetType], Query()] = [],
    limit: int = 100,
    offset: int = 0,
) -> m.SearchAssetsResponse:
    assets = asset_db.search(query, organisations=organisation, themes=topic)
    facets = {"topics": [], "organisations": [], "assetTypes": []}

    response = {"data": assets, "facets": facets}

    r = m.SearchAssetsResponse.model_validate(response)
    return r


@app.get("/catalogue/{asset_id}", tags=["data"])
async def catalogue_entry_detail(asset_id: UUID) -> m.AssetDetailResponse:
    asset = asset_db.detail(asset_id)
    if asset["type"] == m.assetType.dataset:
        asset = m.DatasetResponse.model_validate(asset)
    elif asset["type"] == m.assetType.service:
        asset = m.DataServiceResponse.model_validate(asset)
    else:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"asset": asset}


@app.get("/login", tags=["user"])
async def login(jwt: Annotated[JWTBearer(), Depends()]):
    user_email = jwt.get("email", None)
    if not user_email:
        raise HTTPException(status_code=401, detail="Unauthorised")

    user_id = utils.user_id_from_email(user_email)

    local_user = user_db.get_by_id(user_id)

    if not local_user:
        new_user = user_db.new_user(user_id, user_email)
        return m.LoginResponse.model_validate(
            {"user": new_user, "new_user": True, "sharedata": {}}
        )

    share_request_forms = share_db.get_sharedata(user_id)
    return m.LoginResponse.model_validate(
        {"user": local_user, "new_user": False, "sharedata": share_request_forms}
    )


@app.put("/sharedata", tags=["data share"])
async def upsert_sharedata(
    jwt: Annotated[JWTBearer(), Depends()], req: m.UpsertShareDataRequest
):
    user_id = utils.user_id_from_email(jwt.get("email"))
    res = share_db.upsert_sharedata(user_id, req.sharedata)
    return res


@app.get("/asset-counts")
async def asset_counts(
    user: Annotated[m.RegisteredUser, Depends(authenticated_user)]
) -> m.AssetCountsResponse:
    results_dicts = asset_db.counts_by_org(user.org.slug)

    counts = {"Dataset": 0, "DataService": 0}
    for asset_type in counts.keys():
        for asset in results_dicts:
            if asset["assetLabel"] == asset_type:
                counts[asset_type] = asset["count"]
                break

    return m.AssetCountsResponse.model_validate(counts)


@app.post("/publish", tags=["data"])
async def publish_assets(
    body: pubres.CreateAssetsRequestBody,
) -> pubres.CreateAssetsResponseBody:
    data = body.dict()["data"]
    return pubres.CreateAssetsResponseBody.model_validate(publish.create_assets(data))


# multipart/form-data endpoint
# curl -F "datasets=@dataset.csv" -F "dataservices=@dataservice.csv" localhost:8000/publish/verify
@app.post("/publish/verify", tags=["data"])
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
    return pubres.format_response(parsed)
