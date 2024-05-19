from flask import Flask,jsonify
from flask import request
from flask import redirect,url_for
from flask import render_template, send_from_directory,send_file
from model.check import null,exist_user
from model.sqlsen import userlogsql,usersql,adduser,addloguser,sendlogsql,keysql,recsql
from model.index import correct,sm4_text
from flask_login import current_user, login_user,LoginManager,login_required, logout_user,UserMixin
import secrets
from gevent import pywsgi
import pymysql
import os
from datetime import datetime




conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='615911321',
    db='mmweb',
    )

app = Flask(__name__)
login_manager = LoginManager(app)
app.secret_key = secrets.token_hex(32)


class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/',methods=['GET','POST'])
def a():
    return render_template('login.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':  # 注册发送的请求为POST请求
        username = request.form['username']
        password = request.form['password']
        
        #和sql数据库比较用户名密码
        if correct(username,password):
            #账号密码正确
            user = User(username)
            login_user(user)
            addloguser(username)
            return redirect(url_for('index'))
        else:
            #账号密码不正确
            login_massage = "用户名或账号错误"
            return render_template("login.html",message=login_massage) 
    return render_template("login.html")


@app.route('/regist',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        id	 = request.form['username']
        password = request.form['password']
        rename = request.form['rename']
        email = request.form['email']
        phone = request.form['telphone']
        if null(id,password):
            login_massage = "温馨提示：账号和密码是必填"
            return render_template('regist.html', message=login_massage)
        elif exist_user(id):
            login_massage = "温馨提示：用户已存在，请直接登录"
            # return redirect(url_for('user_login'))
            return render_template('regist.html', message=login_massage)
        else:
            adduser(id,password,rename,email,phone)
            render_template('login.html')
    return render_template('regist.html')


@app.route('/index',methods=['GET','POST'])
@login_required  # 登录保护
def index():
    print(current_user.id)
    return render_template('index.html')

@app.route('/user',methods=['GET','POST'])
def user():
    content = usersql()
    return render_template('user.html',info = content)

@app.route('/loguser',methods=['GET','POST'])
@login_required
def loguser():
    content = userlogsql()
    return render_template('loguser.html',info = content)

@app.route('/logsend',methods=['GET','POST'])
@login_required
def logsend():
    messages = sendlogsql()
    return render_template('logsend.html',messages = messages)

@app.route('/send',methods=['GET','POST'])
def send():
    return render_template('send.html',)

@app.route('/rec',methods=['GET','POST'])
def rec():
    content = recsql(current_user.id)
    return render_template('rec.html',messages = content)

@app.route('/key',methods=['GET','POST'])
def key():
    content = keysql(current_user.id)
    return render_template('key.html',messages = content)

@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    return redirect(url_for('login'))  # 重定向回首页

@app.route('/delete_row', methods=['POST','GET'])
def delete_row():
    # 获取前端发送的需要删除的行的标识符
    data = request.json
    row_id = data.get('id')
    try:
        # 执行删除操作，这里假设你有一个名为 user_info 的表，其中有一个字段为 id 用于标识每一行数据
        # 你需要根据自己的数据库表结构和需要执行的操作来修改这里的 SQL 语句
        cursor = conn.cursor()
        sql = "DELETE FROM user_info WHERE users = '%s'"%(row_id)
        # print(sql)
        cursor.execute(sql)
        conn.commit()  # 提交事务
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        conn.rollback()  # 发生异常时回滚事务
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()  # 关闭游标



@app.route('/download/<filename>', methods=['GET','POST'])
def download(filename):
    cursor = conn.cursor()
    sql = "SELECT downurl FROM message WHERE title = '%s'" % filename
    cursor.execute(sql)
    con = cursor.fetchall()
    file = con[0][0].split('\\', 1)[-1]
    cursor.close()  # 关闭游标
    return send_from_directory(app.config['UPLOAD_FOLDER'], file, as_attachment=True)



@app.route('/form', methods=['GET', 'POST'])
def upload_form():
    if request.method == 'POST':
        # 获取文件
        uploaded_file = request.files['file']

        # 获取表单数据
        text = request.form['con']
        title = request.form['title']
        recuser = request.form['recuser']
        current_time =  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 假设你还有其他需要接收的表单数据，也可以通过类似的方法获取

        # 保存文件到服务器
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
        
        key_A,hash_A,url = sm4_text(file_path,recuser)
        # try:
            # 执行数据库操作，将文件路径、账号、密码等信息保存到数据库中
            
        cursor = conn.cursor()
        sql = "INSERT INTO message (senduser,recuser,title, messageinfo, downurl,key_A,hash) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (current_user.id, recuser, title,text,url,key_A.hex(),hash_A))
        conn.commit()
        sql = "INSERT INTO mes_log (title,senduser,recuser,sendtime,ov) VALUES (%s, %s, %s, %s, '0')"
        cursor.execute(sql, (title,current_user.id, recuser,current_time))
        conn.commit()
        return render_template('index.html')
        # except Exception as e:
        #     conn.rollback()
        #     return '上传失败：{}'.format(str(e))
        # finally:
        #     cursor.close()

    return render_template('send.html')

if __name__ == '__main__':
    # server = pywsgi.WSGIServer(('127.0.0.1', 5000), app)
    # server.serve_forever()  
    app.config['UPLOAD_FOLDER'] = 'download'
    app.run(debug=True,host='127.0.0.2') #127.0.0.1 回路 自己返回自己