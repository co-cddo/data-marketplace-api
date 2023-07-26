#!/bin/bash

JENA_VERSION=4.9.0

SCRIPT=$(readlink -f $0)
THIS_SCRIPT_DIR=`dirname $SCRIPT`

if [ -d "${THIS_SCRIPT_DIR}/fuseki" ]; then
    echo -e "\n\033[32mFound apache-jena-fuseki is already installed in ${THIS_SCRIPT_DIR}\033[0m\n";
else
    echo -e "\n\033[31mapache-jena-fuseki not found in ${THIS_SCRIPT_DIR}\033[0m\n"
    echo "downloading Jena Fuseki distribution..."
    wget -P $THIS_SCRIPT_DIR "http://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${JENA_VERSION}.tar.gz"
    echo "unpacking Jena Fuseki distribution.../n"
    tar -C ${THIS_SCRIPT_DIR} -xvzf "${THIS_SCRIPT_DIR}/apache-jena-fuseki-${JENA_VERSION}.tar.gz"
    rm "${THIS_SCRIPT_DIR}/apache-jena-fuseki-${JENA_VERSION}.tar.gz"
    ln -s "${THIS_SCRIPT_DIR}/apache-jena-fuseki-${JENA_VERSION}" "${THIS_SCRIPT_DIR}/fuseki"
    chmod +x "${THIS_SCRIPT_DIR}/fuseki/fuseki-server"
    echo -e "\n\033[32mApache-jena-fuseki installed into ${THIS_SCRIPT_DIR}/fuseki\033[0m\n"
fi
