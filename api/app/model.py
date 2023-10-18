import uuid
from datetime import datetime, date
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    PositiveInt,
    field_validator,
    model_validator,
    conlist,
)
from pydantic.functional_validators import AfterValidator
from pydantic.networks import AnyUrl
from typing import List, Literal, Any, Optional, Annotated, Union
import uuid


class rightsStatement(str, Enum):
    internal = "INTERNAL"
    open = "OPEN"
    commercial = "COMMERCIAL"


class securityClassification(str, Enum):
    official = "OFFICIAL"
    secret = "SECRET"
    top_secret = "TOP_SECRET"
    not_applicable = "NOT_APPLICABLE"


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "https://www.gov.uk/api/organisations/department-for-work-pensions",
                    "title": "Department for Work and Pensions",
                    "abbreviation": "DWP",
                    "slug": "department-for-work-pensions",
                    "format": "Ministerial department",
                    "web_url": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                }
            ]
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "DWP Integration Team",
                    "email": "integration.technologyplatforms@dwp.gsi.gov.uk",
                }
            ]
        }
    }


def check_date_past(v: datetime) -> datetime:
    assert v <= datetime.now(v.tzinfo), "date must be in the past"
    return v


PastDate = Annotated[datetime, AfterValidator(check_date_past)]


class DistributionSummary(BaseModel):
    title: str
    mediaType: str
    licence: AnyUrl | None = "http://marketplace.cddo.gov.uk/licence/internal"
    modified: PastDate | None = None
    accessService: str | None = None
    externalIdentifier: str | None = None
    issued: PastDate | None = None
    byteSize: PositiveInt | None = None


class DistributionResponse(DistributionSummary):
    identifier: uuid.UUID
    distribution: AnyUrl = Field(serialization_alias="@id")


class BaseAssetSummary(BaseModel):
    created: PastDate | None = None
    summary: str
    modified: PastDate
    title: str
    type: assetType
    theme: List[str] | None = None

    @model_validator(mode="after")
    def check_created_before_modified(self):
        if self.created and self.modified:
            if self.created > self.modified:
                raise ValueError("created date must be before modified date")
        return self


class AssetForHref(BaseModel):
    identifier: str
    title: str


class BaseAsset(BaseAssetSummary):
    accessRights: rightsStatement
    alternativeTitle: List[str] | None = []
    contactPoint: ContactPoint
    description: str
    issued: PastDate | None = None
    keyword: List[str] | None = []
    licence: AnyUrl | Literal[
        "DATA_SHARE_REQUEST"
    ] | None = "http://marketplace.cddo.gov.uk/licence/internal"
    relatedAssets: List[AnyUrl | AssetForHref] | None = []
    securityClassification: securityClassification
    summary: str | None = None
    version: str | None = "1.0"
    externalIdentifier: str

    class Config:
        use_enum_values = True


# Common class for assets returned from the server
class OutputAssetInfo(BaseModel):
    catalogueCreated: PastDate
    catalogueModified: PastDate
    creator: conlist(Organisation, min_length=1)
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
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "accessRights": "INTERNAL",
                    "catalogueCreated": "2023-07-31T11:26:50.383Z",
                    "catalogueModified": "2023-07-31T11:26:50.383Z",
                    "contactPoint": ContactPoint.model_config["json_schema_extra"][
                        "examples"
                    ][0],
                    "creator": Organisation.model_config["json_schema_extra"][
                        "examples"
                    ],
                    "identifier": "fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "externalIdentifier": "postcode-dataset-id",
                    "@id": "http://marketplace.cddo.gov.uk/asset/fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "organisation": Organisation.model_config["json_schema_extra"][
                        "examples"
                    ][0],
                    "distributions": [
                        {
                            "@id": "http://marketplace.cddo.gov.uk/asset/distribution/531847ba-441c-4dd9-afa4-213cfd5a55b2",
                            "identifier": "531847ba-441c-4dd9-afa4-213cfd5a55b2",
                            "title": "Document 1",
                            "modified": "2023-02-01T00:00:00",
                            "mediaType": "text/csv",
                            "externalIdentifier": "doc-1",
                            "licence": "https://opensource.org/license/isc-license-txt/",
                        },
                        {
                            "@id": "http://marketplace.cddo.gov.uk/asset/distribution/dcc16430-cd13-4699-b21c-6ea127377346",
                            "identifier": "dcc16430-cd13-4699-b21c-6ea127377346",
                            "title": "Document 2",
                            "modified": "2023-08-01T00:00:00",
                            "mediaType": "XLS",
                            "externalIdentifier": "doc-2",
                            "licence": "https://opensource.org/license/isc-license-txt/",
                            "issued": "2023-07-01T00:00:00",
                            "byteSize": 123456,
                        },
                    ],
                    "description": "A description of the dataset",
                    "issued": "2022-01-23T00:00:00",
                    "keyword": ["Location"],
                    "licence": "https://opensource.org/license/isc-license-txt/",
                    "modified": "2023-01-30T00:00:00",
                    "relatedAssets": [],
                    "securityClassification": "OFFICIAL",
                    "summary": "Location dataset",
                    "theme": [
                        "https://www.data.gov.uk/search?filters%5Btopic%5D=Mapping"
                    ],
                    "title": "Postcode dataset",
                    "type": "Dataset",
                    "updateFrequency": "freq:monthly",
                    "version": "2.0.0",
                }
            ]
        }
    }


