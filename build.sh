#!/usr/bin/env bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
psql -a -d $DATABASE_URL -f database.sql
make install