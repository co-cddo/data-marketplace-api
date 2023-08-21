from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
from . import config
from string import Template
from itertools import groupby
from rdflib.namespace import XSD


sparql_reader = SPARQLWrapper(config.QUERY_URL)

sparql_reader.setReturnFormat(JSON)


def _prep_query(query_file_name, bindings):
    for k, v in bindings.items():
        if isinstance(v, list):
            bindings[k] = " ".join(v)
    with open(f"queries/{query_file_name}", "r") as f:
        template = Template(f.read())
    return template.substitute(bindings)


def _query_result_to_dict(result):
    d = {}
    for k, v in result.items():
        if v.get("datatype") == str(XSD["date"]):
            d[k] = datetime.fromisoformat(v["value"])
        else:
            d[k] = v["value"]
    return d


def run_query(query_file_name, **bindings):
    q = _prep_query(query_file_name, bindings)
    sparql_reader.setQuery(q)
    results = sparql_reader.queryAndConvert()["results"]["bindings"]
    return [_query_result_to_dict(r) for r in results]


def _aggregate_results(result_dicts):
    """Assuming all results relate to a single item, aggregate them to include a list of values for
    any key with multiple values"""
    match len(result_dicts):
        case 0:
            return {}
        case 1:
            return result_dicts[0]
        case _:
            out = {}
            for r in result_dicts:
                for k, v in r.items():
                    if k not in out:
                        out[k] = v
                    elif out[k] != v:
                        if not isinstance(out[k], set):
                            out[k] = {out[k]}
                        out[k].add(v)
            return out


def aggregate_query_results_by_key(results, group_key="resourceUri"):
    """Groups the result by given key and aggregates the groups into a single dictionary for each"""
    return [
        _aggregate_results(list(results_for_resource))
        for _, results_for_resource in groupby(results, lambda r: r[group_key])
    ]
