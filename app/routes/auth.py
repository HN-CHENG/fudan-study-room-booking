from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        student_id = request.form['student_id']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        error = None
        
        if not student_id:
            error = '需要学号'
        elif not username:
            error = '需要用户名'
        elif not email or ('@fudan.edu.cn' not in email and '@m.fudan.edu.cn' not in email):
            error = '需要有效的复旦大学邮箱'
        elif not password:
            error = '需要密码'
        elif User.query.filter_by(student_id=student_id).first():
            error = f'学号 {student_id} 已经注册'
        elif User.query.filter_by(email=email).first():
            error = f'邮箱 {email} 已经注册'
            
        if error is None:
            user = User(
                student_id=student_id,
                username=username,
                email=email,
                password=password
            )
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
            
        flash(error, 'danger')
        
    return render_template('auth/register.html')
    
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        remember = 'remember' in request.form
        
        error = None
        user = User.query.filter_by(student_id=student_id).first()
        
        if user is None:
            error = '学号不存在'
        elif not user.check_password(password):
            error = '密码不正确'
            
        if error is None:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            flash('登录成功', 'success')
            return redirect(next_page)
            
        flash(error, 'danger')
        
    return render_template('auth/login.html')
    
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('main.index'))
    
@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        
        error = None
        
        if not username:
            error = '需要用户名'
        elif not email or ('@fudan.edu.cn' not in email and '@m.fudan.edu.cn' not in email):
            error = '需要有效的复旦大学邮箱'
        
        if email != current_user.email and User.query.filter_by(email=email).first():
            error = f'邮箱 {email} 已被使用'
            
        if new_password and not current_user.check_password(current_password):
            error = '当前密码不正确'
            
        if error is None:
            current_user.username = username
            current_user.email = email
            
            if new_password:
                current_user.set_password(new_password)
                
            db.session.commit()
            flash('个人资料已更新', 'success')
            return redirect(url_for('auth.profile'))
            
        flash(error, 'danger')
        
    return render_template('auth/profile.html') 