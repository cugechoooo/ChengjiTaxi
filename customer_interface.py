import streamlit as st
import psycopg2


def show_customer_interface():
    user_id = st.session_state['user_id']
    st.write('用户id：', user_id)

    # 数据库连接配置
    hostname = 'localhost'
    port = 5432
    database = 'chengji_special_car'  # 请替换为您的数据库名称
    username = 'postgres'
    password = '123456@cug'

    # 连接到PostgresSQL数据库
    conn = psycopg2.connect(
        host=hostname,
        port=port,
        dbname=database,
        user=username,
        password=password

    )
    cur = conn.cursor()

    # 定义行程分析函数
    def analyze_trip(user_id, start_location, end_location, reservation_date, reservation_time):
        cur.execute("SELECT driver_id FROM drivers WHERE city=%s", (start_location,))
        driver = cur.fetchone()

        if driver is None:
            st.error("无合适的专车司机")
            return False, None, None
        else:
            cur.execute(
                "INSERT INTO orders (user_id, driver_id, start_location, end_location, reservation_date, "
                "reservation_time, status, city, trip_distance) VALUES (%s, %s, %s, %s, %s, %s, '待确认', %s, "
                "45) RETURNING driver_id, order_id",
                (user_id, driver[0], start_location, end_location, reservation_date, reservation_time, start_location))
            conn.commit()

            row = cur.fetchone()
            if row:
                driver_id, order_id = row
                st.success("预约成功")
                return True, driver_id, order_id
            else:
                return False, None, None

    # 页面1：专车预约
    def page_1(user_id):
        st.header("专车预约")
        start_location = st.text_input("出发地")
        end_location = st.text_input("目的地")
        reservation_date = st.date_input("出发日期")
        reservation_time = st.time_input("出发时间")
        if st.button("预约用车"):
            isTripOk, driver_id, orders_id = analyze_trip(user_id, start_location, end_location, reservation_date,
                                                          reservation_time)
            if isTripOk:
                # 向trips表中新建一行数据
                cur.execute("INSERT INTO trips (order_id, status) VALUES (%s, '待确认') RETURNING trip_id",
                            (orders_id,))
                trip_row = cur.fetchone()
                if trip_row:
                    trip_id = trip_row[0]
                    # 在reviews表中创建一行新纪录
                    cur.execute("INSERT INTO reviews (user_id, trip_id) VALUES (%s, %s)",
                                (user_id, trip_id))
                    conn.commit()
                    # 返回预约用车页面
                    st.write("返回预约用车页面")
                else:
                    st.error("创建行程失败")
            else:
                st.error("无适合司机，请重新预约")

    # 页面2：行程评价
    def page_2(user_id):
        st.header("行程评价")

        # 从reviews表中查询待评价记录
        cur.execute("SELECT * FROM reviews WHERE user_id=%s AND rating IS NULL", (user_id,))
        review_data = cur.fetchone()

        if review_data:
            trip_id = review_data[2]

            # 根据trip-id在trips表中获取order-id
            from chengji_special_car_script import get_order_id
            order_id = get_order_id(trip_id)

            if order_id:
                # 从orders表中找到order-id所在的一行
                cur.execute("SELECT * FROM orders WHERE order_id=%s", (order_id,))
                order_data = cur.fetchone()

                if order_data:
                    driver_id = order_data[2]
                    from chengji_special_car_script import get_driver_name
                    driver_name = get_driver_name(driver_id)  # 获取司机姓名

                    # 展示行程信息
                    st.write(f"订单ID: {order_data[0]}")
                    st.write(f"司机ID: {order_data[2]}")
                    st.write(f"司机姓名: {driver_name}")
                    st.write(f"出发地点: {order_data[3]}")
                    st.write(f"终点: {order_data[4]}")
                    st.write(f"出发日期: {order_data[5]}")
                    st.write(f"出发时间: {order_data[6]}")
                    st.write(f"行程距离: {order_data[9]} 公里")

                    # 评价输入
                    rating = st.slider("评分", 1, 5)
                    review_text = st.text_input("评价")

                    if st.button("确认评价"):
                        cur.execute("UPDATE reviews SET rating=%s, review_text=%s WHERE user_id=%s AND trip_id=%s",
                                    (rating, review_text, user_id, trip_id))
                        conn.commit()
                        st.success("评价完成")
                else:
                    st.warning("未找到订单信息")
            else:
                st.warning("未找到订单ID")
        else:
            st.warning("无可评价行程")

    # 页面3：编辑资料
    def page_3(user_id):
        st.header("编辑资料")
        # 从数据库中读取用户信息
        cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        user_info = cur.fetchone()
        # 显示用户信息的输入框
        username = st.text_input("用户名", value=user_info[1])
        password = st.text_input("密码", value=user_info[2], type="password")
        user_type = st.selectbox("用户类型", ["用车人", "管理员", "专车司机"],
                                 index=["用车人", "管理员", "专车司机"].index(user_info[3]))
        name = st.text_input("姓名", value=user_info[4])
        phone = st.text_input("电话", value=user_info[5])
        address = st.text_input("地址", value=user_info[6])
        city = st.text_input("城市", value=user_info[7])

        if st.button("确认修改"):
            cur.execute(
                "UPDATE users SET username=%s, password=%s, user_type=%s, name=%s, phone=%s, address=%s, "
                "city=%s WHERE user_id=%s",
                (username, password, user_type, name, phone, address, city, user_id))
            conn.commit()
            st.success("修改成功")

    # 页面4：支付
    def page_4(user_id):
        st.header("支付")
        # 从数据库中查询用户的未支付订单
        cur.execute("SELECT * FROM orders WHERE user_id=%s AND status='待支付'", (user_id,))
        unpaid_orders = cur.fetchall()

        if unpaid_orders:
            # 显示未支付订单信息
            for order in unpaid_orders:
                st.write(f"订单ID: {order[0]}")
                st.write(f"出发地: {order[3]}")
                st.write(f"目的地: {order[4]}")
                st.write(f"行程距离: {order[9]} 公里")
                st.write(f"费用: {order[9] * 2.5} 元")  # 假设每公里2.5元
                st.write("----------")

            # 添加一个支付按钮
            if st.button("模拟支付"):
                # 更新所有未支付订单的状态为已支付
                for order in unpaid_orders:
                    cur.execute("UPDATE orders SET status='已支付' WHERE order_id=%s", (order[0],))
                    conn.commit()
                st.success("支付成功")
        else:
            st.info("没有未支付的订单")

    # 主程序
    # 选择页面
    page = st.sidebar.selectbox("选择页面", ["专车预约", "行程评价", "编辑资料", "支付"])
    if page == "专车预约":
        page_1(user_id)
    elif page == "行程评价":
        page_2(user_id)
    elif page == "编辑资料":
        page_3(user_id)
    elif page == "支付":
        page_4(user_id)

    '''
    elif page=="退出登录":
        from chengji_special_car_script import session_init
        session_init()
        st.experimental_rerun()# 强制刷新
        cur.close()
        conn.close()
    '''

    # 关闭数据库连接
    cur.close()
    conn.close()
