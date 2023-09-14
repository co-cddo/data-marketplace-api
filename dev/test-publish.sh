#!/bin/bash

# Get the directory containing the script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
datasets="$SCRIPT_DIR/dataset.csv"
dataservices="$SCRIPT_DIR/dataservice.csv"

json_file="$SCRIPT_DIR/publish_body.json"

echo "Calling CSV extraction endpoint for $datasets $dataservices"

curl -F "datasets=@$datasets" -F "dataservices=@$dataservices" localhost:8000/publish/verify > $json_file

echo "Output is in $json_file"

echo "Calling publish endpoint with output"

curl -XPOST -H "Content-type: application/json" -d @$json_file 'localhost:8000/publish'