class DataService(BaseAsset):
    endpointDescription: AnyUrl
    endpointURL: str | None = None
    servesDataset: list[AnyUrl | AssetForHref] | None = []
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
                    "contactPoint": ContactPoint.model_config["json_schema_extra"][
                        "examples"
                    ][0],
                    "creator": Organisation.model_config["json_schema_extra"][
                        "examples"
                    ],
                    "description": "The location-service provides endpoints to perform a range of address based queries for UK locations....",
                    "endpointDescription": "https://engineering.dwp.gov.uk/apis/docs",
                    "endpointURL": "",
                    "identifier": "fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "externalIdentifier": "address-lookup-service-id",
                    "@id": "http://marketplace.cddo.gov.uk/asset/fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "issued": "2022-01-23T00:00:00",
                    "keyword": ["Address Search", "UPRN"],
                    "licence": "https://opensource.org/license/isc-license-txt/",
                    "modified": "2023-01-30T00:00:00",
                    "organisation": Organisation.model_config["json_schema_extra"][
                        "examples"
                    ][0],
                    "relatedAssets": [],
                    "securityClassification": "OFFICIAL",
                    "servesDataset": [
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
    title: str
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "catalogueCreated": "2023-07-28T00:00:00",
                    "catalogueModified": "2023-08-01T00:00:00",
                    "creator": [
                        {
                            "id": "https://www.gov.uk/api/organisations/ordnance-survey",
                            "title": "Ordnance Survey",
                            "abbreviation": "OS",
                            "slug": "ordnance-survey",
                            "format": "Public corporation",
                            "web_url": "https://www.gov.uk/government/organisations/ordnance-survey",
                        }
                    ],
                    "identifier": "b3ae48af-c130-44ac-8341-5dead13c5427",
                    "organisation": {
                        "id": "https://www.gov.uk/api/organisations/department-for-work-pensions",
                        "title": "Department for Work and Pensions",
                        "abbreviation": "DWP",
                        "slug": "department-for-work-pensions",
                        "format": "Ministerial department",
                        "web_url": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                    },
                    "@id": "http://marketplace.cddo.gov.uk/asset/b3ae48af-c130-44ac-8341-5dead13c5427",
                    "summary": "Free and open postcode location data. Can be used for geographical analysis simple route planning asset management and much more.",
                    "modified": "2023-02-01T10:20:13+05:30",
                    "title": "OS Postcodes Data",
                    "type": "Dataset",
                    "theme": ["Mapping"],
                    "mediaType": ["CSV", "GeoPackage"],
                }
            ]
        }
    }


