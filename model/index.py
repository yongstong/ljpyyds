import pymysql
from gmssl import sm3,func,sm4,sm2
import secrets
import os

conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='615911321',
    db='mmweb',
    )
cur = conn.cursor()

def key_pubilc_sql(recuser):
    sql = "SELECT gongyao FROM key_use WHERE users = '%s' "%(recuser)
    cur.execute(sql)
    content  = cur.fetchall()
    return content[0][0]

def correct(username,password):
    sql = "SELECT salt,pw FROM user_info WHERE  users ='%s' "%(username)
    cur.execute(sql)
    result = cur.fetchall()
    
    if not result:  # 如果没有找到对应数据
        return False
        
    salted_password = result[0][0] + password
    hash_value =sm3.sm3_hash(func.bytes_to_list(salted_password.encode("utf-8")))
    if hash_value == result[0][1]:
        return True
    else:
        return False
    

def sm4_encrypt(file_path, key, iv):
    if len(key) != 32:
        raise ValueError("Key must be 32 hex digits long (16 bytes).")
    if len(iv) != 32:
        raise ValueError("IV must be 32 hex digits long (16 bytes).")
    
    key_bytes = bytes.fromhex(key)
    iv_bytes = bytes.fromhex(iv)
    crypt_sm4 = sm4.CryptSM4()
    crypt_sm4.set_key(key_bytes, sm4.SM4_ENCRYPT)
    print(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()

    # 填充数据以确保其长度是16的倍数
    padding_length = 16 - len(file_data) % 16
    file_data += bytes([padding_length] * padding_length)#采用的是PKCS#7填充标准

    encrypted_data = crypt_sm4.crypt_cbc(iv_bytes, file_data)  # 使用CBC模式加密
    encrypted_file_path = file_path + '.encrypted'

    with open(encrypted_file_path, 'wb') as f:
        f.write(encrypted_data)

    return encrypted_file_path

def sm4_decrypt(file_path, key, iv):
    if len(key) != 32:
        raise ValueError("Key must be 32 hex digits long (16 bytes).")
    if len(iv) != 32:
        raise ValueError("IV must be 32 hex digits long (16 bytes).")

    key_bytes = bytes.fromhex(key)
    iv_bytes = bytes.fromhex(iv)
    crypt_sm4 = sm4.CryptSM4()
    crypt_sm4.set_key(key_bytes, sm4.SM4_DECRYPT)

    with open(file_path, 'rb') as f:
        file_data = f.read()

    decrypted_data = crypt_sm4.crypt_cbc(iv_bytes, file_data)  # 使用CBC模式解密

    # 移除填充
    padding_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-padding_length]

    decrypted_file_path = file_path + '.decrypted'

    with open(decrypted_file_path, 'wb') as f:
        f.write(decrypted_data)

    return decrypted_file_path

# 使用示例：
def generate_iv(seed):
    # 使用 SM3 哈希种子
    hash_value = sm3.sm3_hash(func.bytes_to_list(seed.encode()))
    # 取哈希值的前32个十六进制字符（16字节）
    iv_hex = hash_value[:32]
    # 将十六进制字符串转换为字节
    iv_bytes = bytes.fromhex(iv_hex)
    return iv_bytes

def hash_text(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()  # 读取文件内容

        hash_value = sm3.sm3_hash(func.bytes_to_list(data))  # 计算文件的 SM3 哈希值
        return hash_value
    
#已废弃    
# def generate_sm2_keypair():
#     private_key = sm2.CryptSM2.private_key_generate()
#     sm2_crypt = sm2.CryptSM2(public_key='', private_key=private_key)
#     public_key = sm2_crypt.get_public_key()
#     return private_key, public_key

# 使用SM2公钥加密对称密钥
def sm2_encrypt_key(symmetric_key, public_key):
    sm2_crypt = sm2.CryptSM2(
        public_key=public_key,
        private_key=''  # 解密时不需要私钥
    )
    encrypted_key = sm2_crypt.encrypt(symmetric_key)
    return encrypted_key

# 使用SM2私钥解密对称密钥
def sm2_decrypt_key(encrypted_key, private_key):
    sm2_crypt = sm2.CryptSM2(
        public_key='',  # 加密时不需要公钥
        private_key=private_key
    )
    decrypted_key = sm2_crypt.decrypt(encrypted_key)
    return decrypted_key
    
def hash_login_password(password):
    """ 使用SM3对密码进行哈希处理，并截取前128位作为密钥 """
    hash_value = sm3.sm3_hash(func.bytes_to_list(password.encode()))
    return bytes.fromhex(hash_value[:32])  # 取前32个十六进制字符，即128位

def encrypt_key(password, data):
    """ 基于口令生成密钥并加密数据 """
    key = hash_login_password(password)
    crypt_sm4 = sm4.CryptSM4()
    crypt_sm4.set_key(key, sm4.SM4_ENCRYPT)
    
    
    encrypted_data = crypt_sm4.crypt_ecb(data.encode())
    return encrypted_data.hex()
    
def decrypt_key(password, encrypted_data):
    """ 基于口令生成密钥并解密数据 """
    key = hash_login_password(password)
    crypt_sm4 = sm4.CryptSM4()
    crypt_sm4.set_key(key, sm4.SM4_DECRYPT)
    
    decrypted_data = crypt_sm4.crypt_ecb(encrypted_data)

    print(decrypted_data)
    return decrypted_data

def sm4_text(file,recuser):
    
    iv = generate_iv(recuser)
    key = secrets.token_hex(16) 
    url =  sm4_encrypt(file,key,iv.hex())
    key_pubilc = key_pubilc_sql(recuser)
    hash_A = hash_text(url)
    key_A = sm2_encrypt_key(key.encode(),key_pubilc)
    os.remove(file)
    return key_A,hash_A,url








if __name__ == "__main__":
    key = '1234567890abcdef1234567890abcdef'  # 确保密钥是32个十六进制字符，即16字节
    iv = 'abcdef1234567890abcdef1234567890'  # 初始化向量也必须是32个十六进制字符，即16字节
    original_file = r'C:\Users\yyt\Documents\python work\web\sjkweb\download\387423-古今相和，和而不同-项目作品-0f544fa6.pdf'  # 文件路径

    # 加密文件
    encrypted_file = sm4_encrypt(original_file, key, iv)
    print(f"Encrypted file created: {encrypted_file}")

    # 解密文件
    decrypted_file = sm4_decrypt(encrypted_file, key, iv)
    print(f"Decrypted file created: {decrypted_file}")
    
    
    # correct("20211401","615911321")
