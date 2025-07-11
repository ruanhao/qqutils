#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Description:

# rm -rf dist; python -m build . && twine upload -u ruanhao dist/*

set -o errexit

# tag=`date "+%Y%m%d%H%M%S"`
# pytest --html=report-$tag.html --self-contained-html
# pytest -s tests/test_stringutils.py::test_print_html
pytest -s

tempdir="$(mktemp -d)"
file "$tempdir"
# Must prepare $HOME/.pypirc with API token:
# [pypi]
#   username = __token__
#   password = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

python -m build --sdist --wheel --outdir "$tempdir"
if [[ -n $1 ]]; then
    twine upload $tempdir/*
    # twine upload --repository-url $1 $tempdir/*
    exit 0
fi
