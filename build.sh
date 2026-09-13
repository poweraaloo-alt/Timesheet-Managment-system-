#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Import the original SQLite data into PostgreSQL on the first deployment only.
# The import is skipped automatically once the hosted database already contains users.
if [[ -n "${DATABASE_URL:-}" && -f "db.sqlite3" ]]; then
    USER_COUNT=$(python manage.py shell -c "from timesheet_app.models import CustomUser; print(CustomUser.objects.count())" | tail -n 1)

    if [[ "$USER_COUNT" == "0" ]]; then
        echo "Hosted PostgreSQL is empty. Importing data from db.sqlite3..."

        DATABASE_URL="" python manage.py dumpdata \
            --all \
            --natural-foreign \
            --natural-primary \
            --indent 2 \
            timesheet_app auth.Group \
            > /tmp/timesheet_data.json

        python manage.py loaddata /tmp/timesheet_data.json

        python manage.py shell <<'PY'
from django.apps import apps
from django.core.management.color import no_style
from django.db import connection

models = list(apps.get_app_config("timesheet_app").get_models())
statements = connection.ops.sequence_reset_sql(no_style(), models)

with connection.cursor() as cursor:
    for statement in statements:
        cursor.execute(statement)

print("PostgreSQL sequences reset.")
PY

        rm -f /tmp/timesheet_data.json
        echo "Original SQLite data imported successfully."
    else
        echo "Hosted PostgreSQL already contains users. Skipping SQLite import."
    fi
fi
