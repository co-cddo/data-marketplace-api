import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List
from pydantic.networks import AnyUrl


class rightsStatement(str, Enum):
    internal = "INTERNAL"
    open = "OPEN"
    commercial = "COMMERCIAL"


class resourceType(str, Enum):
    service = "dataService"
    dataset = "dataset"


organisations = {
    "department-for-work-pensions": {
        "id": "department-for-work-pensions",
        "title": "Department for Work & Pensions",
        "acronym": "DWP",
        "homepage": "https://www.gov.uk/government/organisations/department-for-work-pensions",
    },
    "food-standards-agency": {
        "id": "food-standards-agency",
        "title": "Food Standards Agency",
        "acronym": "FSA",
        "homepage": "https://www.food.gov.uk/",
    },
    "nhs-digital": {
        "id": "nhs-digital",
        "title": "NHS Digital",
        "acronym": "NHS Digital",
        "homepage": "https://digital.nhs.uk/",
    },
    "ordnance-survey": {
        "id": "ordnance-survey",
        "title": "Ordnance Survey",
        "acronym": "OS",
        "homepage": "https://www.gov.uk/government/organisations/ordnance-survey",
    },
}


class Organisation(BaseModel):
    title: str
    id: str
    acronym: str
    homepage: AnyUrl

    def from_id(org_id):
        org = orgs[org_id]
        return Organisation(
            title=org["title"],
            slug=org_id,
            acronym=org["acronym"],
            homepage=org["homepage"],
        )

    @model_validator(mode="after")
    def check_valid_org(self) -> "Organisation":
        if dict(self) == organisations.get(self.id):
            return self
        else:
            raise ValueError(f"Invalid organisation {dict(self)}")


class securityClass(str, Enum):
    official = "OFFICIAL"
    secret = "SECRET"
    top_secret = "TOP_SECRET"
    na = "NOT_APPLICABLE"


class BaseResourceSummary(BaseModel):
    title: str
    description: str
    created: datetime
    type: resourceType  # TODO I reckon this should be a uri - dcat:DataService, dcat:DataSet
    modified: datetime | None = None


class BaseResource(BaseResourceSummary):
    alternativeTitle: List[str] | None = []
    issued: datetime | None = None
    accessRights: rightsStatement | None = None
    # TODO: features contactName, email
    contactPoint: str = Field(
        # TODO use some kinda library for this so it generates something sensible
        pattern=r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+",
        json_schema_extra={"description": "Valid email address"},
    )
    keyword: List[str] | None = []
    relatedResource: List[AnyUrl] | None = []
    summary: str | None = None
    # TODO - URL, label, and ID
    theme: List[AnyUrl] | None = []

    # TODO - dunno if these are right
    licence: AnyUrl | None = (
        "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    )
    securityClassification: securityClass | None = securityClass.official
    version: str | None = "1.0"

    class Config:
        use_enum_values = True


# Common class for resources returned from the server
class OutputResourceInfo(BaseModel):
    id: uuid.UUID
    publisher: Organisation


# A single resource returned from resource detail endpoint
class DataResource(BaseResource, OutputResourceInfo):
    creator: List[Organisation] | None = []


# For the list endpoint, which returns only a summary of each resource
class DataResourceSummary(BaseResourceSummary, OutputResourceInfo):
    pass


def validate_org_id(org_id: str):
    if organisations.get(org_id) is not None:
        return org_id
    else:
        raise ValueError(f"No organisation with ID {org_id}")


class CreateResourceBody(BaseResource):
    publisherID: str
    creatorID: List[str] | None = []

    class Config:
        use_enum_values = True

    @field_validator("publisherID")
    def publisher_exists(cls, pid) -> str:
        return validate_org_id(pid)

    @field_validator("creatorID")
    def all_creators_exist(cls, creator_ids) -> List[str]:
        return [validate_org_id(c) for c in creator_ids]


def create(resource: CreateResourceBody):
    publisher = Organisation.from_id(resource.publisherID)
    creator = [Organisation.from_id(o) for o in resource.creatorID]
    data = dict(resource)
    data.pop("publisherID")
    data.pop("creatorID")
    data["id"] = uuid.uuid4()
    return DataResource.parse_obj(data)
