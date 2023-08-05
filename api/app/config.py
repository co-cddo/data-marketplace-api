from dotenv import load_dotenv
import os, sys

load_dotenv()
TRIPLESTORE_URL = os.environ.get("TRIPLESTORE_URL", None)
if not TRIPLESTORE_URL:
    sys.exit("TripleStore URL is not set.")

DATASET_NAME = os.environ.get("DATASET_NAME", None)
if not DATASET_NAME:
    sys.exit("Dataset name is not set.")

QUERY_URL = f"{TRIPLESTORE_URL}/{DATASET_NAME}/sparql"
UPDATE_URL = f"{TRIPLESTORE_URL}/{DATASET_NAME}/update"
