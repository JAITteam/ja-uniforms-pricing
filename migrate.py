from app import app, db
from models import StyleImage

with app.app_context():
    db.create_all()
    print("Tables created successfully!")

exit()