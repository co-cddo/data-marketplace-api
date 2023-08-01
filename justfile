run:
  cd api && poetry export -f requirements.txt --output requirements.txt
  docker compose up --build
  # poetry run uvicorn api.app.main:app --reload

setup-hooks:
  poetry run pre-commit install
  poetry run pre-commit run --all-files

generate-spec-file:
  curl localhost:8000/openapi.json | yq eval -P > openapi.yaml
