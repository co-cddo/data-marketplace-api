import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List
from pydantic.networks import AnyUrl


class rightsStatement(str, Enum):
    internal = "INTERNAL"
    open = "OPEN"
    commercial = "COMMERCIAL"


class assetType(str, Enum):
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


class organisationID(str, Enum):
    dwp = "department-for-work-pensions"
    fsa = "food-standards-agency"
    nhsd = "nhs-digital"
    os = "ordnance-survey"


def lookup_organisation(org_id: organisationID) -> Organisation:
    try:
        org_data = organisations[org_id]
    except:
        raise ValueError("Organisation does not exist")
    return Organisation.parse_obj(org_data)


class securityClass(str, Enum):
    official = "OFFICIAL"
    secret = "SECRET"
    top_secret = "TOP_SECRET"
    na = "NOT_APPLICABLE"


class SearchFacet(BaseModel):
    title: str
    id: str


class SearchFacets(BaseModel):
    topics: list[SearchFacet]
    organisations: list[SearchFacet]
    assetTypes: list[SearchFacet]


class ContactPoint(BaseModel):
    contactName: str | None = None
    email: str = Field(
        # TODO use some kinda library for this so it generates something sensible
        pattern=r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+",
        json_schema_extra={"description": "Valid email address"},
        examples=["user@domain.com"],
    )


class BaseAssetSummary(BaseModel):
    title: str
    description: str
    created: datetime
    type: assetType  # TODO I reckon this should be a uri - dcat:DataService, dcat:DataSet
    modified: datetime | None = None


class BaseAsset(BaseAssetSummary):
    alternativeTitle: List[str] | None = []
    issued: datetime | None = None
    accessRights: rightsStatement | None = None
    contactPoint: ContactPoint
    keyword: List[str] | None = []
    relatedAssets: List[AnyUrl] | None = []
    summary: str | None = None
    # TODO - URL, label, and ID for these?
    theme: List[AnyUrl] | None = []

    # TODO - dunno if these are right
    licence: AnyUrl | None = (
        "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    )
    securityClassification: securityClass | None = securityClass.official
    version: str | None = "1.0"

    class Config:
        use_enum_values = True


# Common class for assetss returned from the server
class OutputAssetInfo(BaseModel):
    id: uuid.UUID
    organisation: Organisation


# A single asset returned from asset detail endpoint
class DataAsset(BaseAsset, OutputAssetInfo):
    creator: List[Organisation] | None = []


# For the list endpoint, which returns only a summary of each asset
class DataAssetSummary(BaseAssetSummary, OutputAssetInfo):
    pass


class SearchAssetsResponse(BaseModel):
    data: List[DataAssetSummary]
    facets: SearchFacets


class CreateAssetBody(BaseAsset):
    organisationID: organisationID
    creatorID: List[organisationID] | None = []


def create(asset: CreateAssetBody):
    data = dict(asset)
    data["organisation"] = lookup_organisation(data["organisationID"])
    data.pop("organisationID")
    creator = [lookup_organisation(o) for o in data["creatorID"]]
    data.pop("creatorID")
    data["id"] = uuid.uuid4()
    return DataAsset.parse_obj(data)
