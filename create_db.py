from flatterer import app, db
from flatterer.models import User

db.create_all()

if app.config['DATABASE_TYPE'] == 'dev':
    u = User('johnsdea', 'Dean', 'password', admin=True)
    db.session.add(u)
    db.session.commit()
