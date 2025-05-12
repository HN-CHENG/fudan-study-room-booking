from app import create_app, db
from app.utils import init_scheduler
from app.models import User, StudyRoom, Seat, Booking
import click
from flask.cli import with_appcontext

app = create_app()
init_scheduler(app)

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'StudyRoom': StudyRoom,
        'Seat': Seat,
        'Booking': Booking
    }

@click.command('init-db')
@with_appcontext
def init_db_command():
    """清除并重新创建数据库表"""
    db.drop_all()
    db.create_all()
    click.echo('数据库已初始化')
    
    # 创建管理员账户
    admin = User(
        student_id='admin',
        username='系统管理员',
        email='admin@fudan.edu.cn',
        password='adminpwd',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    click.echo('管理员账户已创建')

app.cli.add_command(init_db_command)

@click.command('create-demo-data')
@with_appcontext
def create_demo_data():
    """创建示例数据"""
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
    from app.routes.admin import generate_verify_code
    generate_verify_code(room1)
    generate_verify_code(room2)
    generate_verify_code(room3)
    
    click.echo('示例数据已创建')

app.cli.add_command(create_demo_data)

if __name__ == '__main__':
    app.run(debug=True) 