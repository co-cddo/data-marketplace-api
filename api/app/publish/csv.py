import csv
import io
from tempfile import SpooledTemporaryFile
from app import model as m
from app import utils
from itertools import groupby
from datetime import datetime
from pydantic import ValidationError
from app.publish.errors import (
    validation_error_info,
    db_validation_error_info,
    ErrorContainer,
    errorScope,
    dicts_diff,
)
from app.db.reference_data import reference_data_validator


expected_headers = {
    m.assetType.dataset: [
        "title",
        "alternativeTitle",
        "summary",
        "description",
        "keyword",
        "theme",
        "contactPoint_contactName",
        "contactPoint_email",
        "publisher",
        "creator",
        "version",
        "issued",
        "modified",
        "created",
        "updateFrequency",
        "licence",
        "accessRights",
        "securityClassification",
        "identifier",
        "relatedResource",
        "distribution_title",
        "distribution_accessService",
        "distribution_identifier",
        "distribution_modified",
        "distribution_issued",
        "distribution_licence",
        "distribution_byteSize",
        "distribution_mediaType",
    ],
    m.assetType.service: [
        "title",
        "alternativeTitle",
        "summary",
        "description",
        "keyword",
        "theme",
        "contactPoint_contactName",
        "contactPoint_email",
        "publisher",
        "creator",
        "version",
        "issued",
        "modified",
        "created",
        "licence",
        "accessRights",
        "securityClassification",
        "identifier",
        "relatedResource",
        "serviceType",
        "serviceStatus",
        "endpointURL",
        "endpointDescription",
        "servesDataset",
    ],
}

distribution_headers = [
    "distribution_title",
    "distribution_accessService",
    "distribution_identifier",
    "distribution_modified",
    "distribution_issued",
    "distribution_licence",
    "distribution_byteSize",
    "distribution_mediaType",
]

keys_to_rename = {
    "creator": "creatorID",
    "publisher": "organisationID",
    "relatedResource": "relatedAssets",
    "identifier": "externalIdentifier",
    "servesData": "servesDataset",
}
date_fields = ["issued", "modified", "created"]

list_fields = [
    "alternativeTitle",
    "theme",
    "keyword",
    "relatedAssets",
    "servesDataset",
    "creatorID",
]


def _to_row_dicts(csv_file: SpooledTemporaryFile, asset_type: m.assetType):
    temp_file_text = io.TextIOWrapper(csv_file, encoding="utf-8")
    reader = csv.reader(temp_file_text)
    # Discard the extra header row that shows whether each field is optional/recommended/mandatory:
    _ = reader.__next__()
    headers = reader.__next__()
    if headers != expected_headers[asset_type]:
        return [], {
            "message": "Incorrect headers in CSV",
            "location": f"{asset_type} file",
            "scope": errorScope.file,
            "extras": {
                "missing_cols": [
                    x for x in expected_headers[asset_type] if x not in headers
                ],
                "invalid_cols": [
                    x for x in headers if x not in expected_headers[asset_type]
                ],
            },
        }
    rows = [r for r in reader]
    rowdicts = [{h: r[idx] for idx, h in enumerate(headers)} for r in rows]
    return rowdicts, None


def _cleanup_csv_row_dict(row_dict):
    row_dict = {k: v for k, v in row_dict.items() if v != ""}
    for date_field in date_fields:
        if date_field in row_dict:
            try:
                row_dict[date_field] = datetime.fromisoformat(row_dict[date_field])
            except ValueError:
                pass  # this is OK as we're going to validate it anyway
    for old_key, new_key in keys_to_rename.items():
        if old_key in row_dict:
            row_dict[new_key] = row_dict[old_key]
            row_dict.pop(old_key)
    for f in list_fields:
        if f in row_dict:
            row_dict[f] = row_dict[f].split(",")
    return row_dict


def _distribution(row_dict):
    dist_detail_dict = {
        k.split("distribution_")[1]: row_dict[k] for k in distribution_headers
    }
    return _cleanup_csv_row_dict(dist_detail_dict)


