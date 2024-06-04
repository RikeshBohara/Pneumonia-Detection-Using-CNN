from flask import Flask, render_template, request, redirect, url_for, session
import tensorflow as tf
from keras.utils import load_img
from keras_preprocessing.image import img_to_array
from keras.models import load_model
import numpy as np
from flask_mysqldb import MySQL

def get_current_username():
    return session.get('username')

Model_Path= 'models/model.h5'
model = load_model(Model_Path)

app = Flask(__name__)
app.secret_key = 'asdfgh'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='pneumonia'

mysql = MySQL(app)

Model_Path= 'models/model.h5'
model = load_model(Model_Path)

@app.route('/',methods=['GET'])
def home():
    if 'username' in session:
        return render_template('home.html',  username=session['username'])
    else:
        return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute(f'select username, password from users where username="{username}"')
        user = cur.fetchone()
        cur.close()
        if user and pwd == user[1]:
            session['username'] = user[0]
            return redirect(url_for('predict'))
        else:
            return render_template('login.html', error='Invalid username or password')
        
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        pwd = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute(f"select * from users where username = '{username}' or email = '{email}'")
        user = cur.fetchone()
        cur.close()

        if user:
            return render_template('register.html', error='Username or email already exists')
        
        cur = mysql.connection.cursor()
        cur.execute(f"insert into users (name, email, username, password) values ('{name}', '{email}', '{username}', '{pwd}')")
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cur = mysql.connection.cursor()
        cur.execute(f"select password from users where username = '{session['username']}'")
        user = cur.fetchone()
        cur.close()

        if user and old_password == user[0]:
            if new_password == confirm_password:
                cur = mysql.connection.cursor()
                cur.execute(f"UPDATE users SET password = '{new_password}' WHERE username = '{session['username']}'")
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('predict'))
            else:
                return render_template('change_password.html', error='New passwords do not match')
        else:
            return render_template('change_password.html', error='Incorrect current password')
    return render_template('change_password.html')

@app.route('/precision')
def precision():
    username = get_current_username()
    print("precision route called")
    return render_template("precision.html",username=username)

@app.route('/about')
def about():
    username = get_current_username()
    print("about route called")
    return render_template("about.html", username=username)

@app.route('/index', methods=['POST', 'GET'])
def predict():
    username = get_current_username()
    if request.method == 'POST':
        if 'imagefile' in request.files:
            imagefile = request.files["imagefile"]
            if imagefile:
                image_path = './static/uploads/' + imagefile.filename
                imagefile.save(image_path)
                img = load_img(image_path, target_size=(224, 224), color_mode='rgb')
                x = img_to_array(img)
                x = x / 255
                x = np.expand_dims(x, axis=0)
                classes = model.predict(x)
                result1 = classes[0][0]
                result2 = 'NORMAL LUNGS'
                if result1 >= 0.5:
                    result2 = 'PNUEMONIC LUNGS'
                classification = '%s (%.2f%%)' %(result2, result1*100)
                return render_template('index.html', prediction=classification, imagePath=image_path, username=username)
    return render_template('index.html', username=username)

if __name__ == '__main__':
    app.run(port=5000,debug=True)