from app import db
from datetime import datetime, time

class StudyRoom(db.Model):
    __tablename__ = 'study_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    building = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    open_time = db.Column(db.Time, default=time(7, 0))  # 默认早7点开放
    close_time = db.Column(db.Time, default=time(22, 0))  # 默认晚10点关闭
    is_active = db.Column(db.Boolean, default=True)
    is_24h = db.Column(db.Boolean, default=False)  # 是否24小时开放
    verify_code = db.Column(db.String(10), nullable=True)  # 当日签到编码
    qr_code_path = db.Column(db.String(200), nullable=True)  # 二维码图片路径
    
    # 关联
    seats = db.relationship('Seat', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, building, floor, capacity, open_time=time(7, 0), close_time=time(22, 0), is_24h=False):
        self.name = name
        self.building = building
        self.floor = floor
        self.capacity = capacity
        self.open_time = open_time
        self.close_time = close_time
        self.is_24h = is_24h
        
    def is_open(self, current_time=None):
        if not self.is_active:
            return False
            
        if self.is_24h:
            return True
            
        if current_time is None:
            current_time = datetime.now().time()
            
        return self.open_time <= current_time <= self.close_time
        
    def update_verify_code(self, code, qr_path=None):
        self.verify_code = code
        if qr_path:
            self.qr_code_path = qr_path
        db.session.commit()
        
    def __repr__(self):
        return f'<StudyRoom {self.name}>'
        
        
class Seat(db.Model):
    __tablename__ = 'seats'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('study_rooms.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    has_power_outlet = db.Column(db.Boolean, default=False)  # 是否有电源插座
    is_active = db.Column(db.Boolean, default=True)
    
    # 关联
    bookings = db.relationship('Booking', backref='seat', lazy='dynamic')
    
    def __init__(self, room_id, seat_number, has_power_outlet=False):
        self.room_id = room_id
        self.seat_number = seat_number
        self.has_power_outlet = has_power_outlet
        
    def is_available(self, start_time, end_time):
        """检查指定时间段内座位是否可用"""
        from app.models.booking import Booking
        
        if not self.is_active:
            return False
            
        # 查找与请求时间段重叠的预约
        overlapping_bookings = Booking.query.filter(
            Booking.seat_id == self.id,
            Booking.end_time > start_time,
            Booking.start_time < end_time,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        
        return overlapping_bookings == 0
        
    def __repr__(self):
        return f'<Seat {self.seat_number} in Room {self.room_id}>' 