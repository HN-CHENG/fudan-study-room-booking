from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.user import User
from app.models.study_room import StudyRoom, Seat
from app.models.booking import Booking 