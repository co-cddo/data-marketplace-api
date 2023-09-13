from SPARQLWrapper import SPARQLWrapper, JSON, POST
from datetime import datetime
from app import config
from string import Template
from rdflib.namespace import XSD


class Connection:
    def __init__(self, query_url=None, update_url=None, query_template_dir="queries"):
        self.query_dir = query_template_dir
        if query_url:
            self.reader = SPARQLWrapper(query_url)
            self.reader.setReturnFormat(JSON)
        if update_url:
            self.writer = SPARQLWrapper(update_url)
            self.writer.setReturnFormat(JSON)
            self.writer.method = POST

    def _prep_query(self, query_file_name, bindings={}):
        for k, v in bindings.items():
            if isinstance(v, list):
                bindings[k] = " ".join(v)
        with open(f"{self.query_dir}/{query_file_name}.sparql", "r") as f:
            template = Template(f.read())
        return template.substitute(bindings)

    @staticmethod
    def _query_result_to_dict(result):
        d = {}
        for k, v in result.items():
            if v.get("datatype") == str(XSD["date"]):
                d[k] = datetime.fromisoformat(v["value"])
            else:
                d[k] = v["value"]
        return d

    def run_update(self, query_name, **bindings):
        assert self.writer, f"No writer configured for {self.graph}"
        q = self._prep_query(query_name, bindings)
        self.writer.setQuery(q)
        return self.writer.queryAndConvert()

    def run_query(self, query_name, **bindings):
        assert self.reader, f"No reader configured for {self.graph}"
        q = self._prep_query(query_name, bindings)
        self.reader.setQuery(q)
        results = self.reader.queryAndConvert()["results"]["bindings"]
        return [self._query_result_to_dict(r) for r in results]


assets_db = Connection(
    query_url=config.QUERY_URL,
    update_url=config.UPDATE_URL,
    query_template_dir="queries",
)

users_db = Connection(
    query_url=config.QUERY_URL,
    update_url=config.UPDATE_URL,
    query_template_dir="queries",
)

shares_db = Connection(
    query_url=config.QUERY_URL,
    update_url=config.UPDATE_URL,
    query_template_dir="queries/shares/",
)
