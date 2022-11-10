from fafscripts import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class CatalogueCategoryChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"CatalogueCategoryChoice('{self.name}')"


class DatabaseID(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"DatabaseID('{self.name}')"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))

    def __repr__(self):
        return f"Event('{self.name}')"


class EventCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer)
    price_discounted = db.Column(db.Integer)
    eventive_tags = db.Column(db.String(250))
    wordpress_post_type = db.Column(db.String(25))

    def __repr__(self):
        return f"EventCategory('{self.name}')"


class EventiveTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    eventive_id = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"Event('{self.name}')"


class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventive_id = db.Column(db.String(30))
    name = db.Column(db.String(100), nullable=False)
    programmes = db.Column(db.String(100), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    seq = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Film('{self.name}')"


class FilmProgramme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notion_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    seq = db.Column(db.String(50))
    unballoted = db.Column(db.Boolean)
    age_limit = db.Column(db.Integer)
    eventive_tags = db.Column(db.String(250))
    template_event_id = db.Column(db.String(50))

    def __repr__(self):
        return f"FilmProgramme('{self.name}')"


class GeoblockOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    country_codes = db.Column(db.String(50))


class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(75), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))

    def __repr__(self):
        return f"Guest('{self.name}')"


class GuestCategoryChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"GuestCategoryChoice('{self.name}')"


class PassBucket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eventive_id = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    print_title = db.Column(db.String(50))
    third_line = db.Column(db.String(50))
    print = db.Column(db.Boolean)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(30))

    def __repr__(self):
        return f"PassBucket('{self.name}')"


class ReimbursementsChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"ReimbursementsChoice('{self.name}')"


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"Room('{self.name}')"


class User (db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False,
                           default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    # posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notion_id = db.Column(db.String(50), nullable=False)
    notion_url = db.Column(db.String(200), nullable=False)
    eventive_id = db.Column(db.String(50))

    def __repr__(self):
        return f"Venue('{self.name}')"
