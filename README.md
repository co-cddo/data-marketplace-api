# CDDO Data Marketplace API

This repository contains everything you need to build the API used for the MVP of the CDDO Data Marketplace project, including the database.

<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

* [Context](#context)
  + [Requirements](#requirements)
* [Implementation](#implementation)
  + [Architecture](#architecture)
    - [Fuseki](#fuseki)
    - [FastAPI](#fastapi)
  + [API design](#api-design)
    - [`/catalogue`](#catalogue)
    - [`/publish/verify`](#publishverify)
* [Build and run](#build-and-run)
  + [Prerequisites](#prerequisites)
    - [just (required)](#just-required)
    - [Poetry (required)](#poetry-required)
    - [docker (required)](#docker-required)
    - [yq (optional)](#yq-optional)
  + [Usage](#usage)
    - [Initial setup](#initial-setup)
      * [Environment variables](#environment-variables)
    - [API](#api)
    - [Triplestore ](#triplestore)

<!-- TOC end -->

<!-- TOC --><a name="context"></a>
## Context

The original plan for the Data Marketplace was to include two main components: a catalogue backend built upon software such as [CKAN](https://github.com/ckan/ckan), and a [javascript webapp](https://github.com/co-cddo/data-marketplace). Early in development, it became clear that we could not use CKAN as the back end for several reasons, most notably that it could not be configured to work with the cross-government metadata model. We began researching alternative cataloguing softwares, but whatever catalogue we might use, there would always be a need for an additional layer between it and the webapp to deal with things like user roles and data validation.

Why, you ask, could we not do such things in the webapp back end? Technically, that might well have made sense, but we already had a front end team working on a webapp that expected a fully-formed catalogue API and did not want to disrupt that work as a result of moving away from CKAN. Additionally, the timing was such that we needed to deliver an MVP faster than we could get a decision on the catalogue software. We hoped to avoid involving third-party catalogue software entirely if we couldn't find anything fit for the job, so it made sense to keep our own version in the same place as the intermediate layer.

The result was what you see here: a minimal implementation of a catalogue API, with the additional behaviour needed to support the aforementioned aspect of the API. We selected a simple triplestore as our database and figured we could replace it with whatever catalogue software was chosen without changing the API exposed to the webapp.

<!-- TOC --><a name="requirements"></a>
### Requirements

To support the webapp, we needed a REST API that could perform the following:

* Add/edit metadata records
* Retrieve metadata records
* Create data share requests
* Review data share requests
* Add/edit users
* Assign permission roles to users
* Check whether users have permission to perform the above actions based on their permission roles

<!-- TOC --><a name="implementation"></a>
## Implementation

<!-- TOC --><a name="architecture"></a>
### Architecture

As this was never intended to see production in its entirety, we opted for the most basic architecture that would do the job: a [FastAPI](https://fastapi.tiangolo.com/) API with a [Fuseki](https://jena.apache.org/documentation/fuseki2/) triplestore behind it, both in Docker containers.

<!-- TOC --><a name="fuseki"></a>
#### Fuseki

We chose to store all of the data as RDF for two reasons: the [UK cross-government metadata model](https://www.gov.uk/government/collections/metadata-standards-for-sharing-and-publishing-data) is already based on the [Dublin Core vocabulary](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/), and the team had plenty of experience with linked data already. The specific choice of Apache Jena Fuseki as our graph/triple store was simply that it's free and we already know how to use it. We had planned to replace this with AWS Neptune if a suitable ready-made catalogue backend could not be found.

Once concern that was raised about this choice was the security risk of storing user data and site data in the same triplestore, in case we accidentally exposed something sensitive. We mitigated this risk by using separate graphs for each; if this had gone to production, we would have used separate connections that restricted access to a single graph, but there seemed little point in doing this for the temporary Fuseki stand-in.

In addition to the data that gets added from the API endpoints, we need some additional reference data such as labels for concepts referred to in the catalogue entries. This is stored in `/fuseki/data` (along with some sample data to populate the database with dummy catalogue entries) and gets loaded in at startup. Note that recreating the container will wipe all of this data.

<!-- TOC --><a name="fastapi"></a>
#### FastAPI

The reason we selected FastAPI as our framework is in the name: we needed an MVP sooner rather than later, and this was quick and easy to set up. Additionally it allowed for the automatic generation of an API spec that can be accessed by the front-end team. When the app is up and running, you'll be able to see this at `localhost:8000/redoc`

There's nothing of particular note in how we chose to design the API as it follows a fairly standard pattern. A single (Pydantic)[https://docs.pydantic.dev/latest/] model defines the metadata model along with various other data models such as users, permissions, and data shares.

We deliberately kept the database-related stuff in `/db` so we could more easily migrate to some kind of cataloguing software (or another graph database like Neptune) further down the line. As mentioned above, we did want to keep the user, asset, and share request graphs separate so we used three different connection class instances (at present they do all have access to all graphs, but we set up the structure so this could be changed).

<!-- TOC --><a name="api-design"></a>
### API design

The API endpoints are documented in the generated specification, but there are a few points to note on their usage:

<!-- TOC --><a name="catalogue"></a>
#### `/catalogue`

The metadata search endpoint specification lists all of the parameters that we wish to support, however some of them are ignored. We currently don't filter by asset type or allow paging through the results because there's so little data available. Additionally, the text search is very basic because we anticipated introducing a cataloguing system that might come with its own search functionality.

<!-- TOC --><a name="publishverify"></a>
#### `/publish/verify`
There was a requirement to publish multiple data assets from a pair of CSV files (one for datasets, and one for data services) that were exported from the agreed excel template, but these of course might have errors in them that needed to get back to the user. Additionally, we wanted the user to "preview" the metadata extracted from the files before publishing them. Therefore we created this endpoint that accepts the contents of two CSVs and returns the parsed contents in a format that could then be sent to `/publish`.

<!-- TOC --><a name="build-and-run"></a>
## Build and run

<!-- TOC --><a name="prerequisites"></a>
### Prerequisites

<!-- TOC --><a name="just-required"></a>
#### just (required)
We just [just](https://github.com/casey/just) for running project-specific commands (see the [justfile](justfile)). 

Install using `brew install just` if you're on macOS, otherwise there are more instructions [here](https://github.com/casey/just#packages).

<!-- TOC --><a name="poetry-required"></a>
#### Poetry (required)
For python version and dependency management.

Installation instructions are [here](https://python-poetry.org/docs/#installing-with-the-official-installer).

<!-- TOC --><a name="docker-required"></a>
#### docker (required)
For running the local API and [Fuseki](https://jena.apache.org/documentation/fuseki2/) SPARQL server.

Installation instructions for macOS [here](https://docs.docker.com/desktop/install/mac-install/).

<!-- TOC --><a name="yq-optional"></a>
#### yq (optional)
A "lightweight and portable command-line YAML processor". 

We're using FastAPI to generate the OpenAPI spec in JSON format, and `yq` to convert it to yaml format.

Installation instructions are [here](https://github.com/mikefarah/yq/#install) (hopefully just `brew install yq`).

<!-- TOC --><a name="usage"></a>
### Usage

<!-- TOC --><a name="initial-setup"></a>
#### Initial setup
-  Install the prerequisites listed above.
-  Install the python dependencies for the API: `cd api && poetry install`.
-  Install the `pre-commit` hooks if you're planning on contributing to this repository: `just setup-hooks`

<!-- TOC --><a name="environment-variables"></a>
##### Environment variables
You'll need to set up a `.env` file by copying `.env.example` and adding the following variables:

* `OPS_API_KEY` is the key that you need to pass to endpoints that require super-admin permissions, such as those that manage users. Generate one with `openssl rand -hex 32`.
* `JWT_AUD` is the audience claim for the gov.uk single sign on, which is needed to decode user JWT tokens. If you've logged in to the front end via SSO, you can find this keyed under `aud` within the response.

<!-- TOC --><a name="api"></a>
#### API
Start the API and Fuseki database with `just run`.

You should then be able to run `curl http://localhost:8000/catalogue` to list the data assets in the triplestore.

The OpenAPI/Swagger documentation will be served at: http://localhost:8000/docs.

<!-- TOC --><a name="triplestore"></a>
#### Triplestore 
Fuseki will be initialised with the data in `fuseki/data` pre-loaded in the database.

The Fuseki web UI will be served at http://localhost:3030, the username is `admin` and the password is printed in the Docker compose logs.
