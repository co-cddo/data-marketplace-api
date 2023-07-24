from fastapi import FastAPI, Body
from src.model import DataResource, CreateResourceBody, create

app = FastAPI()


@app.get("/")
async def root():
    return {"greeting": "Hello world"}


@app.get("/catalogue")
async def list_catalogue_entries() -> list[DataResource]:
    return []


@app.get("/catalogue/{resource_id}")
async def catalogue_entry_detail() -> DataResource:
    return None


@app.post("/dataset/new")
async def new_ds(resource: CreateResourceBody) -> DataResource:
    return create(resource)


# Find API Methods
# Search and Filter
# Facet search parameters
# Organisation
# Topic
# …
# Default find all
#
# GET /catalogue?query=?param1=1,2,3?etc
# _limit, _offset
# Get Asset Info
# GET /catalogue/[UUID]
