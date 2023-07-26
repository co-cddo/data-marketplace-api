run:
  poetry run uvicorn src.main:app --reload

start-fuseki:
  docker compose up --build -d

stop-fuseki:
  docker compose down

setup-hooks:
  poetry run pre-commit install
  poetry run pre-commit run --all-files

dev-deps:
  ./localdb/install.sh

start-db:
  (cd localdb && ./fuseki/fuseki-server --config=fuseki-config.ttl)

generate-spec-file:
  curl localhost:8000/openapi.json | yq eval -P > openapi.yaml
