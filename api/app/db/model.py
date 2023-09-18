from app import model as m
from rdflib.term import URIRef, BNode
from rdflib import Namespace
from rdflib.namespace import RDF, RDFS, DCTERMS, DCAT, SKOS
from pydantic.networks import AnyUrl
from datetime import datetime
from uuid import UUID, uuid4
from app.db.reference_data import reference_data_validator


CDDO_ASSET = Namespace("http://marketplace.cddo.gov.uk/asset/")
CDDO_DISTRIBUTION = Namespace("http://marketplace.cddo.gov.uk/asset/distribution/")
CGMEM = Namespace(
    "https://w3id.org/co-cddo/uk-cross-government-metadata-exchange-model/"
)
ADMS = Namespace("https://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")


def subject_uri(asset):
    id = str(asset["identifier"])
    return CDDO_ASSET[id]


def distribution_uri(distribution):
    id = str(distribution["identifier"])
    return CDDO_DISTRIBUTION[id]


def type_uri(type_str):
    match type_str:
        case m.assetType.dataset:
            return DCAT.Dataset
        case m.assetType.service:
            return DCAT.DataService


def extract_organisation_slug(organisation):
    return organisation["slug"]


def wrap_markdown(markdown_str):
    return markdown_str.replace("\\", "\\\\").replace('"', '\\"')


class SimpleAttribute:
    def __init__(self, predicate, value_converter=lambda v: v):
        self.predicate = predicate
        self.value_converter = value_converter

    def to_triples(self, subject_uri, input_value):
        return [[subject_uri, self.predicate, self.value_converter(input_value)]]


class ListAttribute:
    def __init__(self, predicate, value_converter=lambda v: v):
        self.predicate = predicate
        self.value_converter = value_converter

    def to_triples(self, subject_uri, input_values):
        return [
            [subject_uri, self.predicate, self.value_converter(v)] for v in input_values
        ]


class ObjectAttribute:
    def __init__(self, predicate, attributes, object_id_fn=None, object_type_uri=None):
        self.predicate = predicate
        self.attributes = attributes
        self.object_id_fn = object_id_fn if object_id_fn else lambda x: BNode()
        self.object_type_uri = object_type_uri

    def to_triples(self, subject_uri, input_values_dict):
        object_id = self.object_id_fn(input_values_dict)
        triples = [[subject_uri, self.predicate, object_id]]
        if self.object_type_uri:
            triples.append([object_id, RDF.type, self.object_type_uri])
        for fieldname, attribute in self.attributes.items():
            if input_values_dict.get(fieldname):
                triples = triples + attribute.to_triples(
                    object_id, input_values_dict[fieldname]
                )
        return triples


class ObjectListAttribute:
    # For an attribute whos value is a list of objectattributes
    def __init__(self, object_attribute):
        self.object_attribute = object_attribute

    def to_triples(self, subject_uri, input_value_dicts):
        triples = []
        for obj_val in input_value_dicts:
            triples = triples + self.object_attribute.to_triples(subject_uri, obj_val)
        return triples


predicates_map = {
    "catalogueCreated": SimpleAttribute(CDDO_ASSET.created),
    "catalogueModified": SimpleAttribute(CDDO_ASSET.modified),
    "created": SimpleAttribute(DCTERMS.created),
    "modified": SimpleAttribute(DCTERMS.modified),
    "summary": SimpleAttribute(RDFS.comment),
    "title": SimpleAttribute(DCTERMS.title),
    "type": SimpleAttribute(RDF.type, value_converter=type_uri),
    "accessRights": SimpleAttribute(DCTERMS.accessRights),
    "alternativeTitle": ListAttribute(DCTERMS.alternative),
    "contactPoint": ObjectAttribute(
        DCAT.contactPoint,
        {
            "name": SimpleAttribute(VCARD.fn),
            "email": SimpleAttribute(VCARD.hasEmail),
            "telephone": SimpleAttribute(VCARD.hasTelephone),
            "address": SimpleAttribute(VCARD.hasAddress),
        },
        object_type_uri=VCARD.Kind,
    ),
    "description": SimpleAttribute(DCTERMS.description, value_converter=wrap_markdown),
    "issued": SimpleAttribute(CDDO_ASSET.issued),
    "keyword": ListAttribute(DCAT.keyword),
    "licence": SimpleAttribute(DCTERMS.license),
    "relatedAssets": ListAttribute(DCTERMS.relation),
    "securityClassification": SimpleAttribute(CGMEM.securityClassification),
    "theme": ListAttribute(
        DCAT.theme, value_converter=reference_data_validator.theme_uri
    ),
    "version": SimpleAttribute(DCAT.version),
    "identifier": SimpleAttribute(DCTERMS.identifier),
    "distributions": ObjectListAttribute(
        ObjectAttribute(
            DCAT.distribution,
            {
                "title": SimpleAttribute(DCTERMS.title),
                "modified": SimpleAttribute(DCTERMS.modified),
                "mediaType": SimpleAttribute(
                    DCAT.mediaType,
                    value_converter=reference_data_validator.media_type_uri,
                ),
                "identifier": SimpleAttribute(DCTERMS.identifier),
                "accessService": SimpleAttribute(DCAT.accessService),
                "issued": SimpleAttribute(CDDO_ASSET.issued),
                "licence": SimpleAttribute(DCTERMS.license),
                "byteSize": SimpleAttribute(DCAT.byteSize),
                "externalIdentifier": SimpleAttribute(SKOS.notation),
            },
            object_id_fn=lambda d: d["distribution"],
            object_type_uri=DCAT.Distribution,
        )
    ),
    "updateFrequency": SimpleAttribute(
        DCTERMS.accrualPeriodicity,
        value_converter=reference_data_validator.update_freq_url,
    ),
    "endpointDescription": SimpleAttribute(DCAT.endpointDescription),
    "endpointURL": SimpleAttribute(DCAT.endpointURL),
    "servesDataset": ListAttribute(DCAT.servesDataset),
    "serviceStatus": SimpleAttribute(ADMS.status),
    "serviceType": SimpleAttribute(DCTERMS.type),
    "externalIdentifier": SimpleAttribute(SKOS.notation),
    "organisation": SimpleAttribute(
        DCTERMS.publisher, value_converter=extract_organisation_slug
    ),
    "creator": ListAttribute(
        DCTERMS.creator, value_converter=extract_organisation_slug
    ),
}


def format_term(rdf_term):
    if isinstance(rdf_term, BNode):
        return rdf_term.n3()
    if isinstance(rdf_term, URIRef) or isinstance(rdf_term, AnyUrl):
        return f"<{rdf_term}>"
    if isinstance(rdf_term, datetime):
        strdate = rdf_term.strftime("%Y-%m-%d")
        return f'"{strdate}"^^xsd:date'
    if isinstance(rdf_term, str) or isinstance(rdf_term, UUID):
        return f'"{rdf_term}"'
    else:
        return str(rdf_term)


def asset_to_triples(asset):
    asset_uri = asset["resourceUri"]
    triples = []
    for k, v in asset.items():
        if k in predicates_map and v is not None:  # TODO should always be!
            attribute = predicates_map[k]
            triples = triples + attribute.to_triples(asset_uri, v)
    triples = [[format_term(term) for term in triple] for triple in triples]
    return triples


def format_triple(triple):
    return f"{triple[0]} {triple[1]} {triple[2]} ."


def triples_to_sparql(triples):
    rows = [format_triple(triple) for triple in triples]
    return "\n".join(rows)
