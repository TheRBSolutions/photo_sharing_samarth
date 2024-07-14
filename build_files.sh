#!/bin/bash

# Ensure pip is installed
python3.9 -m ensurepip --upgrade

# Install and upgrade pip, setuptools, and wheel
python3.9 -m pip install --upgrade pip setuptools wheel

# Install distutils
python3.9 -m pip install distutils

# Install the project dependencies
python3.9 -m pip install -r requirements.txt

# Collect static files
python3.9 manage.py collectstatic --noinput