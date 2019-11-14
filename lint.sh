#!/bin/bash

isort readhomer_atlas/**/*.py
flake8 readhomer_atlas
black readhomer_atlas
