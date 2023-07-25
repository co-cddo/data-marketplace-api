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
    organisationID,
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
    publisherID: Annotated[List[organisationID], Query()] = [],
    resourceType: Annotated[List[resourceType], Query()] = [],
    _limit: int = 100,
    _offset: int = 0,
) -> list[DataResourceSummary]:
    return []


@app.get("/catalogue/{resource_id}")
async def catalogue_entry_detail(resource_id: UUID) -> DataResource:
    # Obviously, this would return the resource if it existed!
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/dataset/new")
async def new_ds(resource: CreateResourceBody) -> DataResource:
    return create(resource)
