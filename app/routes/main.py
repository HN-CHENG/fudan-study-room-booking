from flask import Blueprint, render_template, request, jsonify
from app.models import StudyRoom, Seat
from flask_login import current_user
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # 获取可用自习室
    now = datetime.now()
    active_rooms = StudyRoom.query.filter_by(is_active=True).all()
    
    # 获取当前可用的自习室
    available_rooms = [room for room in active_rooms if room.is_open()]
    
    # 查找有空座的自习室数量
    rooms_with_seats = []
    for room in available_rooms:
        available_seats = 0
        for seat in room.seats:
            if seat.is_active and seat.is_available(now, now + timedelta(hours=1)):
                available_seats += 1
        if available_seats > 0:
            rooms_with_seats.append({
                'id': room.id,
                'name': room.name,
                'building': room.building,
                'available_seats': available_seats,
                'total_seats': room.seats.filter_by(is_active=True).count()
            })
    
    return render_template('index.html', 
                          rooms=rooms_with_seats,
                          total_rooms=len(available_rooms),
                          is_authenticated=current_user.is_authenticated)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/api/rooms')
def get_rooms():
    """获取所有可用自习室的API"""
    rooms = StudyRoom.query.filter_by(is_active=True).all()
    result = [{
        'id': room.id,
        'name': room.name,
        'building': room.building,
        'floor': room.floor,
        'is_open': room.is_open(),
        'open_time': room.open_time.strftime('%H:%M') if not room.is_24h else '全天',
        'close_time': room.close_time.strftime('%H:%M') if not room.is_24h else '全天',
        'is_24h': room.is_24h
    } for room in rooms]
    
    return jsonify(result)

@bp.route('/api/room/<int:room_id>/seats')
def get_room_seats(room_id):
    """获取自习室座位的API"""
    room = StudyRoom.query.get_or_404(room_id)
    
    # 获取请求的时间范围
    start_time_str = request.args.get('start_time')
    hours = int(request.args.get('hours', 1))
    
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
    else:
        # 默认从当前时间开始
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        if datetime.now().minute >= 30:
            start_time += timedelta(hours=1)
    
    end_time = start_time + timedelta(hours=hours)
    
    # 获取座位状态
    seats = []
    for seat in room.seats.filter_by(is_active=True).all():
        seats.append({
            'id': seat.id,
            'seat_number': seat.seat_number,
            'has_power_outlet': seat.has_power_outlet,
            'is_available': seat.is_available(start_time, end_time)
        })
    
    room_data = {
        'id': room.id,
        'name': room.name,
        'building': room.building,
        'floor': room.floor,
        'seats': seats
    }
    
    return jsonify(room_data) 