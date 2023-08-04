import os
from rdflib.namespace import (
    DC,
    DCTERMS,
    DOAP,
    FOAF,
    SKOS,
    OWL,
    RDF,
    RDFS,
    VOID,
    XMLNS,
    XSD,
)
from rdflib import Namespace
from SPARQLWrapper import SPARQLWrapper, JSON, POST

from dotenv import load_dotenv
from . import utils
from . import model as m
import json

load_dotenv()

sparql_writer = SPARQLWrapper(os.environ.get("UPDATE_URL"))
sparql_writer.setReturnFormat(JSON)
sparql_writer.method = POST

MARKETPLACE = Namespace("http://dev.data-marketplace.gov.uk/")
DATASET = Namespace(MARKETPLACE["dataset/"])
catalogue_graph = MARKETPLACE["graph/catalogue"]

PREFIX = """
PREFIX adms: <https://www.w3.org/ns/adms#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX text: <http://jena.apache.org/text#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX cddo: <http://marketplace.cddo.gov.uk/asset/>
PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
PREFIX uk_cross_government_metadata_exchange_model: <https://w3id.org/co-cddo/uk-cross-government-metadata-exchange-model/>
"""


def add_entry(ds_uri_slug, name, description):
    query = f"""
    INSERT DATA {{
        GRAPH <{catalogue_graph}> {{
            <{DATASET[ds_uri_slug]}> <{DCTERMS["title"]}> "{name}"
        }}
    }}
    """
    sparql_writer.setQuery(query)
    ret = sparql_writer.queryAndConvert()
    return ret


sparql_reader = SPARQLWrapper(os.environ.get("QUERY_URL"))
sparql_reader.setReturnFormat(JSON)


def mediatypes_of_dataset(identifier: str):
    query = f"""{PREFIX}
    SELECT ?mediaType
    WHERE {{
        ?s dct:identifier "{identifier}" ;
           dcat:distribution ?distribution .
        BIND(URI(STR(?distribution)) AS ?dist)
        ?dist dcat:mediaType ?mediaType .
    }}"""

    sparql_reader.setQuery(query)
    results = sparql_reader.queryAndConvert()["results"]["bindings"]
    result_dicts = [utils.search_query_result_to_dict(r) for r in results]
    media_types = [r["mediaType"] for r in result_dicts]
    return media_types


def distribution_detail(distribution: str):
    query = f"""{PREFIX}
    SELECT ?title ?modified ?mediaType
    WHERE {{
        <{distribution}> dct:title ?title;
                         dct:modified ?modified ;
                         dcat:mediaType ?mediaType .
    }}
    """

    sparql_reader.setQuery(query)
    results = sparql_reader.queryAndConvert()["results"]["bindings"]
    result_dict = [utils.search_query_result_to_dict(r) for r in results]
    assert len(result_dict) == 1
    return m.DistributionSummary.model_validate(result_dict[0])


def search(q: str = ""):
    if q == "":
        q = "*"

    # TODO What else do we need to do to sanitise the query string?
    q = utils.sanitise_search_query(q)

    query = f"""{PREFIX}
    SELECT ?identifier ?type ?title ?description ?organisation 
            ?catalogueCreated ?catalogueModified ?created ?issued ?modified 
            ?summary ?serviceType 
            (GROUP_CONCAT(DISTINCT(?creators); separator='|') AS ?creator)
    WHERE {{
        ?s text:query "{q}" ;
            dct:identifier ?identifier ;
            a ?type ;
            dct:title ?title ;
    	    dct:description ?description ;
            dct:publisher ?organisation ;
            cddo:created ?catalogueCreated ;
            cddo:modified ?catalogueModified .
        OPTIONAL {{ ?s dct:creator ?creators }} .
      	OPTIONAL {{ ?s dct:created ?created }} .
      	OPTIONAL {{ ?s dct:issued ?issued }} .
      	OPTIONAL {{ ?s dct:modified ?modified }} .
      	OPTIONAL {{ ?s rdfs:comment ?summary }} .
        OPTIONAL {{ ?s dct:type ?serviceType }} .
    }}
    GROUP BY ?identifier ?type ?title ?description ?organisation 
            ?catalogueCreated ?catalogueModified ?created ?issued ?modified 
            ?summary ?serviceType
    """

    sparql_reader.setQuery(query)
    result = sparql_reader.queryAndConvert()["results"]["bindings"]

    result_dicts = [utils.search_query_result_to_dict(r) for r in result]
    print(result_dicts)

    for r in result_dicts:
        if r["type"] == "Dataset":
            r["mediaType"] = mediatypes_of_dataset(r["identifier"])

    result_dicts = [utils.munge_asset_summary_response(r) for r in result_dicts]
    return result_dicts


