# CDDO Data Marketplace API
This repository will contain a barebones implementation of the API used for the MVP of the CDDO Data Marketplace project.

## Prerequisites

### just (required)
We just [just](https://github.com/casey/just) for running project-specific commands (see the [justfile](justfile)). 

Install using `brew install just` if you're on macOS, otherwise there are more instructions [here](https://github.com/casey/just#packages).

### Poetry (required)
For python version and dependency management.

Installation instructions are [here](https://python-poetry.org/docs/#installing-with-the-official-installer).

### docker (required)
For running the local API and [Fuseki](https://jena.apache.org/documentation/fuseki2/) SPARQL server.

Installation instructions for macOS [here](https://docs.docker.com/desktop/install/mac-install/).

### yq (optional)
A "lightweight and portable command-line YAML processor". 

We're using FastAPI to generate the OpenAPI spec in JSON format, and `yq` to convert it to yaml format.

Installation instructions are [here](https://github.com/mikefarah/yq/#install) (hopefully just `brew install yq`).

## Usage
### Initial setup
-  Install the prerequisites listed above.
-  Install the python dependencies for the API: `cd api && poetry install`.
-  Install the `pre-commit` hooks if you're planning on contributing to this repository: `just setup-hooks`

### API
Start the API and Fuseki database with `just run`.

The OpenAPI/Swagger documentation will be served at: http://localhost:8000/docs.

Fuseki will be initialised with the data in `fuseki/data` pre-loaded in the database.

The Fuseki web UI will be served at http://localhost:3030, the username is `admin` and the password is printed in the Docker compose logs.
