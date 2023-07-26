FROM secoresearch/fuseki

COPY --chown=9008 data /tmp/data
COPY assembler.ttl /fuseki-base/configuration/assembler.ttl

RUN cat /tmp/data/*.ttl > /tmp/data.ttl

RUN $TDBLOADER --graph=http://dev.data-marketplace.gov.uk/graph/catalogue /tmp/data.ttl 
RUN $TEXTINDEXER 
RUN $TDBSTATS --graph urn:x-arq:UnionGraph > /tmp/stats.opt
RUN mv /tmp/stats.opt /fuseki-base/databases/tdb/