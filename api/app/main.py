from uuid import UUID
import json
from typing import Annotated, List, Union
from fastapi import FastAPI, Body, Query, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from app import model as m
from app import db
from app.publish import csv as pubcsv, response as pubres
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
    if asset["type"] == m.assetType.dataset:
        asset = m.DatasetResponse.model_validate(asset)
    elif asset["type"] == m.assetType.service:
        asset = m.DataServiceResponse.model_validate(asset)
    else:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"asset": asset}


@app.post("/publish")
async def publish_assets(
    body: pubres.CreateAssetsRequestBody,
) -> pubres.CreateAssetsResponseBody:
    return


# multipart/form-data endpoint
# curl -F "datasets=@dataset.csv" -F "dataservices=@dataservice.csv" localhost:8000/publish/batch/create_job
@app.post("/publish/parse_file")
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