def _add_contact_point(row_dict):
    return {
        **{
            k: v
            for k, v in row_dict.items()
            if k not in ["contactPoint_contactName", "contactPoint_email"]
        },
        "contactPoint": {
            "name": row_dict.get("contactPoint_contactName"),
            "email": row_dict.get("contactPoint_email"),
        },
    }


def _aggregate_distributions(row_dicts):
    data = []
    errors = []
    for assetID, rows in groupby(row_dicts, lambda r: r["identifier"]):
        ds_rows = [utils.remove_keys(r, distribution_headers) for r in rows]
        if not all(r == ds_rows[0] for r in ds_rows):
            errors.append(
                {
                    "scope": errorScope.asset,
                    "location": assetID,
                    "message": "Rows for different distributions of the same asset are not identical",
                    "extras": {"mismatched_values": dicts_diff(ds_rows)},
                }
            )
        else:
            data.append(
                {**ds_rows[0], "distributions": [_distribution(r) for r in row_dicts]}
            )
    return data, errors


def _lookup_ok(lookup_fn, value):
    "Return true if the lookup function returned something for the value"
    if value is None:
        return True
    try:
        return bool(lookup_fn(value))
    except ValueError:
        return False


def _validate_db_fields(asset):
    """Check that all fields referencing other entities in the database refer to one that exists,
    and return a list of errors for those that dont"""
    errors = []
    if not _lookup_ok(utils.lookup_organisation, asset["organisationID"]):
        errors.append(
            db_validation_error_info("organisationID", asset["organisationID"])
        )
    for c in asset["creatorID"]:
        if not _lookup_ok(utils.lookup_organisation, c):
            errors.append(db_validation_error_info("creatorID", c))
    if asset["type"] == m.assetType.dataset:
        for dist in asset["distributions"]:
            if not _lookup_ok(
                reference_data_validator.media_type_uri, dist["mediaType"]
            ):
                errors.append(
                    db_validation_error_info(
                        "distribution.mediaType", dist["mediaType"]
                    )
                )
        if not _lookup_ok(
            reference_data_validator.update_freq_url, asset["updateFrequency"]
        ):
            errors.append(
                db_validation_error_info("updateFrequency", asset["updateFrequency"])
            )
    for t in asset["theme"]:
        if not _lookup_ok(reference_data_validator.theme_uri, t):
            errors.append(db_validation_error_info("theme", t))
    return errors


def parse_input_file(
    error_ctx: ErrorContainer, csv_file: SpooledTemporaryFile, asset_type: m.assetType
):
    rows, error = _to_row_dicts(csv_file, asset_type)
    error_ctx.add(error)
    data = [{**row, "type": asset_type} for row in rows]
    if asset_type == m.assetType.dataset:
        data, errors = _aggregate_distributions(data)
        error_ctx.add(errors)
    data = [_cleanup_csv_row_dict(d) for d in data]
    data = [_add_contact_point(d) for d in data]

    model = (
        m.CreateDatasetBody
        if asset_type == m.assetType.dataset
        else m.CreateDataServiceBody
    )
    validated_data = []
    for d in data:
        validation_errors = _validate_db_fields(d)
        try:
            validated = model.model_validate(d)
        except ValidationError as e:
            validation_errors = validation_errors + validation_error_info(e)
        if validation_errors == []:
            validated_data.append(validated)
        else:
            error_ctx.add(
                {
                    "message": "Validation error for asset",
                    "location": d["externalIdentifier"]
                    if d["externalIdentifier"] is not None
                    else d["title"],
                    "scope": errorScope.asset,
                    "sub_errors": validation_errors,
                }
            )
    return validated_data


def parse_input_files(datasets_file=None, services_file=None):
    error_container = ErrorContainer()
    parsed_datasets = (
        parse_input_file(error_container, datasets_file, m.assetType.dataset)
        if datasets_file is not None
        else []
    )
    parsed_services = (
        parse_input_file(error_container, services_file, m.assetType.service)
        if services_file is not None
        else []
    )
    return {
        "errors": error_container.errors(),
        "data": parsed_datasets + parsed_services,
    }
