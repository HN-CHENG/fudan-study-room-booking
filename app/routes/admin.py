from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, StudyRoom, Seat, Booking
from datetime import datetime, timedelta
import random
import string
import qrcode
import os

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(view):
    """管理员权限验证装饰器"""
    @login_required
    def wrapped_view(**kwargs):
        if not current_user.is_admin:
            flash('您没有管理员权限', 'danger')
            return redirect(url_for('main.index'))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view

@bp.route('/')
@admin_required
def index():
    """管理员控制面板"""
    # 统计信息
    total_rooms = StudyRoom.query.filter_by(is_active=True).count()
    total_seats = Seat.query.filter_by(is_active=True).count()
    total_users = User.query.filter_by(is_admin=False).count()
    
    # 今日预约数据
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    today_bookings = Booking.query.filter(
        Booking.start_time >= today,
        Booking.start_time < tomorrow
    ).count()
    
    # 获取最近活跃的预约
    recent_bookings = Booking.query.order_by(Booking.booking_time.desc()).limit(10).all()
    
    return render_template('admin/index.html',
                          total_rooms=total_rooms,
                          total_seats=total_seats,
                          total_users=total_users,
                          today_bookings=today_bookings,
                          recent_bookings=recent_bookings)

@bp.route('/rooms')
@admin_required
def rooms():
    """自习室管理"""
    rooms = StudyRoom.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@bp.route('/room/add', methods=['GET', 'POST'])
@admin_required
def add_room():
    """添加自习室"""
    if request.method == 'POST':
        name = request.form['name']
        building = request.form['building']
        floor = int(request.form['floor'])
        capacity = int(request.form['capacity'])
        open_time_str = request.form['open_time']
        close_time_str = request.form['close_time']
        is_24h = 'is_24h' in request.form
        
        # 转换时间
        open_time = datetime.strptime(open_time_str, '%H:%M').time()
        close_time = datetime.strptime(close_time_str, '%H:%M').time()
        
        room = StudyRoom(
            name=name,
            building=building,
            floor=floor,
            capacity=capacity,
            open_time=open_time,
            close_time=close_time,
            is_24h=is_24h
        )
        
        db.session.add(room)
        db.session.commit()
        
        # 生成初始验证码
        generate_verify_code(room)
        
        flash('自习室添加成功', 'success')
        return redirect(url_for('admin.rooms'))
        
    return render_template('admin/add_room.html')

