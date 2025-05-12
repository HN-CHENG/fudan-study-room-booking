from app import create_app, db
from app.models import User, StudyRoom, Seat, Booking

# 创建应用实例和上下文
app = create_app()
with app.app_context():
    # 清除并重新创建数据库表
    db.drop_all()
    db.create_all()
    print('数据库已初始化')
    
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
    print('管理员账户已创建')
