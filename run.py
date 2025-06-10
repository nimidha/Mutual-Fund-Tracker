# run.py
from database import create_users_table, create_funds_table

create_users_table()
create_funds_table()

from app import create_app
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
