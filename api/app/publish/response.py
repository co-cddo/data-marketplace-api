# TODO rename this - it's not just responses!
from pydantic import BaseModel
from app import model as m
from enum import Enum
from typing import List
import app.publish.errors as err


class PostResponseBody(BaseModel):
    errors: List[err.ErrorInfo]

    def ok(self):
        return self.errors != []


class CreateAssetsRequestBody(BaseModel):
    data: List[m.CreateDatasetBody | m.CreateDataServiceBody]


class ParseFilesResponseBody(CreateAssetsRequestBody, PostResponseBody):
    errors: List[
        err.FileErrorInfo | err.AssetValidationErrorInfo | err.FieldValidationErrorInfo
    ]


class CreateAssetsResponseBody(PostResponseBody):
    data: List[m.DatasetResponse | m.DataServiceResponse]


def format_response(response_dict):
    errors = response_dict.get("errors", [])
    data = response_dict.get("data", [])
    return ParseFilesResponseBody.model_validate(
        {
            "errors": errors,
            "data": data,
        }
    )
