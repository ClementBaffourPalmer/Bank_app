#!/usr/bin/env bash
# Controlled Render pre-deploy / release step.
# Run migrations once here. Do not also run migrate in the start command.
set -euo pipefail
python manage.py migrate --noinput
python manage.py createcachetable
