import streamlit as st
import psycopg2
from chengji_special_car_script import get_driver_name

def show_admin_interface():

    # 连接到PostgreSQL数据库
    conn = psycopg2.connect(
        dbname="chengji_special_car",
        user="postgres",
        password="123456",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()

    # 页面一：专车组织与管理
    def page_1():
        st.header("专车组织与管理")
        cur.execute("SELECT driver_id, name, license_number, vehicle_plate FROM drivers")
        data = cur.fetchall()
        st.table(data)

    # 页面二：制定用车计划
    def page_2():
        st.header("制定用车计划")
        st.write("暂无计划")

    # 页面三：用车服务追踪与评价
    def page_3():
        st.header("用车服务追踪与评价")
        cur.execute("SELECT trip_id, AVG(rating) AS avg_rating FROM reviews GROUP BY trip_id")
        trip_ratings = cur.fetchall()
        for trip_id, avg_rating in trip_ratings:
            # 通过trip-id查询trips表中的order-id
            # 通过order-id查询orders表中的driver-id
            # 通过get_driver_name(driver_id)获取司机名字
            driver_name = get_driver_name(trip_id)  # 假设有一个名为get_driver_name的函数用于获取司机名字
            st.write(f"{driver_name}: 平均分 {avg_rating}")

    # 页面四：第三方支付服务
    def page_4():
        st.header("第三方支付服务")
        st.write("暂无想法")

    # 页面五：订单管理
    def page_5():
        st.header("订单管理")
        cur.execute("SELECT * FROM orders")
        orders = cur.fetchall()
        for order in orders:
            driver_name = get_driver_name(order[2])  # 假设有一个名为get_driver_name的函数用于获取司机名字
            st.write(f"{driver_name}, 订单详情: {order}")

    # 选择页面
    page = st.sidebar.selectbox("选择页面",
                                ["专车组织与管理", "制定用车计划", "用车服务追踪与评价", "第三方支付服务", "订单管理","退出登录"])

    # 根据选择的页面显示内容
    if page == "专车组织与管理":
        page_1()
    elif page == "制定用车计划":
        page_2()
    elif page == "用车服务追踪与评价":
        page_3()
    elif page == "第三方支付服务":
        page_4()
    elif page == "订单管理":
        page_5()
    '''
    elif page == "退出登录":
        from chengji_special_car_script import session_init
        session_init()
        st.experimental_rerun()  # 强制刷新
        cur.close()
        conn.close()'''

    # 关闭数据库连接
    cur.close()
    conn.close()





