from app import model as m
from uuid import uuid4


def create_job(data: list[m.CreateDatasetBody | m.CreateDataServiceBody]):
    "Set off a job to add the given data and return its ID"
    return {"jobID": uuid4(), "jobStatus": m.publishJobStatus.created}


def job_state(job_id):
    "Check on the status of the job"
    return {"jobID": job_id, "jobStatus": m.publishJobStatus.created}


def publish_draft_job(job_id):
    "For a job in draft state, set off a job to make all of its datasets public"
    return {"jobID": job_id, "jobStatus": m.publishJobStatus.published}


def abort_job(job_id):
    "Abort the given job (instant - no async)"
    return {"jobID": job_id, "jobStatus": m.publishJobStatus.aborted}
