from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_apscheduler import APScheduler
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
scheduler = APScheduler()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///../instance/study_room.sqlite',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER='smtp.example.com',  # 邮件服务器配置，实际使用时需修改
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='example@fudan.edu.cn',
        MAIL_PASSWORD='password',
        MAIL_DEFAULT_SENDER=('复旦自习室系统', 'example@fudan.edu.cn'),
        MAX_BOOKING_HOURS=4  # 最大预约时长（小时）
    )
    
    # 确保实例文件夹存在
    try:
        os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    except OSError:
        pass
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面'
    mail.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    
    # 注册蓝图
    from app.routes import auth, student, admin, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(main.bp)
    
    return app 