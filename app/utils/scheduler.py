from app import scheduler, db, mail
from app.models import Booking, User
from flask_mail import Message
from datetime import datetime, timedelta
from flask import current_app, render_template

def init_scheduler(app):
    """初始化调度器任务"""
    with app.app_context():
        # 检查预约是否需要提醒
        scheduler.add_job(
            id='check_upcoming_bookings',
            func=check_upcoming_bookings,
            trigger='interval',
            minutes=5,
            replace_existing=True
        )
        
        # 检查未签到的预约
        scheduler.add_job(
            id='check_unchecked_bookings',
            func=check_unchecked_bookings,
            trigger='interval',
            minutes=5,
            replace_existing=True
        )
        
        # 每天凌晨生成新的签到码
        scheduler.add_job(
            id='generate_daily_codes',
            func=generate_daily_codes,
            trigger='cron',
            hour=0,
            minute=0,
            replace_existing=True
        )
        
        # 完成已结束的预约
        scheduler.add_job(
            id='complete_finished_bookings',
            func=complete_finished_bookings,
            trigger='interval',
            minutes=10,
            replace_existing=True
        )
        
def check_upcoming_bookings():
    """检查即将开始的预约并发送提醒"""
    now = datetime.now()
    
    # 查找15分钟内即将开始的预约
    upcoming_bookings = Booking.query.filter(
        Booking.start_time > now,
        Booking.start_time <= now + timedelta(minutes=15),
        Booking.status == 'confirmed'
    ).all()
    
    for booking in upcoming_bookings:
        # 发送邮件提醒
        send_reminder_email(booking, '预约即将开始', '您预约的自习座位即将开始，请提前到达并签到。')

def check_unchecked_bookings():
    """检查未签到的预约"""
    now = datetime.now()
    
    # 查找已开始10分钟但未签到的预约
    late_bookings = Booking.query.filter(
        Booking.start_time < now,
        Booking.start_time > now - timedelta(minutes=15),
        Booking.start_time <= now - timedelta(minutes=10),
        Booking.status == 'confirmed'
    ).all()
    
    for booking in late_bookings:
        # 发送提醒邮件
        send_reminder_email(booking, '签到提醒', '您的预约已开始，请尽快到达自习室并签到，否则预约将在5分钟后自动取消。')
    
    # 查找超过15分钟未签到的预约
    expired_bookings = Booking.query.filter(
        Booking.start_time < now - timedelta(minutes=15),
        Booking.status == 'confirmed'
    ).all()
    
    for booking in expired_bookings:
        # 标记为过期并记录违约
        booking.expire()
        
        user = User.query.get(booking.user_id)
        user.add_violation()
        
        # 发送取消通知
        send_reminder_email(booking, '预约已取消', '由于您未按时签到，您的座位预约已自动取消。这将记录为一次违约。')

def generate_daily_codes():
    """每日生成新的签到验证码"""
    from app.models import StudyRoom
    from app.routes.admin import generate_verify_code
    
    rooms = StudyRoom.query.filter_by(is_active=True).all()
    for room in rooms:
        generate_verify_code(room)

def complete_finished_bookings():
    """完成已结束的预约"""
    now = datetime.now()
    
    # 查找已结束的预约
    finished_bookings = Booking.query.filter(
        Booking.end_time < now,
        Booking.status == 'checked_in'
    ).all()
    
    for booking in finished_bookings:
        booking.complete()

def send_reminder_email(booking, subject, message):
    """发送提醒邮件"""
    user = User.query.get(booking.user_id)
    
    if not user or not user.email:
        return
        
    msg = Message(
        subject=f'[复旦自习室] {subject}',
        recipients=[user.email],
        html=render_template('emails/reminder.html',
                           user=user,
                           booking=booking,
                           message=message)
    )
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"发送邮件失败: {str(e)}") 