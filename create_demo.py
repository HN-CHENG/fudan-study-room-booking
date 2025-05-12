from app import create_app
from app import db
from app.models import User, StudyRoom, Seat, Booking
from datetime import datetime, time
from app.routes.admin import generate_verify_code

# 创建应用实例和上下文
app = create_app()
with app.app_context():
    # 添加示例自习室
    room1 = StudyRoom(
        name='光华楼自习室A',
        building='光华楼',
        floor=2,
        capacity=50
    )
    db.session.add(room1)
    
    room2 = StudyRoom(
        name='光华楼自习室B',
        building='光华楼',
        floor=3,
        capacity=40
    )
    db.session.add(room2)
    
    room3 = StudyRoom(
        name='李兆基自习室',
        building='李兆基',
        floor=1,
        capacity=60
    )
    db.session.add(room3)
    
    db.session.commit()
    
    # 添加座位
    for i in range(1, 51):
        has_power = i % 5 == 0  # 每5个座位有1个电源插座
        seat = Seat(
            room_id=room1.id,
            seat_number=f"{i}",
            has_power_outlet=has_power
        )
        db.session.add(seat)
        
    for i in range(1, 41):
        has_power = i % 4 == 0  # 每4个座位有1个电源插座
        seat = Seat(
            room_id=room2.id,
            seat_number=f"{i}",
            has_power_outlet=has_power
        )
        db.session.add(seat)
        
    for i in range(1, 61):
        has_power = i % 3 == 0  # 每3个座位有1个电源插座
        seat = Seat(
            room_id=room3.id,
            seat_number=f"{i}",
            has_power_outlet=has_power
        )
        db.session.add(seat)
    
    db.session.commit()
    
    # 创建测试用户
    test_user = User(
        student_id='19302010001',
        username='测试用户',
        email='test@fudan.edu.cn',
        password='123456'
    )
    db.session.add(test_user)
    db.session.commit()
    
    # 为房间生成验证码
    generate_verify_code(room1)
    generate_verify_code(room2)
    generate_verify_code(room3)
    
    print('示例数据已创建')
