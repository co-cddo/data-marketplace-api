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
import json

load_dotenv()
print(os.getenv("UPDATE_URL"))

sparql_writer = SPARQLWrapper(os.environ.get("UPDATE_URL"))
sparql_writer.setReturnFormat(JSON)
sparql_writer.method = POST

MARKETPLACE = Namespace("http://dev.data-marketplace.gov.uk/")
DATASET = Namespace(MARKETPLACE["dataset/"])
catalogue_graph = MARKETPLACE["graph/catalogue"]

PREFIX = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX text: <http://jena.apache.org/text#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX cddo: <http://marketplace.cddo.gov.uk/asset/>
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


def search(q=""):
    if q == "":
        q = "*"

    query = f"""{PREFIX}
    SELECT ?identifier ?type ?title ?description ?organisation ?creator ?catalogueCreated ?catalogueModified ?created ?issued ?modified ?summary
    WHERE {{
        ?s text:query "{q}" ;
            dct:identifier ?identifier ;
            a ?type ;
            dct:title ?title ;
    	    dct:description ?description ;
            dct:publisher ?organisation ;
            dct:creator ?creator ;
            cddo:created ?catalogueCreated ;
            cddo:modified ?catalogueModified .
      	OPTIONAL {{ ?s dct:created ?created }} .
      	OPTIONAL {{ ?s dct:issued ?issued }} .
      	OPTIONAL {{ ?s dct:modified ?modified }} .
      	OPTIONAL {{ ?s rdfs:comment ?summary }} .
    }}
    """

    sparql_reader.setQuery(query)
    result = sparql_reader.queryAndConvert()["results"]["bindings"]

    result_dicts = [utils.queryResultToDict(r) for r in result]

    result_dicts = [utils.normaliseValues(r) for r in result_dicts]

    return result_dicts


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
