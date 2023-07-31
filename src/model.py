import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Literal
from pydantic.networks import AnyUrl


class rightsStatement(str, Enum):
    internal = "INTERNAL"
    open = "OPEN"
    commercial = "COMMERCIAL"


class assetType(str, Enum):
    service = "DataService"
    dataset = "Dataset"


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


# TODO Update this to allow any IANA media type:
#  https://www.iana.org/assignments/media-types/media-types.xhtml
# or service type:
#  https://github.com/co-cddo/data-catalogue-schemas/blob/linkml/src/model/uk_cross_government_metadata_exchange_model.yaml#L466
class MediaType(str, Enum):
    csv = "CSV"
    xml = "XML"
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
    contactName: str | None = None
    email: str = Field(
        # TODO use some kinda library for this so it generates something sensible
        pattern=r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+",
        json_schema_extra={"description": "Valid email address"},
        examples=["user@domain.com"],
    )


class DistributionSummary(BaseModel):
    title: str
    modified: datetime
    mediaType: MediaType


class BaseAssetSummary(BaseModel):
    created: datetime
    description: str
    modified: datetime | None = None
    title: str
    type: assetType  # TODO I reckon this should be a uri - dcat:DataService, dcat:DataSet


class BaseAsset(BaseAssetSummary):
    accessRights: rightsStatement | None = None
    alternativeTitle: List[str] | None = []
    contactPoint: ContactPoint
    issued: datetime | None = None
    keyword: List[str] | None = []
    licence: AnyUrl | None = (
        "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    )
    relatedAssets: List[AnyUrl] | None = []
    securityClassification: securityClass | None = securityClass.official
    summary: str | None = None
    theme: List[AnyUrl] | None = []
    version: str | None = "1.0"

    class Config:
        use_enum_values = True


# Common class for assets returned from the server
class OutputAssetInfo(BaseModel):
    catalogueCreated: datetime
    catalogueModified: datetime
    creator: List[Organisation] | None = []
    identifier: uuid.UUID
    organisation: Organisation


# A single dataset returned from asset detail endpoint
class Dataset(BaseAsset, OutputAssetInfo):
    distributions: list[DistributionSummary]
    type: Literal[assetType.dataset]


class DataService(BaseAsset, OutputAssetInfo):
    endpointDescription: str
    endpointURL: str | None = None
    servesData: list[AnyUrl]
    serviceStatus: ServiceStatus
    serviceType: list[ServiceType]
    type: Literal[assetType.service]

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
                    "creator": ["department-for-work-pensions"],
                    "description": 'The location-service provides endpoints to perform a range of address based queries for UK locations. The reference data used is provided by Ordnance Survey and covers Great Britain Northern Ireland and the Channel Islands.\n\nThe API currently supports the following functions:\n\n- Postcode Lookup and filtering\n- Fuzzy address searching\n- Unique Property Reference Number (UPRN) lookup\n- Address matching\n- Data provided\n\n## Postcode lookup and fuzzy address search\n\nThis endpoint serves as both the standard postcode lookup and the fuzzy lookup. If you call the endpoint with just a search string query parameter the service will perform a fuzzy search against your string and bring back the closest matching results.\n\nFor example sending a request to the lookup endpoint with the search string "holy island castle" will return the following address as the top result:\n\n- `NATIONAL TRUST`\n- `LINDISFARNE CASTLE`\n- `HOLY ISLAND`\n- `BERWICK-UPON-TWEED`\n- `TD15 2SH`\n  \nAlternatively if you want to limit your search to a specific postcode you can call the endpoint with the postcode query parameter set. If you call the endpoint with just the postcode then the service will return all addresses for that postcode.\n  \nIf you call the endpoint with both postcode and search string the service will return only addresses that match the provided postcode and search string.\n  \nThere is also one further parameter for this endpoint (excludeBusiness) which if set will restrict the returned result list to non-commercial addresses.\n  \n## Unique Property Reference Number lookup\n  \nThis endpoint will take a unique property reference number (UPRN) as a query parameter and return the specific address record for that ID if present in the data set. As the data set contains a snapshot of current addresses it may be the case that UPRNs which are no longer valid get removed from the data set by Ordnance Survey.\n  \n## Address matching\n  \nThis endpoint provides an address matching function. It will take an unstructured address string along with a postcode and try to find an exact match in the data set. If the service can find an exact match then that specific record will be returned. If no match is found then no records are returned. This endpoint also uses fuzzy matching algorithms which allow it to cope with spelling mistakes transposed characters and other errors within the search string.',
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
                    "serviceType": ["REST"],
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
class DataAssetSummary(BaseAssetSummary, OutputAssetInfo):
    # mediaType technically only belongs to Distributions, but we're
    # using is here also as a synonym for a DataService's serviceType
    mediaType: List[MediaType]


class SearchAssetsResponse(BaseModel):
    data: List[DataAssetSummary]
    facets: SearchFacets


class CreateAssetBody(BaseAsset):
    organisationID: organisationID
    creatorID: List[organisationID] | None = []


# def create(asset: CreateAssetBody):
#     data = dict(asset)
#     data["organisation"] = lookup_organisation(data["organisationID"])
#     data.pop("organisationID")
#     creator = [lookup_organisation(o) for o in data["creatorID"]]
#     data.pop("creatorID")
#     data["id"] = uuid.uuid4()
#     return DataAsset.parse_obj(data)
