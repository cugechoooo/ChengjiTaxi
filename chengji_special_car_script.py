import time
import streamlit as st
import psycopg2
from psycopg2 import Error
import customer_interface
import driver_interface
import admin_interface

#                    streamlit run chengji_special_car_script.py
#         streamlit run chengji_special_car_script.py --server.enableCORS false
#         streamlit run chengji_special_car_script.py --browser.serverAddress=localhost --server.port=8502
# git remote add origin https://github.com/cugechoooo/ChengjiTaxi.git

# 数据库连接配置
hostname = 'localhost'
port = 5432
database = 'chengji_special_car'  # 请替换为您的数据库名称
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

# 获取数据库连接
connection = init()

# 注册新用户
def register_user(connection, user_type, username, password,city):
    cursor = connection.cursor()
    try:
        # 直接存储密码的明文
        cursor.execute("INSERT INTO users (user_type, username, password,city) VALUES (%s, %s, %s, %s)",
                       (user_type, username, password, city))
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
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        stored_tuple = cursor.fetchone()

        if stored_tuple is not None and stored_tuple[2] == password:
            return stored_tuple[3]        #元组第4列为用户身份
        else:
            return False
    except Error as e:
        print(f"登录失败: {e}")
        return False
    finally:
        cursor.close()

# 定义常量
INITIAL_STATE = 'initial'
REGISTER_STATE = 'register'
LOGIN_STATE = 'login'

# 初始状态
# 初始化session
if 'state' not in st.session_state:
    st.session_state['state'] = INITIAL_STATE
    st.session_state['user_id'] = None

# 显示页面标题
st.title('嘟嘟打车服务平台')

empty = st.empty()

def get_id(connection, username):
    cur = connection.cursor()
    cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    result = cur.fetchone()  # 获取查询结果
    if result:  # 如果查询有结果
        user_id = result[0]  # 获取user_id
        return user_id
    else:
        return None  # 如果没有结果，则返回 None 或者其他适合的值

def get_driver_name(driver_id):
    # 从数据库中获取driver姓名
    cur = connection.cursor()
    cur.execute("SELECT name FROM drivers WHERE driver_id = %s", (driver_id,))
    result = cur.fetchone()
    if result:
        return result[0]  # 此处sql语句查询的就是name，不用result[1]
    else:
        return "Unknown"

def get_order_id(trip_id):
    # 从数据库中获取order_id
    cur = connection.cursor()
    cur.execute("SELECT order_id FROM trips WHERE trip_id = %s", (trip_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return None

def session_init():
    st.session_state['state'] = INITIAL_STATE
    st.session_state['user_id'] = None

# 登录状态
if st.session_state['state'] == LOGIN_STATE:
    username = st.text_input('请输入用户名', key='username')
    password = st.text_input('请输入密码', type='password', key='password')
    st.write('用户名',username)
    st.write('密码',password)
    user_type = login_user(connection, username, password)
    # 获取user_id
    user_id = get_id(connection, username)  # 传入连接和用户名参数来获取用户 ID
    st.session_state['user_id'] = user_id
    if user_id:  # 如果能够成功获取用户 ID
        st.write('用户id：', user_id)
        st.session_state.user_id = user_id    # user_id存入
    else:
        st.write('没有找到对应的用户id')  # 如果没有结果，则输出提示信息
    st.write(user_type)
    if user_type == '用车人':
        # 在需要的地方添加延迟
        # time.sleep(1)  # 延迟一秒钟

        empty.empty()
        st.write('欢迎您，',username)

        customer_interface.show_customer_interface()
        st.experimental_set_query_params(page='customer_interface')

    elif user_type == '专车司机':
        empty.empty()
        st.text('专车司机界面')  # 更新empty的内容
        # time.sleep(1)  # 延迟一秒钟
        # st.experimental_rerun()  # 强制刷新
        st.write('欢迎您，', username)
        driver_interface.show_driver_interface()
        st.experimental_set_query_params(page='driver_interface')

    elif user_type == '平台管理员':
        empty.empty()
        st.text('平台管理员界面')  # 更新empty的内容
        # time.sleep(1)  # 延迟一秒钟
        # st.experimental_rerun()  # 强制刷新
        st.write('欢迎您，', username)
        admin_interface.show_admin_interface()
        st.experimental_set_query_params(page='admin_interface')

    else:
        empty.empty()
        st.error('登录失败，请检查用户名和密码。')
        st.session_state['state'] = INITIAL_STATE
        time.sleep(1)  # 延迟一秒钟
        # st.experimental_rerun()  # 强制刷新
    # cur.close()


# 注册状态
elif st.session_state['state'] == REGISTER_STATE:

    st.header('注册')
    empty.empty()
    new_username = st.text_input('请输入用户名', key='new_username')
    new_password = st.text_input('请输入密码', type='password', key='new_password')
    new_usertype = st.selectbox('请选择您的身份', ('用车人', '专车司机', '平台管理员'), key='user_type_select')
    city = st.text_input('请输入城市')
    if st.button('注册', key='register_button'):
        # register_or_not=register_user(connection, new_usertype, new_username, new_password,city)
        if register_user(connection, new_usertype, new_username, new_password,city):
            st.success('注册成功！')
            time.sleep(1)  # 等待1秒
            st.session_state['state'] = INITIAL_STATE
            st.experimental_rerun()
        else:
            st.error('注册失败，请重试。')
            time.sleep(1)  # 等待1秒
            st.session_state['state'] = INITIAL_STATE
            st.experimental_rerun()

# 初始页面
else:
    st.header('欢迎来到嘟嘟打车服务平台')
    username = st.text_input('请输入用户名', key='username')
    password = st.text_input('请输入密码', type='password', key='password')

    if st.button('登录', key='login_button'):
        st.session_state['state'] = LOGIN_STATE
        empty.empty()  # 清空 empty 的内容
        # st.experimental_rerun()  # 重新运行整个应用程序
    elif st.button('注册', key='register_button'):
        st.session_state['state'] = REGISTER_STATE
        empty.empty()  # 清空 empty 的内容
        # st.experimental_rerun()  # 重新运行整个应用程序

