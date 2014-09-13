#!/bin/bash

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTDIR

./test_simple_system_config.py && \
./test_complex_system_config.py && \
./test_system_params.py && \
./test_template_files.py && \
./test_same_file_param_subst.py && \
./test_plans_in_subdirs.py && \
./test_files_param_subst.py && \
./test_inline_ansible_plan.py && \
./test_local_connect_for_testing.py && \
./test_files_with_parameters.py && \
./test_run_selectors.py

# NOT WORKING:
#
#   ./test_hashskip.py
#