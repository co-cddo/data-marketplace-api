FROM secoresearch/fuseki

USER root
RUN apt-get install -qq curl
USER 9008

COPY --chown=9008 data /tmp/data
COPY assembler.ttl /fuseki-base/configuration/assembler.ttl

RUN cat /tmp/data/*.ttl > /tmp/data.ttl

RUN $TDBLOADER --graph=http://marketplace.cddo.gov.uk/graph/assets /tmp/data.ttl 
RUN $TEXTINDEXER 
RUN $TDBSTATS --graph urn:x-arq:UnionGraph > /tmp/stats.opt
RUN mv /tmp/stats.opt /fuseki-base/databases/tdb/