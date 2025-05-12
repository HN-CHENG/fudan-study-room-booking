# 复旦大学自习室预约系统

这是一个基于Python Flask的自习室座位预约系统，旨在提高复旦大学各类自习室座位的使用率，通过信息技术手段解决"一座难求"与"占座却不在"的问题。

## 功能特点

- 学生可以查询、预约自习室座位
- 支持按教学楼、是否有电源等条件筛选座位
- 预约开始前15分钟提醒学生
- 签到功能：通过验证码或扫描二维码完成签到
- 未按时签到的预约自动取消，并记录违约行为
- 管理员可配置自习室及开放时间
- 使用数据统计功能，帮助管理者了解使用情况

## 技术栈

- Python 3.8+
- Flask 2.2.3
- SQLAlchemy (SQLite数据库)
- Flask-Login（用户认证）
- Flask-Mail（邮件提醒）
- Flask-APScheduler（定时任务）
- Bootstrap 5（前端UI）
- QRCode（生成签到二维码）

## 从零开始运行项目

### 1. 环境准备

- Python 3.8 或以上版本
- pip 包管理工具
- 推荐使用虚拟环境

```bash
# 安装虚拟环境工具(如果尚未安装)
pip install virtualenv

# 或者使用conda
conda create -n book python=3.9
conda activate book
```

### 2. 获取代码

```bash
# 克隆代码库到本地
git clone <repository-url>
cd book

# 或者直接解压下载的代码包
cd 代码所在路径
```

### 3. 安装依赖

```bash
# 激活虚拟环境(如果使用virtualenv)
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate  # Windows

# 如果使用conda
conda activate book

# 安装所有依赖
pip install -r requirements.txt
```

### 4. 初始化数据库

由于项目结构的原因，我们需要使用自定义脚本初始化数据库，而不是直接使用Flask命令。

```bash
# 在项目根目录下创建一个init_db.py文件，内容如下：
cat > init_db.py << "EOF"
from app import create_app, db
from app.models import User, StudyRoom, Seat, Booking

# 创建应用实例和上下文
app = create_app()
with app.app_context():
    # 清除并重新创建数据库表
    db.drop_all()
    db.create_all()
    print("数据库已初始化")
    
    # 创建管理员账户
    admin = User(
        student_id="admin",
        username="系统管理员",
        email="admin@fudan.edu.cn",
        password="adminpwd",
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("管理员账户已创建")
EOF

# 执行脚本初始化数据库
python init_db.py
```

### 5. 创建示例数据(可选)

```bash
# 在项目根目录下创建create_demo.py文件，内容如下：
cat > create_demo.py << "EOF"
from app import create_app, db
from app.models import User, StudyRoom, Seat, Booking
from datetime import datetime, time
from app.routes.admin import generate_verify_code

# 创建应用实例和上下文
app = create_app()
with app.app_context():
    # 添加示例自习室
    room1 = StudyRoom(
        name="光华楼自习室A",
        building="光华楼",
        floor=2,
        capacity=50
    )
    db.session.add(room1)
    
    room2 = StudyRoom(
        name="光华楼自习室B",
        building="光华楼",
        floor=3,
        capacity=40
    )
    db.session.add(room2)
    
    room3 = StudyRoom(
        name="李兆基自习室",
        building="李兆基",
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
        student_id="19302010001",
        username="测试用户",
        email="test@fudan.edu.cn",
        password="123456"
    )
    db.session.add(test_user)
    db.session.commit()
    
    # 为房间生成验证码
    generate_verify_code(room1)
    generate_verify_code(room2)
    generate_verify_code(room3)
    
    print("示例数据已创建")
EOF

# 执行脚本创建示例数据
python create_demo.py
```

### 6. 运行应用程序

```bash
# 设置环境变量并启动应用
export FLASK_APP=app.py  # Linux/Mac
# 或者
set FLASK_APP=app.py  # Windows CMD
# 或者
$env:FLASK_APP = "app.py"  # Windows PowerShell

# 启动应用
flask run

# 如果需要在局域网内访问
flask run --host=0.0.0.0
```

### 7. 访问应用

- 在浏览器中访问 http://127.0.0.1:5000 或 http://服务器IP:5000

### 8. 系统账户

#### 管理员账户
- 学号：admin
- 密码：adminpwd

#### 测试用户(如果创建了示例数据)
- 学号：19302010001
- 密码：123456

## 注意事项

1. 项目默认使用SQLite数据库，数据库文件位于`instance/study_room.sqlite`
2. 邮件提醒功能需要配置邮件服务器，请在`app/__init__.py`中修改相关配置
3. 静态文件(CSS、JS)和二维码图片位于`static`目录
4. HTML模板文件位于`templates`目录
5. 如果需要在生产环境部署，请使用生产级WSGI服务器(如Gunicorn、uWSGI等)

## 系统结构

- `app/models/` - 数据模型定义
- `app/routes/` - 路由和视图函数
- `app/utils/` - 工具函数和定时任务
- `templates/` - HTML模板
- `static/` - 静态文件(CSS、JS、图片)
- `instance/` - 实例文件夹(数据库等)

## 常见问题解决

1. **无法运行Flask命令**
   
   请确保正确设置了`FLASK_APP`环境变量，或直接使用提供的初始化脚本。

2. **依赖安装失败**
   
   可以尝试单个安装依赖：`pip install 依赖名称`，或者更新pip：`pip install --upgrade pip`

3. **运行时出现"no such table"错误**
   
   这表示数据库表未创建，请运行初始化数据库脚本。

4. **邮件发送失败**
   
   请检查邮件服务器配置，或者在开发过程中可以暂时禁用邮件功能。
