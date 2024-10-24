#! /usr/bin/env sh
set -e


# Let the DB start
python3 /code/app/db/backend_pre_start.py

# database migrations
alembic upgrade head

# load initial data
python3 /code/app/db/initial_data.py

echo "Finished API Pre-start"
