#!/bin/bash

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTDIR

echo "RUNNING: test_simple_system_config.py"
$SCRIPTDIR/test_simple_system_config.py

echo "RUNNING: test_complex_system_config.py"
$SCRIPTDIR/test_complex_system_config.py 

echo "RUNNING: test_system_params.py"
$SCRIPTDIR/test_system_params.py 

echo "RUNNING: test_template_files.py"
$SCRIPTDIR/test_template_files.py 

echo "RUNNING: test_same_file_param_subst.py"
$SCRIPTDIR/test_same_file_param_subst.py 

echo "RUNNING: test_plans_in_subdirs.py"
$SCRIPTDIR/test_plans_in_subdirs.py 

echo "RUNNING: test_files_param_subst.py"
$SCRIPTDIR/test_files_param_subst.py 

echo "RUNNING: test_inline_ansible_plan.py"
$SCRIPTDIR/test_inline_ansible_plan.py 

echo "RUNNING: test_local_connect_for_testing.py"
$SCRIPTDIR/test_local_connect_for_testing.py 

echo "RUNNING: test_files_with_parameters.py"
$SCRIPTDIR/test_files_with_parameters.py 

echo "RUNNING: test_run_selectors.py"
$SCRIPTDIR/test_run_selectors.py

echo "RUNNING: test_hashskip.py"
$SCRIPTDIR/test_hashskip.py

