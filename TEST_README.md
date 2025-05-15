# 自习室预约系统测试指南

本文档介绍如何运行自习室预约系统的自动化测试。

## 测试类型

本项目包含两种类型的测试：

1. **单元测试**：测试应用的各个功能模块，不涉及UI界面
2. **UI自动化测试**：使用Selenium模拟用户在浏览器中的操作，测试整个应用的功能流程

## 前置要求

在运行测试前，请确保已满足以下条件：

1. Python 3.8或更高版本
2. 已安装所有应用依赖（`pip install -r requirements.txt`）
3. 已安装测试依赖（`pip install -r test_requirements.txt`）
4. 如果运行UI测试，需要安装Chrome浏览器和ChromeDriver

## 安装ChromeDriver

### Linux（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install -y chromium-chromedriver
```

### macOS

```bash
brew install --cask chromedriver
```

### Windows

1. 下载与你的Chrome版本匹配的ChromeDriver：https://chromedriver.chromium.org/downloads
2. 将下载的文件解压缩并添加到系统PATH

## 运行测试

我们提供了一个统一的测试运行脚本`run_tests.py`，可以通过以下命令运行：

### 安装依赖并准备测试环境

```bash
python run_tests.py --setup
```

### 运行所有测试

```bash
python run_tests.py
```

### 只运行单元测试

```bash
python run_tests.py --unit
```

### 只运行UI自动化测试

```bash
python run_tests.py --selenium
```

### 清理测试环境和数据库

```bash
python run_tests.py --clean
```

## 测试脚本说明

1. `test_app.py` - 包含应用功能的单元测试
2. `selenium_test.py` - 包含使用Selenium的UI自动化测试
3. `run_tests.py` - 测试运行和管理脚本

## 测试内容

测试脚本涵盖了以下功能：

### 单元测试

- 用户注册
- 用户登录
- 座位搜索
- 座位预约
- 查看预约记录
- 取消预约
- 管理员功能
- 按电源筛选座位

### UI自动化测试

- 用户注册流程
- 登录和退出流程
- 搜索座位
- 预约座位
- 查看和取消预约
- 管理员登录

## 故障排除

1. **ChromeDriver版本问题**：确保ChromeDriver版本与Chrome版本匹配
2. **权限问题**：在某些Linux系统上，可能需要为ChromeDriver添加执行权限：`chmod +x /path/to/chromedriver`
3. **测试数据库错误**：确保应用有权限创建和访问`test.db`文件
4. **端口占用**：确保端口5000未被其他应用占用

## 已知问题和解决方案

### 数据库唯一性约束冲突

如果遇到以下错误：
```
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: users.email
```

**解决方案**：我们已通过以下方式解决此问题：
1. 在测试中使用随机后缀为每个测试用户生成唯一的学号和邮箱
2. 测试开始前清理数据库
3. 单元测试使用内存数据库以避免持久化数据冲突

如果仍然遇到此问题，请尝试：
```bash
python run_tests.py --clean
```

### 调度器错误（SchedulerAlreadyRunningError）

当多次运行测试时，可能会遇到以下错误：
```
apscheduler.schedulers.SchedulerAlreadyRunningError: Scheduler is already running
```

**解决方案**：我们已在测试中处理这个问题，确保在每次测试前停止调度器。如果仍然遇到问题，请尝试：

1. 重新启动测试脚本
2. 手动终止所有Python进程后再运行测试

### 模型初始化参数不匹配

当ModelStudyRoom或Seat的模型定义与测试不符时，可能会遇到：
```
TypeError: __init__() got an unexpected keyword argument 'is_active'
```

**解决方案**：我们已更新测试脚本，在初始化对象后手动设置属性，而不是通过构造函数参数传递。如果更改了模型定义，请相应地更新测试脚本。

## 自定义测试

如果需要编写自己的测试，请参考现有的测试脚本。以下是一些关键点：

1. 总是在`setUp`方法中停止调度器：
   ```python
   from app import scheduler
   if scheduler.running:
       scheduler.shutdown()
   ```

2. 注意模型初始化时的必须参数和可选参数，避免使用构造函数中不存在的参数：
   ```python
   # 正确方式
   room = StudyRoom(name="测试", building="楼", floor=1, capacity=10)
   room.is_active = True  # 手动设置属性
   
   # 错误方式
   room = StudyRoom(name="测试", building="楼", floor=1, capacity=10, is_active=True)
   ```

3. 使用随机后缀确保邮箱和学号的唯一性：
   ```python
   import random
   import string
   
   # 生成随机后缀
   random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
   
   # 用于用户创建
   user = User(
       student_id=f"19302010001_{random_suffix}",
       username="测试用户",
       email=f"test_{random_suffix}@fudan.edu.cn",
       password="123456"
   )
   ```

4. 使用隔离的测试数据库：
   ```python
   app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
   ``` 