#from crypt import methods
#from crypt import methods
from hashlib import sha256
from msilib import Table
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from sqlHelper import *
from forms import *
from functools import wraps
import time

app = Flask(__name__)

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "UNICORN"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"
app.secret_key = 'secret123'

mysql = MySQL(app)

def isLoggedIn(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized! Please log in!', 'danger')
            return redirect(url_for('login'))

    return wrap


def loginUser(username):
    users = Table("users", "name", "email", "username", "password")
    user = users.getOne("username", username)

    session['logged_in'] = True
    session['username'] = username
    session['name'] = user.get('name')
    session['email'] = user.get('email')



@app.route('/register', methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    users = Table("users", "name", "email", "username", "password")
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data

        if isNewUser(username): #vedem daca e utilizator nou
            password = sha256_crypt.encrypt(form.password.data)
            users.insert(name,email,username,password)
            loginUser(username)
            return redirect(url_for('dashboard'))
        else:
            flash('Username already exist', 'danger')
            return redirect(url_for('register'))

        
    return render_template('register.html', form = form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        candidate = request.form['password']


        users = Table("users", "name", "email", "username", "password")
        user = users.getOne('username', username)
        if user is None:
            flash('Username is not found', 'danger')
            return redirect(url_for('login'))
        else:
            accpass = user.get('password')

        if accpass is None:
            flash('Username is not found', 'danger')
            return redirect(url_for('login'))
        else:
            if sha256_crypt.verify(candidate, accpass):
                loginUser(username)
                flash('You are now logged in.', 'success')

                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Password', 'danger')

                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/transaction', methods=['GET', 'POST'])
@isLoggedIn
def transaction():
    form = SendMoneyForm(request.form)
    balance = getBalance(session.get('username'))
    if request.method == "POST":
        try:
            send_money(session.get('username'), form.username.data, form.amount.data)
            flash("Money Sent", "success")
        except Exception as e:
            flash(str(e), "danger")
        
        return redirect(url_for('transaction'))

    return render_template('transaction.html', balance = balance, form = form)

@app.route('/buy', methods=['GET', 'POST'])
@isLoggedIn
def buy():
    form = BuyForm(request.form)
    balance = getBalance(session.get('username'))
    if request.method == "POST":
        try:
            send_money("BANK", session.get('username'), form.amount.data)
            flash("Purchase Successful", "success")
        except Exception as e:
            flash(str(e), "danger")
        
        return redirect(url_for('dashboard'))    
        
    return render_template('buy.html', balance=balance, form=form, page='buy')




@app.route('/logout')
@isLoggedIn
def logout():
    session.clear()
    flash("Logout success", "success")
    return redirect(url_for("login"))



@app.route('/dashboard')
@isLoggedIn
def dashboard():
    blockchain = getBlockChain().chain
    ct = time.strftime('%I:%M %p')
    return render_template('dashboard.html',session = session, ct=ct, blockchain = blockchain, page='dashboard')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    
    app.run(debug=True)