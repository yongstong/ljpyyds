import pymysql
from .index import encrypt_key
from datetime import datetime
from gmssl import sm3,func
import secrets
from .sm2key import create_key_pair


conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='615911321',
    db='mmweb',
    )



def creat(password):        
    password_bytes = password
    salt = secrets.token_hex(32)
    salted_password = salt + password_bytes
    # print(salted_password)
    hash_value =sm3.sm3_hash(func.bytes_to_list(salted_password.encode("utf-8")))
    # print(salt+"\n"+hash_value)
    return salt,hash_value

def userlogsql():
    cur = conn.cursor()
    sql = "SELECT * FROM login_log "
    cur.execute(sql)
    content  = cur.fetchall()
    cur.close()
    return content

def usersql():
    cur = conn.cursor()
    sql = "SELECT users,name,level,gp,phone,email,pw FROM user_info "
    cur.execute(sql)
    content  = cur.fetchall()
    cur.close()
    return content
 
def key_pubilc_sql(recuser):
    cur = conn.cursor()
    sql = "SELECT gongyao FROM key WHERE users = '%s' "%(recuser)
    cur.execute(sql)
    content  = cur.fetchall()
    cur.close()
    return content[0][0]

def adduser(id,password,rename,email,phone):
    salt,hash_value = creat(password)
    cur = conn.cursor()
    sql = "INSERT INTO user_info (users,salt,pw,name,level,gp,phone,email) VALUES (%s, %s, %s, %s,'0','0', %s, %s)"
    cur.execute(sql,(id,salt,hash_value,rename,phone,email))
    conn.commit()
    private_key, public_key = create_key_pair()
    private_key_en = encrypt_key(password,private_key)
    creattime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = "INSERT INTO key_use (users,siyao,gongyao,creattime,survivaltime) VALUES ('%s', '%s', '%s', '%s',240)"%(id,private_key_en,public_key,creattime)
    print(sql)
    cur.execute(sql)
    conn.commit()
    cur.close()
    return 0

def addloguser(username):
    cur = conn.cursor()
    sql = "SELECT name FROM user_info WHERE users = '%s' "%(username)
    cur.execute(sql)
    content  = cur.fetchall()
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = "INSERT INTO login_log (users,name,logtime) VALUES (%s, %s, %s)"
    cur.execute(sql,(username,content[0][0],time))
    conn.commit()
    cur.close()
    
def sendlogsql():
    cur = conn.cursor()
    sql = "SELECT * FROM mes_log "
    cur.execute(sql)
    messages  = cur.fetchall()
    print(messages)
    cur.close()
    return messages

def keysql(username):
    cur = conn.cursor()
    sql = "SELECT gongyao,siyao,creattime,survivaltime FROM key_use WHERE users = '%s' "%(username)
    cur.execute(sql)
    messages  = cur.fetchall()
    cur.close()
    return messages

def recsql(username):
    cur = conn.cursor()
    sql = "SELECT senduser,title,sendtime FROM mes_log WHERE recuser = '%s' "%(username)
    cur.execute(sql)
    messages  = cur.fetchall()
    cur.close()
    return messages