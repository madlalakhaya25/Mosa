from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'

def user_exists_in_database(user_id):
    # Query the database for the user
    user = User.query.filter_by(id=user_id).first()
    # Return True if the user exists, False otherwise
    return user is not None