class DataServiceSummary(BaseAssetSummary, OutputAssetInfo):
    type: Literal[assetType.service]
    serviceType: ServiceType
    title: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "catalogueCreated": "2023-07-28T00:00:00",
                    "catalogueModified": "2023-08-01T00:00:00",
                    "creator": [
                        {
                            "id": "https://www.gov.uk/api/organisations/department-for-work-pensions",
                            "title": "Department for Work and Pensions",
                            "abbreviation": "DWP",
                            "slug": "department-for-work-pensions",
                            "format": "Ministerial department",
                            "web_url": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                        }
                    ],
                    "identifier": "fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "organisation": {
                        "id": "https://www.gov.uk/api/organisations/department-for-work-pensions",
                        "title": "Department for Work and Pensions",
                        "abbreviation": "DWP",
                        "slug": "department-for-work-pensions",
                        "format": "Ministerial department",
                        "web_url": "https://www.gov.uk/government/organisations/department-for-work-pensions",
                    },
                    "@id": "http://marketplace.cddo.gov.uk/asset/fcbc4d3f-0c05-4857-b0e3-eeec6bfea3a1",
                    "summary": "DWP single strategic solution for looking up addresses including fuzzy search and UPRN.",
                    "modified": "2023-01-30T00:00:00",
                    "title": "Address Lookup",
                    "type": "DataService",
                    "theme": ["Mapping"],
                    "serviceType": "REST",
                }
            ]
        }
    }


class SearchAssetsResponse(BaseModel):
    data: List[DatasetSummary | DataServiceSummary]
    facets: SearchFacets


class AssetDetailResponse(BaseModel):
    asset: DatasetResponse | DataServiceResponse


class CreateAssetBody(BaseAsset):
    organisationID: str
    creatorID: conlist(str, min_length=1)


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
    contactPoint: ContactPoint | None = None
    overviewSections: dict[str, ShareDataSection]
    steps: dict[str, ShareDataStep]


class UpsertShareDataRequest(BaseModel):
    sharedata: ShareData


ShareRequestDecisionStatus = Literal[
    "IN REVIEW",
    "RETURNED",
    "ACCEPTED",
    "REJECTED",
]

ShareRequestStatus = Union[
    ShareRequestDecisionStatus,
    Literal[
        "NOT STARTED",
        "IN PROGRESS",
        "AWAITING REVIEW",
    ],
]


class ShareRequest(BaseModel):
    requestId: str
    assetTitle: str
    requesterId: str
    requesterEmail: EmailStr
    requestingOrg: str
    assetPublisher: Organisation
    publisherContactName: str
    publisherContactEmail: EmailStr
    received: datetime
    status: ShareRequestStatus
    sharedata: Optional[ShareData] = None
    neededBy: date | Literal["UNREQUESTED"]
    decisionNotes: Optional[str] = None
    decisionDate: Optional[date] = None


class ShareRequestWithExtras(ShareRequest):
    reviewNotes: Optional[str] = None


class CreateDatasetBody(CreateAssetBody, Dataset):
    pass


class CreateDataServiceBody(CreateAssetBody, DataService):
    pass


class userPermission(str, Enum):
    member = "MEMBER"
    publisher = "PUBLISHER"
    org_admin = "ADMINISTRATOR"
    ops_admin = "OPS"
    reviewer = "SHARE_REVIEWER"


class EditUserOrgRequest(BaseModel):
    org: str


class EditUserPermissionRequest(BaseModel):
    add: List[userPermission] | None = []
    remove: List[userPermission] | None = []

    class Config:
        use_enum_values = True


# Base class for any user, with or without account
class AnyUser(BaseModel):
    id: Optional[str] = Field(serialization_alias="@id", default=None)
    email: Optional[EmailStr] = None
    org: Optional[Organisation] = None
    jobTitle: Optional[str] = None
    permission: Optional[List[userPermission]] = []

    class Config:
        use_enum_values = True


class RegisteredUser(AnyUser):
    id: str = Field(serialization_alias="@id")
    email: EmailStr


class SPARQLUpdate(BaseModel):
    statusCode: int
    message: str


class LoginResponse(BaseModel):
    user: RegisteredUser
    new_user: bool
    sharedata: dict[str, ShareData]


class CompleteProfileRequest(BaseModel):
    organisation: str
    jobTitle: str


class ReviewRequest(BaseModel):
    notes: str


class DecisionRequest(BaseModel):
    status: ShareRequestDecisionStatus
    decisionNotes: str
