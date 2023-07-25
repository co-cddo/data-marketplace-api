from uuid import UUID
from typing import Annotated, List
from fastapi import FastAPI, Body, Query, HTTPException
from fastapi.responses import JSONResponse
import src.model as m
from pydantic import BaseModel, field_validator

app = FastAPI()


@app.get("/")
async def root():
    return {"greeting": "Hello world"}


# TODO: in order to find out what filters are available, we need
# and endpoint to return all of the available organisations, themes, and types.
# Something like this, except we'll need to figure out how themes work.
# May not need it for types seeing as we only have 2


@app.get("/list/organisations")
async def list_organisations() -> List[m.Organisation]:
    return [m.Organisation.parse_obj(o) for o in m.organisations.values()]


# TODO: add theme query param
@app.get("/catalogue")
async def list_catalogue_entries(
    query: str = None,
    publisherID: Annotated[List[m.organisationID], Query()] = [],
    resourceType: Annotated[List[m.resourceType], Query()] = [],
    _limit: int = 100,
    _offset: int = 0,
) -> list[m.DataResourceSummary]:
    return []


@app.get("/catalogue/{resource_id}")
async def catalogue_entry_detail(resource_id: UUID) -> m.DataResource:
    # Obviously, this would return the resource if it existed!
    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/dataset/new")
async def new_ds(resource: m.CreateResourceBody) -> m.DataResource:
    return create(resource)
