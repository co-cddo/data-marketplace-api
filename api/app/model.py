import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Literal, Any, Optional
from pydantic.networks import AnyUrl
import re


class rightsStatement(str, Enum):
    internal = "INTERNAL"
    open = "OPEN"
    commercial = "COMMERCIAL"


class assetType(str, Enum):
    service = "DataService"
    dataset = "Dataset"


class Organisation(BaseModel):
    id: str
    title: str
    abbreviation: str | None
    slug: str
    format: str
    web_url: AnyUrl


class securityClass(str, Enum):
    official = "OFFICIAL"
    secret = "SECRET"
    top_secret = "TOP_SECRET"
    na = "NOT_APPLICABLE"


class ServiceStatus(str, Enum):
    discovery = "DISCOVERY"
    alpha = "ALPHA"
    beta = "BETA"
    private_beta = "PRIVATE_BETA"
    public_beta = "PUBLIC_BETA"
    live = "LIVE"
    deprecated = "DEPRECATED"
    withdrawn = "WITHDRAWN"


class ServiceType(str, Enum):
    event = "EVENT"
    rest = "REST"
    soap = "SOAP"


class ServiceType(str, Enum):
    rest = "REST"
    event = "EVENT"
    soap = "SOAP"


class SearchFacet(BaseModel):
    title: str
    id: str


class SearchFacets(BaseModel):
    topics: list[SearchFacet]
    organisations: list[SearchFacet]
    assetTypes: list[SearchFacet]


class ContactPoint(BaseModel):
    name: str
    email: EmailStr
    telephone: str | None = None
    address: str | None = None

    @field_validator("email")
    @classmethod
    def email_must_be_gov_uk(cls, v: EmailStr) -> EmailStr:
        pattern = re.compile(r".+@.*.gov.uk")
        if re.fullmatch(pattern, v):
            return v
        else:
            raise ValueError("must be a .gov.uk domain")


class DistributionSummary(BaseModel):
    title: str
    modified: datetime
    mediaType: str
    accessService: str | None = None
    externalIdentifier: str | None = None
    issued: datetime | None = None
    licence: AnyUrl | None = (
        "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    )
    byteSize: int | None = None


class DistributionResponse(DistributionSummary):
    identifier: uuid.UUID
    distribution: AnyUrl = Field(serialization_alias="@id")


class BaseAssetSummary(BaseModel):
    created: datetime | None = None
    summary: str
    modified: datetime | None = None
    title: str
    type: assetType  # TODO I reckon this should be a uri - dcat:DataService, dcat:DataSet
    theme: List[str] | None = []


class BaseAsset(BaseAssetSummary):
    accessRights: rightsStatement | None = None
    alternativeTitle: List[str] | None = []
    contactPoint: ContactPoint
    description: str
    issued: datetime | None = None
    keyword: List[str] | None = []
    licence: AnyUrl | None = (
        "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    )
    relatedAssets: List[AnyUrl] | None = []
    securityClassification: securityClass | None = securityClass.official
    summary: str | None = None
    version: str | None = "1.0"
    externalIdentifier: str | None = None

    class Config:
        use_enum_values = True


# Common class for assets returned from the server
class OutputAssetInfo(BaseModel):
    catalogueCreated: datetime
    catalogueModified: datetime
    creator: Organisation
    identifier: uuid.UUID
    organisation: Organisation
    resourceUri: AnyUrl = Field(serialization_alias="@id")


class Dataset(BaseAsset):
    distributions: list[DistributionSummary]
    updateFrequency: str
    type: Literal[assetType.dataset]


# A single dataset returned from asset detail endpoint
class DatasetResponse(Dataset, OutputAssetInfo):
    distributions: list[DistributionResponse]
    # TODO update this
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "accessRights": "INTERNAL",
                    "catalogueCreated": "2023-07-31T11:26:50.383Z",
                    "catalogueModified": "2023-07-31T11:26:50.383Z",
                    "contactPoint": {
                        "contactName": "DWP Integration Team",
                        "email": "integration.technologyplatforms@dwp.gsi.gov.uk",
                    },
                    "creator": {
                        "id": "department-for-work-pensions",
                        "title": "Department for Work & Pensions",
                        "acronym": "DWP",
                        "homepage": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                    },
                    "description": "The location-service provides endpoints to perform a range of address based queries for UK locations....",
                    "distributions": [
                        {
                            "title": "document1",
                            "modified": "2023-08-01",
                            "mediaType": "CSV",
                        },
                        {
                            "title": "document2",
                            "modified": "2023-08-01",
                            "mediaType": "XLS",
                        },
                    ],
                    "identifier": "fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "issued": "2022-01-23",
                    "keyword": ["Address Search", "UPRN"],
                    "licence": "https://opensource.org/license/isc-license-txt/",
                    "modified": "2023-01-30",
                    "organisation": {
                        "id": "department-for-work-pensions",
                        "title": "Department for Work & Pensions",
                        "acronym": "DWP",
                        "homepage": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                    },
                    "relatedAssets": [],
                    "securityClassification": "OFFICIAL",
                    "summary": "DWP single strategic solution for looking up addresses including fuzzy search and UPRN.",
                    "theme": [
                        "https://www.data.gov.uk/search?filters%5Btopic%5D=Mapping"
                    ],
                    "title": "Address Lookup",
                    "type": "Dataset",
                    "updateFrequency": "Monthly",
                    "version": "2.0.0",
                }
            ]
        }
    }


