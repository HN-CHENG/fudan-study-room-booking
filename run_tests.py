#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import argparse
import time
import sqlite3
from termcolor import colored

def run_unit_tests():
    """运行单元测试"""
    print(colored("开始运行单元测试...", "cyan"))
    # 确保scheduler已停止，以防止测试间的冲突
    try:
        from app import scheduler
        if scheduler.running:
            print(colored("停止全局调度器...", "yellow"))
            scheduler.shutdown()
    except Exception as e:
        print(colored(f"无法停止调度器: {e}", "yellow"))
        print(colored("继续测试...", "yellow"))
    
    # 确保使用内存数据库
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    print(colored("使用内存数据库进行单元测试...", "cyan"))
        
    # 导入测试用例
    from test_app import TestStudyRoomApp
    
    # 创建测试套件
    unit_suite = unittest.TestLoader().loadTestsFromTestCase(TestStudyRoomApp)
    
    # 运行测试
    result = unittest.TextTestRunner(verbosity=2).run(unit_suite)
    
    return result.wasSuccessful()

def run_selenium_tests():
    """运行Selenium UI测试"""
    print(colored("开始运行UI自动化测试...", "cyan"))
    
    # 确保scheduler已停止，以防止测试间的冲突
    try:
        from app import scheduler
        if scheduler.running:
            print(colored("停止全局调度器...", "yellow"))
            scheduler.shutdown()
    except Exception as e:
        print(colored(f"无法停止调度器: {e}", "yellow"))
        print(colored("继续测试...", "yellow"))
    
    # 检查是否已安装Selenium
    try:
        import selenium
    except ImportError:
        print(colored("错误: 未安装Selenium。请先安装: pip install selenium", "red"))
        return False
    
    # 检查Chrome WebDriver是否可用
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        driver.quit()
    except Exception as e:
        print(colored(f"错误: Chrome WebDriver不可用: {e}", "red"))
        print(colored("请安装Chrome WebDriver并确保其在PATH中", "yellow"))
        return False
    
    # 删除可能存在的测试数据库
    try:
        if os.path.exists('test.db'):
            os.remove('test.db')
            print(colored("已删除旧的测试数据库", "yellow"))
    except Exception as e:
        print(colored(f"无法删除测试数据库: {e}", "yellow"))
    
    from selenium_test import SeleniumTestStudyRoom
    
    # 创建测试套件
    selenium_suite = unittest.TestLoader().loadTestsFromTestCase(SeleniumTestStudyRoom)
    
    # 运行测试
    result = unittest.TextTestRunner(verbosity=2).run(selenium_suite)
    
    # 测试结束后清理
    try:
        if os.path.exists('test.db'):
            os.remove('test.db')
            print(colored("已删除测试数据库", "yellow"))
    except Exception as e:
        print(colored(f"无法删除测试数据库: {e}", "yellow"))
    
    return result.wasSuccessful()

def install_requirements():
    """安装测试所需的依赖"""
    print(colored("安装测试所需的依赖...", "cyan"))
    
    # 创建测试需要的依赖文件
    with open('test_requirements.txt', 'w') as f:
        f.write("""selenium>=4.0.0
termcolor>=1.1.0
pytest>=7.0.0
pytest-flask>=1.2.0
webdriver-manager>=3.8.5
""")
    
    # 安装依赖
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'test_requirements.txt'])
    
    if result.returncode == 0:
        print(colored("依赖安装完成", "green"))
        return True
    else:
        print(colored("依赖安装失败", "red"))
        return False

