import streamlit as st
import psycopg2
from psycopg2 import Error
import hashlib
import binascii
import os

# 数据库连接配置
hostname = 'localhost'
port = 5432
database = 'chengji_special_car'
username = 'postgres'
password = '123456@cug'

# 初始化数据库连接
def init():
    try:
        connection = psycopg2.connect(
            host=hostname,
            port=port,
            dbname=database,
            user=username,
            password=password
        )
        print("数据库连接成功")
    except Error as e:
        print(f"数据库连接失败: {e}")
        connection = None
    return connection

# 创建密码的哈希值
def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    password_hash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    password_hash = binascii.hexlify(password_hash)
    return (salt + password_hash).decode('ascii')

# 验证密码
def verify_password(stored_password, provided_password):
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

# 注册新用户
def register_user(connection, user_type, username, password):
    cursor = connection.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (user_type, username, password) VALUES (%s, %s, %s)",
                       (user_type, username, password_hash))
        connection.commit()
        return True
    except Error as e:
        print(f"注册用户失败: {e}")
        return False
    finally:
        cursor.close()

# 用户登录
def login_user(connection, username, password):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        stored_password = cursor.fetchone()
        if stored_password and verify_password(stored_password[0], password):
            return True
        else:
            return False
    except Error as e:
        print(f"登录失败: {e}")
        return False
    finally:
        cursor.close()

# 设置页面标题
st.title('橙际专车服务平台')

# 判断用户身份
user_type = st.sidebar.selectbox('请选择您的身份', ('用车人', '专车司机', '平台管理员'))

# 注册或登录
register_or_login = st.sidebar.selectbox('请选择操作', ('注册', '登录'))

# 获取数据库连接
connection = init()

# 注册或登录逻辑
if register_or_login == '注册':
    st.subheader('注册')
    new_username = st.text_input('请输入用户名')
    new_password = st.text_input('请输入密码', type='password')
    if st.button('注册'):
        if register_user(connection, user_type, new_username, new_password):
            st.success('注册成功！')
        else:
            st.error('注册失败，请重试。')
elif register_or_login == '登录':
    st.subheader('登录')
    username = st.text_input('请输入用户名')
    password = st.text_input('请输入密码', type='password')
    if st.button('登录'):
        if login_user(connection, username, password):
            st.success(f'欢迎，{username}！')
            # 这里可以根据user_type跳转到不同的页面
            if user_type == '用车人':
                st.write('用车人界面')
            elif user_type == '专车司机':
                st.write('专车司机界面')
            elif user_type == '平台管理员':
                st.write('平台管理员界面')
        else:
            st.error('登录失败，请检查用户名和密码。')

# 预约专车的数据库操作
def reserve_car(start_location, end_location, date, time):
    connection = init()
    if connection:
        try:
            cursor = connection.cursor()
            # 创建插入预约的SQL语句
            insert_query = "INSERT INTO reservations (start_location, end_location, date, time) VALUES (%s, %s, %s, %s)"
            # 执行SQL语句
            cursor.execute(insert_query, (start_location, end_location, date, time))
            # 提交事务
            connection.commit()
            print("预约信息已存储在数据库中")
        except Error as e:
            print(f"数据库操作失败: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()