@bp.route('/room/<int:room_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_room(room_id):
    """编辑自习室"""
    room = StudyRoom.query.get_or_404(room_id)
    
    if request.method == 'POST':
        room.name = request.form['name']
        room.building = request.form['building']
        room.floor = int(request.form['floor'])
        room.capacity = int(request.form['capacity'])
        room.is_24h = 'is_24h' in request.form
        
        if not room.is_24h:
            open_time_str = request.form['open_time']
            close_time_str = request.form['close_time']
            room.open_time = datetime.strptime(open_time_str, '%H:%M').time()
            room.close_time = datetime.strptime(close_time_str, '%H:%M').time()
        
        room.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('自习室信息已更新', 'success')
        return redirect(url_for('admin.rooms'))
        
    return render_template('admin/edit_room.html', room=room)

@bp.route('/room/<int:room_id>/seats')
@admin_required
def room_seats(room_id):
    """查看自习室座位"""
    room = StudyRoom.query.get_or_404(room_id)
    seats = room.seats.all()
    return render_template('admin/room_seats.html', room=room, seats=seats)

@bp.route('/room/<int:room_id>/add_seats', methods=['GET', 'POST'])
@admin_required
def add_seats(room_id):
    """批量添加座位"""
    room = StudyRoom.query.get_or_404(room_id)
    
    if request.method == 'POST':
        start_num = int(request.form['start_num'])
        count = int(request.form['count'])
        has_power = 'has_power' in request.form
        
        for i in range(count):
            seat_number = f"{start_num + i}"
            seat = Seat(
                room_id=room.id,
                seat_number=seat_number,
                has_power_outlet=has_power
            )
            db.session.add(seat)
            
        db.session.commit()
        flash(f'成功添加 {count} 个座位', 'success')
        return redirect(url_for('admin.room_seats', room_id=room.id))
        
    return render_template('admin/add_seats.html', room=room)

@bp.route('/seat/<int:seat_id>/toggle', methods=['POST'])
@admin_required
def toggle_seat(seat_id):
    """启用/禁用座位"""
    seat = Seat.query.get_or_404(seat_id)
    seat.is_active = not seat.is_active
    db.session.commit()
    
    status = '启用' if seat.is_active else '禁用'
    flash(f'座位 {seat.seat_number} 已{status}', 'success')
    return redirect(url_for('admin.room_seats', room_id=seat.room_id))

@bp.route('/seat/<int:seat_id>/power', methods=['POST'])
@admin_required
def toggle_power(seat_id):
    """设置座位是否有电源"""
    seat = Seat.query.get_or_404(seat_id)
    seat.has_power_outlet = not seat.has_power_outlet
    db.session.commit()
    
    status = '有' if seat.has_power_outlet else '没有'
    flash(f'座位 {seat.seat_number} 已设置为{status}电源', 'success')
    return redirect(url_for('admin.room_seats', room_id=seat.room_id))

@bp.route('/bookings')
@admin_required
def bookings():
    """预约管理"""
    # 获取查询参数
    status = request.args.get('status')
    room_id = request.args.get('room_id')
    date_str = request.args.get('date')
    
    # 构建查询
    query = Booking.query
    
    if status:
        query = query.filter_by(status=status)
        
    if room_id:
        query = query.join(Seat).filter(Seat.room_id == room_id)
        
    if date_str:
        date = datetime.fromisoformat(date_str).date()
        next_date = date + timedelta(days=1)
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(next_date, datetime.min.time())
        query = query.filter(Booking.start_time >= start_datetime, Booking.start_time < end_datetime)
        
    # 获取所有自习室，用于筛选
    rooms = StudyRoom.query.all()
    
    # 执行查询
    bookings = query.order_by(Booking.start_time.desc()).all()
    
    return render_template('admin/bookings.html', 
                          bookings=bookings, 
                          rooms=rooms,
                          selected_room=room_id,
                          selected_status=status,
                          selected_date=date_str if date_str else datetime.now().date().isoformat())

@bp.route('/statistics')
@admin_required
def statistics():
    """使用统计"""
    # 获取时间范围
    period = request.args.get('period', 'week')
    
    if period == 'day':
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        title = '今日使用统计'
    elif period == 'week':
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now().weekday())
        title = '本周使用统计'
    elif period == 'month':
        today = datetime.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        title = '本月使用统计'
    else:
        # 默认为一周
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now().weekday())
        title = '本周使用统计'
        
    # 各状态预约数
    status_counts = db.session.query(
        Booking.status, 
        db.func.count(Booking.id)
    ).filter(
        Booking.start_time >= start_date
    ).group_by(Booking.status).all()
    
    status_data = {status: count for status, count in status_counts}
    
    # 各自习室使用情况
    room_usage = db.session.query(
        StudyRoom.name,
        db.func.count(Booking.id)
    ).join(Seat, Seat.id == Booking.seat_id
    ).join(StudyRoom, StudyRoom.id == Seat.room_id
    ).filter(
        Booking.start_time >= start_date
    ).group_by(StudyRoom.name).order_by(db.func.count(Booking.id).desc()).all()
    
    # 违约用户
    violation_users = User.query.filter(User.violation_count > 0).order_by(User.violation_count.desc()).limit(10).all()
    
    return render_template('admin/statistics.html',
                          title=title,
                          period=period,
                          status_data=status_data,
                          room_usage=room_usage,
                          violation_users=violation_users)

@bp.route('/verify_codes')
@admin_required
def verify_codes():
    """签到验证码管理"""
    rooms = StudyRoom.query.filter_by(is_active=True).all()
    return render_template('admin/verify_codes.html', rooms=rooms)

@bp.route('/generate_code/<int:room_id>', methods=['POST'])
@admin_required
def generate_code(room_id):
    """生成新的签到码"""
    room = StudyRoom.query.get_or_404(room_id)
    generate_verify_code(room)
    flash(f'已为 {room.name} 生成新的签到码: {room.verify_code}', 'success')
    return redirect(url_for('admin.verify_codes'))

def generate_verify_code(room):
    """生成签到验证码和二维码"""
    # 生成6位随机验证码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # 保存二维码图片
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 确保目录存在
    qr_dir = os.path.join('static', 'qr_codes')
    os.makedirs(qr_dir, exist_ok=True)
    
    # 保存图片
    file_path = os.path.join(qr_dir, f'room_{room.id}_{datetime.now().strftime("%Y%m%d")}.png')
    img.save(file_path)
    
    # 更新自习室验证码
    room.update_verify_code(code, file_path)
    
    return code 