from dotenv import load_dotenv
import os, sys
from rdflib import Namespace

load_dotenv()
TRIPLESTORE_URL = os.environ.get("TRIPLESTORE_URL", None)
if not TRIPLESTORE_URL:
    sys.exit("ERROR: TripleStore URL is not set.")

DATASET_NAME = os.environ.get("DATASET_NAME", None)
if not DATASET_NAME:
    sys.exit("ERROR: Dataset name is not set.")

QUERY_URL = f"{TRIPLESTORE_URL}/{DATASET_NAME}/sparql"
UPDATE_URL = f"{TRIPLESTORE_URL}/{DATASET_NAME}/update"

JWKS_URL = os.environ.get("JWKS_URL", None)
JWT_AUD = os.environ.get("JWT_AUD", None)
OPS_API_KEY = os.environ.get("OPS_API_KEY", None)

cddo_graph = Namespace("http://marketplace.cddo.gov.uk/graph/")
ASSET_GRAPH = cddo_graph.assets
USER_GRAPH = cddo_graph.users
SHARE_GRAPH = cddo_graph.shares
