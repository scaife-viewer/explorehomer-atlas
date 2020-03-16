#!/bin/bash
isort -rc readhomer_atlas
black readhomer_atlas
flake8 readhomer_atlas
