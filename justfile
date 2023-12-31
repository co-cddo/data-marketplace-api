run:
  cd api && poetry export -f requirements.txt --output requirements.txt
  docker compose up --build

shell-fuseki:
  docker compose exec fuseki /bin/bash
  
copy-backups:
  docker compose cp fuseki:/fuseki-base/backups .

shell-api:
  docker compose exec api /bin/sh

setup-hooks:
  cd api && poetry run pre-commit install
  cd api && poetry run pre-commit run --all-files

generate-spec-file:
  curl localhost:8000/openapi.json | yq eval -P > openapi.yaml

test:
  cd api/test && hurl --test --variables-file=.env admin_routes.hurl && hurl --test --variables-file=.env asset_details.hurl