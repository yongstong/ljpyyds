import pymysql

conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='615911321',
    db='mmweb',
    )
cur = conn.cursor()

def null(username,password):
	if(username==''or password==''):
		return True
	else:
		return False


def existed(username,password):
	sql = "SELECT * FROM user_info WHERE user ='%s' and mima ='%s'"%(username,password)
	cur.execute(sql)
	result = cur.fetchall()
	if (len(result) == 0):
		return False
	else:
		return True
    
def exist_user(username):
	sql = "SELECT * FROM user_info WHERE 	users	 ='%s'" % (username)
	cur.execute(sql)
	result = cur.fetchall()
	if (len(result) == 0):
		return False
	else:
		return True
