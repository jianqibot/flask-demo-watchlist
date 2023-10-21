import os
import click

from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

name = 'jianqi zhao'
movies = [
    {'title': 'My Neighbor Totoro', 'year': '1988'},
    {'title': 'Dead Poets Society', 'year': '1989'},
    {'title': 'A Perfect World', 'year': '1993'},
    {'title': 'Leon', 'year': '1994'},
    {'title': 'Mahjong', 'year': '1996'},
    {'title': 'Swallowtail Butterfly', 'year': '1996'},
    {'title': 'King of Comedy', 'year': '1999'},
    {'title': 'Devils on the Doorstep', 'year': '1999'},
    {'title': 'WALL-E', 'year': '2008'},
    {'title': 'The Pork of Music', 'year': '2012'},
]

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + \
    os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'
db = SQLAlchemy(app)  # 初始化扩展，传入程序实例 app
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Define view after login validation fails
login_manager.login_message = 'Please login first'


@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user


# command definition
@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


@app.cli.command()
def forge():
    # Generate fake data.
    db.create_all

    # 全局的两个变量移动到这个函数内
    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')


@app.cli.command()
@click.option('--name', prompt=True, help='The user name used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(name, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.name = name
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')


@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


@app.errorhandler(404)  # 传入要处理的错误代码
def page_not_found(e):  # 接受异常对象作为参数
    user = User.query.first()
    return render_template('not_found.html'), 404  # 返回模板和状态码


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        if not current_user.is_authenticated:
            return redirect(url_for('index'))

        # 获取表单数据
        title = request.form.get('title')
        year = request.form.get('year')

        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input')
            return redirect(url_for('index'))

        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Item created')
        return redirect(url_for('index'))

    movies = Movie.query.all()
    # 普通的视图函数之所以不用写出状态码，是因为默认会使用 200 状态码
    return render_template('index.html', movies=movies)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print('username = {}'.format(username))
        print('password = {}'.format(password))

        if (not username or not password):
            print('afefe')
            flash('Invalid input')
            return redirect(url_for('login'))

        user = User.query.first()
        print('name = {}'.format(user.name))
        print('password equals = {}'.format(user.validate_password(password)))

        # 验证用户名和密码是否一致
        if (username == user.name and user.validate_password(password)):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页


@login_required
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_item(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':
        title = request.form.get('title')
        year = request.form.get('year')

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input')
            # 重定向回对应的编辑页面
            return redirect(url_for('edit_item'), movie_id=movie_id)

        movie.title = title
        movie.year = year
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)


@login_required  # 登录保护
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页


@login_required
@app.route('/setting', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        name = request.form.get('name')

        if not name or len(name) > 20:
            flash('Invalid name')
            return redirect(url_for('settings'))

        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')


# DB domain
class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字
    password_hash = db.Column(db.String(20))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份
