from app.db.sparql import assets_db
from rdflib.term import URIRef
from rdflib import Namespace

FREQ = Namespace("http://purl.org/cld/freq/")


class ReferenceDataValidator:
    _media_types = None
    _update_frequencies = None

    def _init_media_types(self):
        self._media_types = {}
        query_results = assets_db.run_query("all_mimetypes")
        for r in query_results:
            self._media_types[r["mimetypeLabel"]] = URIRef(r["mimetypeUri"])
        return

    def _init_update_frequencies(self):
        query_results = assets_db.run_query("all_update_frequencies")
        self._update_frequencies = {URIRef(r["updateFrequency"]) for r in query_results}
        return

    def media_type_uri(self, media_type_str):
        if self._media_types is None:
            self._init_media_types()
        try:
            return self._media_types[media_type_str]
        except:
            raise ValueError(f"Invalid media type: {media_type_str}")

    def update_freq_url(self, update_freq_notation):
        """For update frequency such as 'freq:quarterly', convert to URI and check it's ok.
        At present this is what we get from the spreadsheet, though at some point we may want
        to support a string label like 'Quarterly'"""
        if self._update_frequencies is None:
            self._init_update_frequencies()
        try:
            suffix = update_freq_notation.split("freq:")[1]
        except:
            raise ValueError(
                f"Frequency should be of the format freq:<frequency> - {update_freq_notation}"
            )
        uri = FREQ[suffix]
        if uri in self._update_frequencies:
            return uri
        else:
            raise ValueError(f"Invalid update frequency: {update_freq_notation}")

    def theme_uri(self, theme_uri_str):
        """Since we can't get a list of themes from the DB, just validate themes by checking
        that they have a label. Not ideal - at some point we'll need to add a type to the themes
        so we can supply a list of valid options"""
        theme_as_uri = URIRef(theme_uri_str)
        query_results = assets_db.run_query("get_label", subject=theme_as_uri)
        if len(query_results) == 0:
            raise ValueError(f"Invalid theme: {theme_uri_str}")
        return theme_as_uri


reference_data_validator = ReferenceDataValidator()
