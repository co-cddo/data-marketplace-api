from uuid import UUID
import json
from typing import Annotated, List, Union
from fastapi import FastAPI, Body, Query, HTTPException, File, UploadFile
from app import model as m
from app import db
from app.publish import csv as pubcsv, batch
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


# multipart/form-data endpoint
# curl -F "datasets=@dataset.csv" -F "dataservices=@dataservice.csv" localhost:8000/publish/batch/create_job
@app.post("/publish/batch/create_job", status_code=201)
async def create_batch_publish_job(
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
) -> m.BeginBatchPublishJobResponse:
    try:
        services = pubcsv.parse_dataservice_file(dataservices.file)
        datasets = pubcsv.parse_dataset_file(datasets.file)
    except pubcsv.FileContentException as e:
        raise HTTPException(status_code=422, detail=str(e))
    job = batch.create_job(datasets + services)
    return {**job, "data": datasets + services}


@app.get("/publish/batch/{jobID}/status")
async def get_publish_job_status(jobID: UUID) -> m.BatchPublishJob:
    return batch.job_state(jobID)


@app.post("/publish/batch/{jobID}/publish")
async def publish_draft(jobID: UUID) -> m.BatchPublishJob:
    return batch.publish_draft_job(jobID)


@app.post("/publish/batch/{jobID}/abort")
async def abort_job(jobID: UUID) -> m.BatchPublishJob:
    return batch.abort_job(jobID)
