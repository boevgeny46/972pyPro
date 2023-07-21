from flask import Flask, request, redirect, abort
from flask import render_template, make_response, session
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_login import current_user
import requests
from forms.add_news import NewsForm
from loginform import LoginForm
from data import db_session
from dotenv import load_dotenv
from data.users import User
from data.news import News
from forms.user import RegisterForm
import datetime

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

app.config['SECRET_KEY'] = 'too short key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/news.sqlite'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)  # год


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


# ошибка 404
@app.errorhandler(404)
def http_404_error(error):
    return redirect('/error404')


@app.route('/error404')
def well():  # колодец
    return render_template('well.html')


@app.errorhandler(401)
def http_401_handler(error):
    return redirect('/login')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='apeBuona')



@app.route('/weatherForm', methods=['GET', 'POST'])

def weatherForm():
    if request.method == 'GET':
        return render_template('weatherForm.html',
                               title="Выбор места")
    elif request.method == 'POST':
        town = request.form.get('town')
        data = {}
        key = '78104c7cf846b04c6e7f47d241f9bb7e'
        url = 'https://api.openweathermap.org/data/2.5/weather'
        params = {'APPID': key, 'q': town, 'units': 'metric'}
        result = requests.get(url, params=params)
        weather = result.json()
        code = weather['cod']
        icon = weather['weather'][0]['icon']
        temperature = weather['main']['temp']
        pressure = weather['main']['pressure']
        wind = weather['wind']['speed']
        data['icon'] = weather['weather'][0]['icon']
        data['temp'] = weather['main']['temp']
        data['pressure'] = weather['main']['pressure']
        data['wind'] = weather['wind']['speed']
        print(temperature)
        return render_template('weather.html',
                               title=f'Погода в городе{town}',
                               town=town, data=data)


@app.route('/news', methods=['GET', 'POST'])
def news():
    db_sess = db_session.create_session()
    news = db_sess.query(News)
    db_sess.commit()
    return render_template('news.html', title='Новости', news=news)


@app.route('/news', methods=['GET', 'POST'])
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()  # ORM-модель News
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)  # слияние сессии с текущим пользователем
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
        else:
            abort(404)
    return render_template('news.html', title='редактирование новости', form=form)


@app.route('/form_sample', methods=['GET', 'POST'])
def from_sample():
    if request.method == 'GET':
        return render_template('User_form.html', title='Форма')
    elif request.method == 'POST':
        f = request.files['file']
        f.save('./static/images/loaded.png')
        myform = request.form.to_dict()
        return render_template('filled_form.html',
                               title='ваши данные',
                               data=myform)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', title='Повторная авторизация', message='Неверный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/cookie_test')
def cookie_test():
    visit_count = int(request.cookies.get('visit_count', 0))
    if visit_count != 0 and visit_count <= 20:
        res = make_response(f'Были уже {visit_count + 1} раз')
        res.set_cookie('visit_count', str(visit_count + 1), max_age=60 * 60 * 365 * 2)
    elif visit_count > 20:
        res = make_response(f'Были уже {visit_count + 1} раз')
        res.set_cookie('visit_count', '1', max_age=0)
    else:
        res = make_response('Вы впервые здесь за 2 года')
        res.set_cookie('visit_count', '1', max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route('/session_test')  # сесия живет в кукисах но в зашифрованном виде
def session_test():
    visit_count = session.get('visit_count', 0)
    session['visit_count'] = visit_count + 1
    if session['visit_count'] > 3:
        session.pop('visit_count', None)
    session.permanent = True  # данный способ позволяет не убивать сессию при закрытии браузера, но максимум 31 день
    return make_response(f'Мы тут были уже {visit_count + 1} раз')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html',
                                   title='Проблемы с регистрацией',
                                   message='Пароли не совпадают',
                                   form=form)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html',
                                   title='Проблемы с регистрацией',
                                   message='Такой пользователь уже есть',
                                   form=form)
        user = User(name=form.name.data, email=form.email.data, about=form.about.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


if __name__ == '__main__':
    db_session.global_init('db/news.sqlite')
    app.run(host='127.0.0.1', port=5000, debug=True)
