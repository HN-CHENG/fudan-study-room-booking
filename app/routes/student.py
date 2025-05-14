from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import StudyRoom, Seat, Booking
from datetime import datetime, timedelta

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/bookings')
@login_required
def bookings():
    """查看用户的所有预约"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 获取今天及以后的预约
    active_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.end_time >= today,
        Booking.status.in_(['confirmed', 'checked_in'])
    ).order_by(Booking.start_time).all()
    
    # 获取历史预约（最近30天内的）
    history_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.end_time < today,
        Booking.start_time >= today - timedelta(days=30)
    ).order_by(Booking.start_time.desc()).all()
    
    return render_template('student/bookings.html', 
                          active_bookings=active_bookings,
                          history_bookings=history_bookings)

@bp.route('/search')
@login_required
def search():
    """搜索可用座位"""
    # 获取筛选条件
    building = request.args.get('building')
    has_power = request.args.get('has_power') == 'on'
    date_str = request.args.get('date')
    start_hour = request.args.get('start_hour')
    duration = request.args.get('duration')
    
    # 默认为今天
    today = datetime.now().date()
    if date_str:
        date = datetime.fromisoformat(date_str).date()
    else:
        date = today
    
    # 默认为当前时间的下一个整点
    if start_hour:
        start_hour = int(start_hour)
    else:
        current_hour = datetime.now().hour
        start_hour = current_hour + 1 if current_hour < 23 else 7  # 如果当前是23点，默认为第二天早上7点
    
    # 默认预约时长为1小时
    if duration:
        duration = int(duration)
    else:
        duration = 1
    
    # 构建开始时间和结束时间
    start_time = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
    end_time = start_time + timedelta(hours=duration)
    
    # 过滤自习室
    query = StudyRoom.query.filter_by(is_active=True)
    if building:
        query = query.filter_by(building=building)
    
    rooms = query.all()
    
    # 过滤时间范围外的自习室
    available_rooms = []
    for room in rooms:
        # 检查自习室是否在请求的时间范围内开放
        room_open = True
        current_time = start_time
        while current_time < end_time:
            current_date = current_time.date()
            current_time_of_day = current_time.time()
            
            # 检查当前时间点自习室是否开放
            if not room.is_24h and (current_time_of_day < room.open_time or current_time_of_day > room.close_time):
                room_open = False
                break
                
            current_time += timedelta(hours=1)
        
        if not room_open:
            continue
            
        # 获取可用座位
        available_seats = []
        for seat in room.seats.filter_by(is_active=True).all():
            if has_power and not seat.has_power_outlet:
                continue
                
            if seat.is_available(start_time, end_time):
                available_seats.append({
                    'id': seat.id,
                    'seat_number': seat.seat_number,
                    'has_power_outlet': seat.has_power_outlet
                })
        
        if available_seats:
            available_rooms.append({
                'id': room.id,
                'name': room.name,
                'building': room.building,
                'floor': room.floor,
                'available_seats': available_seats,
                'total_available': len(available_seats)
            })
    
    # 获取所有建筑列表，用于筛选
    buildings = db.session.query(StudyRoom.building).distinct().all()
    buildings = [b[0] for b in buildings]
    
    return render_template('student/search.html', 
                          rooms=available_rooms,
                          date=date.isoformat(),
                          start_hour=start_hour,
                          duration=duration,
                          has_power=has_power,
                          selected_building=building,
                          buildings=buildings,
                          today=today.isoformat())

@bp.route('/book', methods=['POST'])
@login_required
def book():
    """预约座位"""
    seat_id = request.form.get('seat_id')
    date_str = request.form.get('date')
    start_hour = int(request.form.get('start_hour'))
    duration = int(request.form.get('duration'))
    
    # 验证输入
    if not seat_id or not date_str or start_hour < 0 or start_hour > 23 or duration < 1:
        flash('请提供有效的预约信息', 'danger')
        return redirect(url_for('student.search'))
    
    # 获取座位
    seat = Seat.query.get_or_404(seat_id)
    
    # 构建开始和结束时间
    date = datetime.fromisoformat(date_str).date()
    start_time = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
    end_time = start_time + timedelta(hours=duration)
    
    # 验证座位在这个时间段是否可用
    if not seat.is_available(start_time, end_time):
        flash('该座位在选择的时间段已被预约', 'danger')
        return redirect(url_for('student.search'))
    
    # 验证预约时长是否超过最大限制
    max_hours = current_app.config.get('MAX_BOOKING_HOURS', 4)
    if duration > max_hours:
        flash(f'单次预约时长不能超过{max_hours}小时', 'danger')
        return redirect(url_for('student.search'))
    
    # 检查是否有与当前预约时间重叠的其他预约
    overlapping_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.end_time > start_time,
        Booking.start_time < end_time,
        Booking.status.in_(['confirmed', 'checked_in'])
    ).count()
    
    if overlapping_bookings > 0:
        flash('您在选择的时间段内已有其他预约', 'danger')
        return redirect(url_for('student.search'))
    
    # 创建预约
    booking = Booking(
        user_id=current_user.id,
        seat_id=seat_id,
        start_time=start_time,
        end_time=end_time
    )
    
    db.session.add(booking)
    db.session.commit()
    
    # 触发预约提醒任务（在实际应用中会通过调度器执行）
    
    flash('座位预约成功！', 'success')
    return redirect(url_for('student.bookings'))

@bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """取消预约"""
    booking = Booking.query.get_or_404(booking_id)
    
    # 验证预约属于当前用户
    if booking.user_id != current_user.id:
        flash('无权操作此预约', 'danger')
        return redirect(url_for('student.bookings'))
    
    # 验证预约可以被取消
    if booking.status not in ['confirmed', 'checked_in']:
        flash('此预约无法被取消', 'danger')
        return redirect(url_for('student.bookings'))
    
    booking.cancel()
    flash('预约已取消', 'success')
    return redirect(url_for('student.bookings'))

@bp.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    """座位签到"""
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        verify_code = request.form.get('verify_code')
        
        if not booking_id or not verify_code:
            flash('请提供有效的签到信息', 'danger')
            return redirect(url_for('student.checkin'))
        
        booking = Booking.query.get_or_404(booking_id)
        
        # 验证预约属于当前用户
        if booking.user_id != current_user.id:
            flash('无权操作此预约', 'danger')
            return redirect(url_for('student.checkin'))
        
        # 验证预约可以签到
        if not booking.can_check_in():
            flash('此预约现在不能签到', 'danger')
            return redirect(url_for('student.checkin'))
        
        # 验证签到码
        room = StudyRoom.query.get(booking.seat.room_id)
        if room.verify_code != verify_code:
            flash('签到码不正确', 'danger')
            return redirect(url_for('student.checkin'))
        
        # 执行签到
        booking.check_in()
        flash('签到成功！', 'success')
        return redirect(url_for('student.bookings'))
    
    # 获取可以签到的预约
    now = datetime.now()
    eligible_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status == 'confirmed',
        Booking.start_time - timedelta(minutes=15) <= now,
        Booking.start_time + timedelta(minutes=15) >= now
    ).all()
    
    return render_template('student/checkin.html', bookings=eligible_bookings)

@bp.route('/favorites')
@login_required
def favorites():
    """查看常用座位"""
    # 获取用户最近一个月内使用过的座位
    one_month_ago = datetime.now() - timedelta(days=30)
    
    # 查找用户的历史预约并按座位分组计数
    seat_usage = db.session.query(
        Booking.seat_id,
        db.func.count(Booking.id).label('usage_count')
    ).filter(
        Booking.user_id == current_user.id,
        Booking.booking_time >= one_month_ago
    ).group_by(Booking.seat_id).order_by(db.desc('usage_count')).limit(10).all()
    
    # 获取座位详细信息
    favorite_seats = []
    for seat_id, count in seat_usage:
        seat = Seat.query.get(seat_id)
        if seat:
            favorite_seats.append({
                'id': seat.id,
                'room_name': seat.room.name,
                'building': seat.room.building,
                'seat_number': seat.seat_number,
                'has_power_outlet': seat.has_power_outlet,
                'usage_count': count
            })
    
    return render_template('student/favorites.html', favorite_seats=favorite_seats) 