def asset_detail(asset_id: str):
    query = f"""{PREFIX}
SELECT  ?updateFrequency ?endpointDescription ?endpointURL ?serviceStatus ?serviceType ?accessRights
?contactName ?contactEmail ?contactAddress ?contactTelephone ?created ?description ?issued
?licence ?modified ?organisation ?securityClassification ?summary ?title ?type ?catalogueCreated ?catalogueModified
(GROUP_CONCAT(DISTINCT(?creators); separator='|') AS ?creator)
(GROUP_CONCAT(DISTINCT(?keywords); separator='|') AS ?keyword)
(GROUP_CONCAT(DISTINCT(?alternativeTitles); separator='|') AS ?alternativeTitle)
(GROUP_CONCAT(DISTINCT(?relatedResources); separator='|') AS ?relatedResource)
(GROUP_CONCAT(DISTINCT(?themes); separator='|') AS ?theme)
(GROUP_CONCAT(DISTINCT(?servesDatas); separator='|') AS ?servesData)
(GROUP_CONCAT(DISTINCT(?distribution); separator='|') AS ?distributions)
WHERE {{
?s dct:identifier "{asset_id}" ;
   dcat:contactPoint ?contact ;
   dct:description ?description ;
   dct:license ?licence ;
   dct:publisher ?organisation ;
   uk_cross_government_metadata_exchange_model:securityClassification ?securityClassification ;
   dct:title ?title ;
   a ?type;
   dcat:version ?version ;
   cddo:created ?catalogueCreated ;
   cddo:modified ?catalogueModified .
  OPTIONAL {{ ?s dct:accrualPeriodicity ?updateFrequency }} .
  OPTIONAL {{ ?s dcat:distribution ?distribution }} .
  OPTIONAL {{ ?s dcat:endpointDescription ?endpointDescription }}.
  OPTIONAL {{ ?s dcat:endpointURL ?endpointURL }}.
  OPTIONAL {{ ?s dcat:servesData ?servesDatas }} .
  OPTIONAL {{ ?s adms:status ?serviceStatus }} .
  OPTIONAL {{ ?s dct:type ?serviceType }} .
  OPTIONAL {{ ?s dct:accessRights ?accessRights }} .
  OPTIONAL {{ ?s dct:created ?created }} .
  OPTIONAL {{ ?s dct:issued ?issued }} .
  OPTIONAL {{ ?s dct:modified ?modified }} .
  OPTIONAL {{ ?s rdfs:comment ?summary }} .
  OPTIONAL {{ ?s dct:creator ?creators }} .
  OPTIONAL {{ ?s dcat:keyword ?keywords }} .
  OPTIONAL {{ ?s dct:alternative ?alternativeTitles }} .
  OPTIONAL {{ ?s dct:relation ?relatedResources }} .
  OPTIONAL {{ ?s dcat:theme ?themes }} .

  ?contact vcard:fn ?contactName ;
           vcard:hasEmail ?contactEmail.
  OPTIONAL {{?contact vcard:hasTelephone ?contactTelephone}}
  OPTIONAL {{?contact vcard:hasAddress ?contactAddress}}
}}
GROUP BY ?updateFrequency ?endpointDescription ?endpointURL ?serviceStatus ?serviceType ?accessRights
?contactName ?contactEmail ?contactAddress ?contactTelephone ?created ?description ?issued
?licence ?modified ?organisation ?securityClassification ?summary ?title ?type ?catalogueCreated ?catalogueModified
    """
    sparql_reader.setQuery(query)
    result = sparql_reader.queryAndConvert()["results"]["bindings"]

    result_dicts = [utils.search_query_result_to_dict(r) for r in result]
    assert len(result_dicts) == 1
    asset = result_dicts[0]

    asset["identifier"] = asset_id

    contactPoint = {
        "name": asset["contactName"],
        "email": asset["contactEmail"],
        "contactTelephone": asset.get("contentTelephone", None),
        "contactAddress": asset.get("contentAddress", None),
    }

    asset["contactPoint"] = m.ContactPoint.model_validate(contactPoint)

    if asset["type"] == m.assetType.dataset:
        distributions = [distribution_detail(d) for d in asset["distributions"]]
        asset["distributions"] = distributions

    return asset


def list_datasets():
    query = f"""
    SELECT * WHERE {{
        GRAPH <{catalogue_graph}> {{
            ?s ?p ?o .
        }}
    }}
    """
    sparql_reader.setQuery(query)
    return sparql_reader.queryAndConvert()
