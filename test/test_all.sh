#!/bin/bash

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTDIR

./test_simple_system_config.py && \
./test_complex_system_config.py && \
./test_system_params.py && \
./test_template_files.py
