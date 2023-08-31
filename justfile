run:
  cd api && poetry export -f requirements.txt --output requirements.txt
  docker compose up --build

shell-fuseki:
  docker compose exec fuseki /bin/sh

shell-api:
  docker compose exec api /bin/sh

setup-hooks:
  cd api && poetry run pre-commit install
  cd api && poetry run pre-commit run --all-files

generate-spec-file:
  curl localhost:8000/openapi.json | yq eval -P > openapi.yaml