class DataService(BaseAsset):
    endpointDescription: str
    endpointURL: str | None = None
    servesData: list[AnyUrl]
    serviceStatus: ServiceStatus
    serviceType: ServiceType
    type: Literal[assetType.service]


class DataServiceResponse(DataService, OutputAssetInfo):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "accessRights": "INTERNAL",
                    "catalogueCreated": "2023-07-31T11:26:50.383Z",
                    "catalogueModified": "2023-07-31T11:26:50.383Z",
                    "contactPoint": {
                        "contactName": "DWP Integration Team",
                        "email": "integration.technologyplatforms@dwp.gsi.gov.uk",
                    },
                    "creator": {
                        "id": "department-for-work-pensions",
                        "title": "Department for Work & Pensions",
                        "acronym": "DWP",
                        "homepage": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                    },
                    "description": "The location-service provides endpoints to perform a range of address based queries for UK locations....",
                    "endpointDescription": "https://engineering.dwp.gov.uk/apis/docs",
                    "endpointURL": "",
                    "identifier": "fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "issued": "2022-01-23",
                    "keyword": ["Address Search", "UPRN"],
                    "licence": "https://opensource.org/license/isc-license-txt/",
                    "modified": "2023-01-30",
                    "organisation": {
                        "id": "department-for-work-pensions",
                        "title": "Department for Work & Pensions",
                        "acronym": "DWP",
                        "homepage": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                    },
                    "relatedAssets": [],
                    "securityClassification": "OFFICIAL",
                    "servesData": [
                        "https://www.data.gov.uk/dataset/2dfb82b4-741a-4b93-807e-11abb4bb0875/os-postcodes-data",
                        "https://www.data.gov.uk/dataset/03d48dba-529b-4bd5-93a5-6d41d1b20ff9/national-address-gazetteer",
                        "https://www.data.gov.uk/dataset/92b32629-8ad4-43cb-9952-7d104971fa12/one-scotland-gazetteer",
                    ],
                    "serviceStatus": "LIVE",
                    "serviceType": "REST",
                    "summary": "DWP single strategic solution for looking up addresses including fuzzy search and UPRN.",
                    "theme": [
                        "https://www.data.gov.uk/search?filters%5Btopic%5D=Mapping"
                    ],
                    "title": "Address Lookup",
                    "type": "DataService",
                    "version": "2.0.0",
                }
            ]
        }
    }


# For the list endpoint, which returns only a summary of each asset
class DatasetSummary(BaseAssetSummary, OutputAssetInfo):
    type: Literal[assetType.dataset]
    mediaType: List[str]


class DataServiceSummary(BaseAssetSummary, OutputAssetInfo):
    type: Literal[assetType.service]
    serviceType: ServiceType


class SearchAssetsResponse(BaseModel):
    data: List[DatasetSummary | DataServiceSummary]
    facets: SearchFacets


class AssetDetailResponse(BaseModel):
    asset: DatasetResponse | DataServiceResponse


class CreateAssetBody(BaseAsset):
    organisationID: str
    creatorID: str


class JWT(BaseModel):
    token: str


class ShareDataSection(BaseModel):
    name: str
    steps: list[str]


class ShareDataStep(BaseModel):
    id: str
    name: str
    status: str
    value: Any
    nextStep: str
    errorMessage: Optional[str] = None


class ShareData(BaseModel):
    requestId: str
    assetTitle: str
    dataAsset: str  # aka asset ID
    ownedBy: str
    completedSections: int
    status: str
    overviewSections: dict[str, ShareDataSection]
    steps: dict[str, ShareDataStep]
    stepHistory: list[str] | None


class UpsertUserResponse(BaseModel):
    user_id: str
    sharedata: dict[str, ShareData]


class UpsertShareDataRequest(BaseModel):
    jwt: str
    sharedata: ShareData


class CreateDatasetBody(CreateAssetBody, Dataset):
    pass


class CreateDataServiceBody(CreateAssetBody, DataService):
    pass
