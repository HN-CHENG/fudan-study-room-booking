#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import json
import time
import random
import string
from datetime import datetime, timedelta
from app import create_app, db, scheduler
from app.models import User, StudyRoom, Seat, Booking

class TestStudyRoomApp(unittest.TestCase):
    """测试复旦大学自习室预约系统的功能测试类"""

    def setUp(self):
        """测试前的准备工作"""
        # 停止全局调度器，防止SchedulerAlreadyRunningError
        if scheduler.running:
            scheduler.shutdown()
            
        # 创建测试应用
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            SERVER_NAME='localhost:5000',
            WTF_CSRF_ENABLED=False,  # 禁用CSRF保护以简化测试
            SCHEDULER_API_ENABLED=False  # 禁用调度器API
        )
        
        # 创建测试客户端
        self.client = self.app.test_client()
        
        # 创建应用上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建数据库表结构
        db.create_all()
        
        # 生成随机后缀，用于确保邮箱地址唯一
        self.random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        # 创建测试数据
        self._create_test_data()
    
    def tearDown(self):
        """测试结束后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """创建测试用数据"""
        # 创建管理员用户，使用随机后缀确保邮箱唯一
        admin = User(
            student_id=f"admin_{self.random_suffix}",
            username="管理员",
            email=f"admin_{self.random_suffix}@fudan.edu.cn",
            password="adminpw",
            is_admin=True
        )
        db.session.add(admin)
        
        # 创建测试自习室 - 修正初始化参数，符合StudyRoom模型的__init__方法
        room = StudyRoom(
            name="测试自习室",
            building="测试楼",
            floor=1,
            capacity=10,
            is_24h=True
        )
        # 手动设置is_active属性，而不是通过构造函数
        room.is_active = True
        
        db.session.add(room)
        db.session.commit()
        
        # 创建测试座位
        for i in range(1, 11):
            has_power = i % 2 == 0  # 偶数座位有电源
            seat = Seat(
                room_id=room.id,
                seat_number=f"{i}",
                has_power_outlet=has_power
            )
            # 手动设置is_active属性
            seat.is_active = True
            db.session.add(seat)
        
        # 提交更改
        db.session.commit()
        
        # 保存测试数据的ID以便后续测试使用
        self.room_id = room.id
        self.admin_id = admin.id
    
    def test_1_register(self):
        """测试用户注册功能"""
        # 提交注册表单，注意使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        response = self.client.post('/auth/register', data={
            'student_id': f'19302010001_{random_suffix}',
            'username': '测试用户',
            'email': f'test_{random_suffix}@fudan.edu.cn',
            'password': '123456'
        }, follow_redirects=True)
        
        # 验证注册成功
        self.assertEqual(response.status_code, 200)
        self.assertIn('注册成功，请登录', response.get_data(as_text=True))
        
        # 验证用户已添加到数据库
        user = User.query.filter_by(student_id=f'19302010001_{random_suffix}').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, '测试用户')
        self.assertEqual(user.email, f'test_{random_suffix}@fudan.edu.cn')
        self.assertFalse(user.is_admin)
    
    def test_2_login(self):
        """测试用户登录功能"""
        # 先创建测试用户，使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user = User(
            student_id=f'19302010002_{random_suffix}',
            username='登录测试用户',
            email=f'login_{random_suffix}@fudan.edu.cn',
            password='123456'
        )
        db.session.add(user)
        db.session.commit()
        
        # 提交登录表单
        response = self.client.post('/auth/login', data={
            'student_id': f'19302010002_{random_suffix}',
            'password': '123456',
            'remember': 'on'
        }, follow_redirects=True)
        
        # 验证登录成功
        self.assertEqual(response.status_code, 200)
        self.assertIn('登录成功', response.get_data(as_text=True))
    
    def test_3_search_seats(self):
        """测试搜索座位功能"""
        # 先创建并登录测试用户，使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user = User(
            student_id=f'19302010003_{random_suffix}',
            username='搜索测试用户',
            email=f'search_{random_suffix}@fudan.edu.cn',
            password='123456'
        )
        db.session.add(user)
        db.session.commit()
        
        self.client.post('/auth/login', data={
            'student_id': f'19302010003_{random_suffix}',
            'password': '123456'
        })
        
        # 执行座位搜索
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        response = self.client.get(f'/student/search?date={tomorrow}&start_hour=10&duration=2&building=测试楼&has_power=on')
        
        # 验证搜索结果
        self.assertEqual(response.status_code, 200)
        # 应该能找到有电源的座位
        self.assertIn('测试自习室', response.get_data(as_text=True))
    
    def test_4_book_seat(self):
        """测试预约座位功能"""
        # 先创建并登录测试用户，使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user = User(
            student_id=f'19302010004_{random_suffix}',
            username='预约测试用户',
            email=f'book_{random_suffix}@fudan.edu.cn',
            password='123456'
        )
        db.session.add(user)
        db.session.commit()
        
        self.client.post('/auth/login', data={
            'student_id': f'19302010004_{random_suffix}',
            'password': '123456'
        })
        
        # 获取一个有电源的座位ID
        seat = Seat.query.filter_by(room_id=self.room_id, has_power_outlet=True).first()
        
        # 预约明天10点到12点
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        response = self.client.post('/student/book', data={
            'seat_id': seat.id,
            'date': tomorrow,
            'start_hour': 10,
            'duration': 2
        }, follow_redirects=True)
        
        # 验证预约成功
        self.assertEqual(response.status_code, 200)
        self.assertIn('座位预约成功', response.get_data(as_text=True))
        
        # 验证数据库中有记录
        booking = Booking.query.filter_by(user_id=user.id, seat_id=seat.id).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'confirmed')
    
    def test_5_check_booking(self):
        """测试查看预约记录功能"""
        # 先创建测试用户，使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user = User(
            student_id=f'19302010005_{random_suffix}',
            username='查询测试用户',
            email=f'check_{random_suffix}@fudan.edu.cn',
            password='123456'
        )
        db.session.add(user)
        db.session.commit()
        
        # 创建一个预约记录
        seat = Seat.query.filter_by(room_id=self.room_id).first()
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=2)
        
        booking = Booking(
            user_id=user.id,
            seat_id=seat.id,
            start_time=start_time,
            end_time=end_time
        )
        booking.status = 'confirmed'
        db.session.add(booking)
        db.session.commit()
        
        # 登录
        self.client.post('/auth/login', data={
            'student_id': f'19302010005_{random_suffix}',
            'password': '123456'
        })
        
        # 查看预约记录
        response = self.client.get('/student/bookings')
        
        # 验证预约记录存在
        self.assertEqual(response.status_code, 200)
        html_content = response.get_data(as_text=True)
        self.assertIn('测试自习室', html_content)
        self.assertIn(seat.seat_number, html_content)
    
    def test_6_cancel_booking(self):
        """测试取消预约功能"""
        # 先创建测试用户，使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user = User(
            student_id=f'19302010006_{random_suffix}',
            username='取消测试用户',
            email=f'cancel_{random_suffix}@fudan.edu.cn',
            password='123456'
        )
        db.session.add(user)
        db.session.commit()
        
        # 创建一个预约记录
        seat = Seat.query.filter_by(room_id=self.room_id).first()
        start_time = datetime.now() + timedelta(hours=3)
        end_time = start_time + timedelta(hours=2)
        
        booking = Booking(
            user_id=user.id,
            seat_id=seat.id,
            start_time=start_time,
            end_time=end_time
        )
        booking.status = 'confirmed'
        db.session.add(booking)
        db.session.commit()
        
        # 登录
        self.client.post('/auth/login', data={
            'student_id': f'19302010006_{random_suffix}',
            'password': '123456'
        })
        
        # 取消预约
        response = self.client.post(f'/student/cancel/{booking.id}', follow_redirects=True)
        
        # 验证取消成功
        self.assertEqual(response.status_code, 200)
        self.assertIn('预约已取消', response.get_data(as_text=True))
        
        # 验证数据库中状态已更新
        updated_booking = Booking.query.get(booking.id)
        self.assertEqual(updated_booking.status, 'cancelled')
    
    def test_7_admin_login(self):
        """测试管理员登录功能"""
        # 提交登录表单，使用创建的管理员用户
        response = self.client.post('/auth/login', data={
            'student_id': f"admin_{self.random_suffix}",
            'password': 'adminpw'
        }, follow_redirects=True)
        
        # 验证登录成功
        self.assertEqual(response.status_code, 200)
        self.assertIn('登录成功', response.get_data(as_text=True))
    
    def test_8_filter_by_power(self):
        """测试按电源筛选功能"""
        # 先创建并登录测试用户，使用随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user = User(
            student_id=f'19302010007_{random_suffix}',
            username='筛选测试用户',
            email=f'filter_{random_suffix}@fudan.edu.cn',
            password='123456'
        )
        db.session.add(user)
        db.session.commit()
        
        self.client.post('/auth/login', data={
            'student_id': f'19302010007_{random_suffix}',
            'password': '123456'
        })
        
        # 按电源筛选座位
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        
        # 筛选带电源的座位
        response_with_power = self.client.get(f'/student/search?date={tomorrow}&start_hour=14&duration=2&has_power=on')
        
        # 筛选不带电源筛选条件
        response_all = self.client.get(f'/student/search?date={tomorrow}&start_hour=14&duration=2')
        
        # 验证结果
        html_with_power = response_with_power.get_data(as_text=True)
        html_all = response_all.get_data(as_text=True)
        
        # 应该能看到有电源的座位
        self.assertIn('有电源', html_with_power)
        
        # 验证筛选结果不同
        self.assertNotEqual(html_with_power.count('座位'), html_all.count('座位'))

if __name__ == '__main__':
    unittest.main() 