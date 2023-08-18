import csv
import io
from tempfile import SpooledTemporaryFile
from app import model as m
from app import utils
from itertools import groupby
from datetime import datetime


class FileContentException(Exception):
    "Raised when the file content is invalid"

    def __init__(self, msg, value=None, error=None):
        self.message = msg
        self.value = value
        self.error = error

    def __str__(self):
        msg = self.message
        if self.value:
            msg = msg + f" - Error with input value {self.value}"
        if self.error:
            msg = msg + f": {self.error}"
        return msg


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
}
date_fields = ["issued", "modified", "created"]

list_fields = ["alternativeTitle", "theme", "keyword", "relatedAssets", "servesData"]


def _to_row_dicts(csv_file: SpooledTemporaryFile):
    temp_file_text = io.TextIOWrapper(csv_file, encoding="utf-8")
    reader = csv.reader(temp_file_text)
    _ = reader.__next__()
    headers = reader.__next__()
    rows = [r for r in reader]
    rowdicts = [{h: r[idx] for idx, h in enumerate(headers)} for r in rows]
    return rowdicts


def _cleanup_csv_row_dict(row_dict):
    row_dict = {k: v for k, v in row_dict.items() if v != ""}
    for date_field in date_fields:
        if date_field in row_dict:
            row_dict[date_field] = datetime.fromisoformat(row_dict[date_field])
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
    dist_detail_dict = _cleanup_csv_row_dict(dist_detail_dict)
    try:
        return m.DistributionSummary.model_validate(dist_detail_dict)
    except Exception as e:
        raise FileContentException("Could not parse distribution", error=e)


def _add_contact_point(row_dict):
    try:
        contact_point = m.ContactPoint.model_validate(
            {
                "name": row_dict["contactPoint_contactName"],
                "email": row_dict["contactPoint_email"],
            }
        )
    except Exception as e:
        raise FileContentException("Could not parse contact point", error=e)
    return {
        **{
            k: v
            for k, v in row_dict.items()
            if k not in ["contactPoint_contactName", "contactPoint_email"]
        },
        "contactPoint": contact_point,
    }


def _aggregate_distributions(row_dicts):
    out = []
    for _, rows in groupby(row_dicts, lambda r: r["identifier"]):
        ds_rows = [utils.remove_keys(r, distribution_headers) for r in rows]
        if not all(r == ds_rows[0] for r in ds_rows):
            raise FileContentException(
                "Rows for the same, dataset should be identical apart from distribution",
                value=ds_rows,
            )
        else:
            out.append(
                {**ds_rows[0], "distributions": [_distribution(r) for r in row_dicts]}
            )
    return out


def parse_dataservice_file(csv_file: SpooledTemporaryFile):
    rows = _to_row_dicts(csv_file)
    rows = [{**row, "type": "DataService"} for row in rows]
    assets = [_cleanup_csv_row_dict(r) for r in rows]
    assets = [_add_contact_point(a) for a in assets]
    try:
        return [m.CreateDataServiceBody.model_validate(a) for a in assets]
    except Exception as e:
        raise FileContentException("Could not parse data service file", error=e)


def parse_dataset_file(csv_file: SpooledTemporaryFile):
    rows = _to_row_dicts(csv_file)
    rows = [{**row, "type": "Dataset"} for row in rows]
    assets = _aggregate_distributions(rows)
    assets = [_cleanup_csv_row_dict(r) for r in assets]
    assets = [_add_contact_point(a) for a in assets]
    try:
        return [m.CreateDatasetBody.model_validate(r) for r in assets]
    except Exception as e:
        raise FileContentException("Could not parse data service file", error=e)
