#!/usr/bin/env bash
set -o errexit

# Install wkhtmltopdf and dependencies
apt-get update -y
apt-get install -y --no-install-recommends \
  wkhtmltopdf \
  xvfb \
  xfonts-75dpi \
  xfonts-base

# Install Python dependencies
pip install -r requirements.txt 