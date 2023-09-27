from pydantic import BaseModel, ValidationError, Field
from enum import Enum
from typing import List, Dict, Any, Literal


class errorScope(str, Enum):
    file = "FILE"
    asset = "ASSET"
    field = "FIELD"
    batch = "BATCH"


class ErrorInfo(BaseModel):
    message: str
    location: str = Field(description="The file, asset, or field that caused the error")
    extras: Dict | None = Field(default=None, description="Extra info about the error")
    scope: errorScope


class FileErrorInfo(ErrorInfo):
    "An error parsing the whole file"
    scope: Literal[errorScope.file]


class FieldValidationErrorInfo(ErrorInfo):
    "Error indicating that a single value is not valid"
    scope: Literal[errorScope.field]
    value: Any = Field(description="The value that caused the error")


class AssetValidationErrorInfo(ErrorInfo):
    "Error indicating that a single asset is not valid"
    scope: Literal[errorScope.asset]
    sub_errors: List[FieldValidationErrorInfo] | None = Field(
        default=[],
        description="A list of the errors with individual fields within the asset",
    )


class ErrorContainer:
    __errors: List[ErrorInfo]

    def __init__(self):
        self.__errors = []

    def add(self, error_or_errors):
        if isinstance(error_or_errors, list):
            for e in error_or_errors:
                self.add(e)
        elif error_or_errors is not None:
            self.__errors.append(error_or_errors)

    def has_error(self):
        return self.__errors != []

    def __model_validate_error(_, err):
        match err["scope"]:
            case errorScope.file:
                return FileErrorInfo.model_validate(err)
            case errorScope.asset:
                return AssetValidationErrorInfo.model_validate(err)
            case errorScope.field:
                return FieldValidationErrorInfo.model_validate(err)

    def errors(self):
        return [self.__model_validate_error(e) for e in self.__errors]


def validation_error_info(e: ValidationError) -> List[ErrorInfo]:
    output = []
    for err in e.errors():
        field_name = ".".join([str(field) for field in err["loc"]])
        if err["type"] == "enum":
            info = {
                "message": "Invalid option for field",
                "extras": {"valid_options": err["ctx"]["expected"]},
            }
        else:
            info = {"message": err["msg"]}

        output.append(
            {
                "scope": errorScope.field,
                "location": field_name,
                "value": "" if err["type"] == "missing" else err["input"],
                **info,
            }
        )
    return output


def db_validation_error_info(field_name, value) -> ErrorInfo:
    return {
        "scope": errorScope.field,
        "location": field_name,
        "value": value,
        "message": "Invalid option - no matching record found in database",
    }


def dicts_diff(list_of_dicts):
    "For a list of dictionaries that should be identical, give a summary of what's mismatched"
    aggregated = {}
    for d in list_of_dicts:
        for k, v in d.items():
            if k not in aggregated:
                aggregated[k] = set()
            aggregated[k].add(v)
    return {k: v for k, v in aggregated.items() if len(v) > 1}
