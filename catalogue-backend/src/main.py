from fastapi import FastAPI, Body

app = FastAPI()


@app.get("/")
async def root():
    return {"greeting": "Hello world"}


@app.get("/dataset/list")
async def datasets_ep():
    return db.list_datasets()


@app.post("/dataset/new")
async def new_ds(ds_id: str = Body(...), name: str = Body(...)):
    return db.add_entry(ds_id, name, "description")
