from app import db
from datetime import datetime, timedelta

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, checked_in, cancelled, completed, expired
    booking_time = db.Column(db.DateTime, default=datetime.now)
    checkin_time = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, user_id, seat_id, start_time, end_time):
        self.user_id = user_id
        self.seat_id = seat_id
        self.start_time = start_time
        self.end_time = end_time
        
    def check_in(self):
        self.status = 'checked_in'
        self.checkin_time = datetime.now()
        db.session.commit()
        
    def cancel(self):
        self.status = 'cancelled'
        db.session.commit()
        
    def complete(self):
        self.status = 'completed'
        db.session.commit()
        
    def expire(self):
        self.status = 'expired'
        db.session.commit()
        
    def is_active(self):
        now = datetime.now()
        return self.status in ['confirmed', 'checked_in'] and self.start_time <= now <= self.end_time
        
    def can_check_in(self):
        now = datetime.now()
        # 可以在预约时间前15分钟开始签到
        return self.status == 'confirmed' and now >= (self.start_time - timedelta(minutes=15)) and now <= (self.start_time + timedelta(minutes=15))
        
    def is_expired(self):
        now = datetime.now()
        # 超过预约开始时间15分钟未签到，视为过期
        return self.status == 'confirmed' and now > (self.start_time + timedelta(minutes=15))
        
    def time_until_start(self):
        now = datetime.now()
        if now >= self.start_time:
            return timedelta(0)
        return self.start_time - now
        
    def time_until_expire(self):
        expire_time = self.start_time + timedelta(minutes=15)
        now = datetime.now()
        if now >= expire_time:
            return timedelta(0)
        return expire_time - now
        
    def remaining_time(self):
        now = datetime.now()
        if now >= self.end_time:
            return timedelta(0)
        return self.end_time - now
        
    def __repr__(self):
        return f'<Booking {self.id} for User {self.user_id} on Seat {self.seat_id}>' 