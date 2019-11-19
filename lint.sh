#!/bin/bash

isort lemma_content_atlas/**/*.py
flake8 lemma_content_atlas
black lemma_content_atlas
