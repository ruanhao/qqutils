#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Description:

# rm -rf dist; python -m build . && twine upload -u ruanhao dist/*

tempdir="$(mktemp -d)"
file "$tempdir"
# Must prepare $HOME/.pypirc with API token:
# [pypi]
#   username = __token__
#   password = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
python setup.py sdist -d "$tempdir" bdist_wheel -d "$tempdir" && twine upload $tempdir/*
