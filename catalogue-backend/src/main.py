from uuid import UUID
from typing import Annotated, List
from fastapi import FastAPI, Body, Query, HTTPException
from fastapi.responses import JSONResponse
from src.model import (
    DataResource,
    CreateResourceBody,
    DataResourceSummary,
    create,
    resourceType,
    validate_org_id,
)
from pydantic import BaseModel, field_validator

app = FastAPI()


@app.get("/")
async def root():
    return {"greeting": "Hello world"}


# TODO: add theme query param
@app.get("/catalogue")
async def list_catalogue_entries(
    query: str = None,
    publisherID: Annotated[List[str], Query()] = [],
    resourceType: Annotated[List[resourceType], Query()] = [],
    _limit: int = 100,
    _offset: int = 0,
) -> list[DataResourceSummary]:
    bad_org_ids = []
    for i in publisherID:
        try:
            validate_org_id(i)
        except ValueError:
            bad_org_ids.append(i)
    if bad_org_ids != []:
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "loc": ["publisherID"],
                        "msg": f"Organisation ID(s) not found: {bad_org_ids}",
                        "type": "value_error",
                    }
                ]
            },
        )
    return []


@app.get("/catalogue/{resource_id}")
async def catalogue_entry_detail(resource_id: UUID) -> DataResource:
    # Obviously, this would return the resource if it existed!
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/dataset/new")
async def new_ds(resource: CreateResourceBody) -> DataResource:
    return create(resource)
