from datetime import datetime
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    PositiveInt,
    field_validator,
    model_validator,
)
from pydantic.functional_validators import AfterValidator
from pydantic.networks import AnyUrl
import re
from typing import List, Literal, Any, Optional, Annotated
import uuid


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

    @field_validator("email")
    @classmethod
    def email_must_be_gov_uk(cls, v: EmailStr) -> EmailStr:
        pattern = re.compile(r".+@.*.gov.uk")
        if re.fullmatch(pattern, v):
            return v
        else:
            raise ValueError("must be a .gov.uk domain")

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
    modified: PastDate
    mediaType: str
    accessService: str | None = None
    externalIdentifier: str
    issued: PastDate | None = None
    licence: AnyUrl
    byteSize: PositiveInt | None = None


class DistributionResponse(DistributionSummary):
    identifier: uuid.UUID
    distribution: AnyUrl = Field(serialization_alias="@id")


class BaseAssetSummary(BaseModel):
    created: PastDate | None = None
    summary: str
    modified: PastDate | None = None
    title: str
    type: assetType
    theme: List[str] | None = None

    @model_validator(mode="after")
    def check_created_before_modified(self):
        if self.created and self.modified:
            if self.created > self.modified:
                raise ValueError("created date must be before modified date")
        return self


class BaseAsset(BaseAssetSummary):
    accessRights: rightsStatement | None = None
    alternativeTitle: List[str] | None = []
    contactPoint: ContactPoint
    description: str
    issued: PastDate | None = None
    keyword: List[str] | None = []
    licence: AnyUrl
    relatedAssets: List[AnyUrl] | None = []
    securityClassification: Literal["OFFICIAL"]
    summary: str | None = None
    version: str | None = "1.0"
    externalIdentifier: str

    class Config:
        use_enum_values = True


# Common class for assets returned from the server
class OutputAssetInfo(BaseModel):
    catalogueCreated: PastDate
    catalogueModified: PastDate
    creator: List[Organisation]
    identifier: uuid.UUID
    organisation: Organisation
    resourceUri: AnyUrl = Field(serialization_alias="@id")

    @field_validator("creator")
    @classmethod
    def at_least_one_creator(cls, v: List[Organisation]) -> List[Organisation]:
        if len(v) > 0:
            return v
        else:
            raise ValueError("must have at least one creator")


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
    mediaType: List[str] = Field(examples=[["CSV", "text/csv"]])
    title: str = Field(examples=["Dataset title"])


class DataServiceSummary(BaseAssetSummary, OutputAssetInfo):
    type: Literal[assetType.service]
    serviceType: ServiceType
    title: str = Field(examples=["Data service title"])


class SearchAssetsResponse(BaseModel):
    data: List[DatasetSummary | DataServiceSummary]
    facets: SearchFacets


class AssetDetailResponse(BaseModel):
    asset: DatasetResponse | DataServiceResponse


class CreateAssetBody(BaseAsset):
    organisationID: str
    creatorID: List[str]

    @field_validator("creatorID")
    @classmethod
    def at_least_one_creator(cls, v: List[str]) -> List[str]:
        if len(v) > 0:
            return v
        else:
            raise ValueError("must have at least one creator")


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