def setup_test_environment():
    """准备测试环境"""
    print(colored("准备测试环境...", "cyan"))
    
    # 检查并初始化测试数据库
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # 清理可能存在的数据库文件
    try:
        db_path = os.path.join('instance', 'study_room.sqlite')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            # 清空每个表
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':
                    try:
                        cursor.execute(f"DELETE FROM {table_name};")
                    except:
                        pass
            conn.commit()
            conn.close()
            print(colored("已清理测试数据库内容", "yellow"))
    except Exception as e:
        print(colored(f"数据库清理警告: {e}", "yellow"))
        print(colored("继续测试...", "yellow"))
    
    # 检查模型定义是否符合测试预期
    print(colored("检查模型定义...", "cyan"))
    try:
        from app.models import StudyRoom, Seat
        import random
        import string
        
        # 生成随机后缀确保邮箱唯一
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        # 验证StudyRoom模型
        room = StudyRoom(
            name=f"测试自习室_{random_suffix}",
            building="测试楼", 
            floor=1,
            capacity=10
        )
        # 手动设置额外属性
        room.is_active = True
        room.is_24h = True
        
        # 验证Seat模型
        seat = Seat(
            room_id=1,
            seat_number=f"1_{random_suffix}",
            has_power_outlet=True
        )
        # 手动设置额外属性
        seat.is_active = True
        
        print(colored("模型检查通过", "green"))
        
    except Exception as e:
        print(colored(f"模型检查失败: {e}", "red"))
        print(colored("请确保测试脚本与当前模型定义一致", "yellow"))
        return False
    
    # 确保应用初始化正确
    try:
        from app import create_app, scheduler
        app = create_app()
        
        # 停止调度器，防止SchedulerAlreadyRunningError
        if scheduler.running:
            print(colored("停止全局调度器...", "yellow"))
            scheduler.shutdown()
            
        with app.app_context():
            # 简单测试应用上下文
            pass
        print(colored("应用初始化成功", "green"))
        return True
    except Exception as e:
        print(colored(f"应用初始化失败: {e}", "red"))
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='自习室预约系统测试脚本')
    parser.add_argument('--unit', action='store_true', help='只运行单元测试')
    parser.add_argument('--selenium', action='store_true', help='只运行Selenium测试')
    parser.add_argument('--setup', action='store_true', help='安装测试依赖并准备环境')
    parser.add_argument('--clean', action='store_true', help='清理测试数据和数据库')
    args = parser.parse_args()
    
    start_time = time.time()
    
    # 如果指定了清理选项，执行清理操作
    if args.clean:
        clean_test_environment()
        if not (args.unit or args.selenium or args.setup):
            return 0
    
    if args.setup or (not args.unit and not args.selenium):
        # 安装依赖并设置环境
        if not install_requirements() or not setup_test_environment():
            print(colored("测试环境准备失败，退出测试", "red"))
            return 1
    
    unit_success = True
    selenium_success = True
    
    if args.unit or (not args.selenium and not args.setup):
        unit_success = run_unit_tests()
    
    if args.selenium or (not args.unit and not args.setup):
        selenium_success = run_selenium_tests()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(colored(f"测试总耗时: {duration:.2f} 秒", "cyan"))
    
    if unit_success and selenium_success:
        print(colored("所有测试通过! ✅", "green"))
        return 0
    else:
        failed_tests = []
        if not unit_success:
            failed_tests.append("单元测试")
        if not selenium_success:
            failed_tests.append("Selenium测试")
        
        print(colored(f"以下测试失败: {', '.join(failed_tests)} ❌", "red"))
        return 1

def clean_test_environment():
    """清理测试环境"""
    print(colored("清理测试环境...", "cyan"))
    
    # 清理数据库文件
    files_to_remove = ['test.db']
    
    # 尝试清理instance文件夹中的数据库
    if os.path.exists('instance'):
        files_to_remove.append(os.path.join('instance', 'study_room.sqlite'))
    
    for file_path in files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(colored(f"已删除: {file_path}", "yellow"))
        except Exception as e:
            print(colored(f"无法删除 {file_path}: {e}", "red"))
    
    print(colored("测试环境清理完成", "green"))

if __name__ == "__main__":
    sys.exit(main()) 