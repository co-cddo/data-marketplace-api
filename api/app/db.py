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

load_dotenv()
print(os.getenv("UPDATE_URL"))

sparql_writer = SPARQLWrapper(os.environ.get("UPDATE_URL"))
sparql_writer.setReturnFormat(JSON)
sparql_writer.method = POST

MARKETPLACE = Namespace("http://dev.data-marketplace.gov.uk/")
DATASET = Namespace(MARKETPLACE["dataset/"])
catalogue_graph = MARKETPLACE["graph/catalogue"]


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
