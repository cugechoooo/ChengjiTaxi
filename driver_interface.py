import streamlit as st
import psycopg2

def show_driver_interface():
    user_id=st.session_state['user_id']
    # Connect to PostgresSQL database
    def connect_to_db():
        try:
            conn = psycopg2.connect(
                dbname="chengji_special_car",
                user="postgres",
                password="123456",
                host="localhost",
                port="5432"
            )
            return conn
        except psycopg2.Error as e:
            st.error(f"Unable to connect to the database: {e}")
            return None

    # Page 1: 申请入会
    def apply_for_membership(conn, username):
        st.title("申请入会")

        # Check if driver exists in database
        cur = conn.cursor()
        cur.execute("SELECT * FROM drivers WHERE name = %s", (username,))
        driver_record = cur.fetchone()

        if driver_record:  # drivers表存在数据行
            # 检查是否数据行全填满
            if all(driver_record[2:]):
                st.success("您已经是城际专车的专车司机.，可以开始接单了!")
                st.write(driver_record)
            else:  # 存在空行
                st.warning("您的资料不完整，无法成为专车司机，请完善您的信息")
                name = st.text_input("姓名:")
                phone = st.text_input("联系方式:")
                address = st.text_input("地址:")
                city = st.text_input("所在城市:")
                license_number = st.text_input("证书号:")
                vehicle_plate = st.text_input("车牌号:")
                if st.button("提交"):
                    cur.execute("""
                        UPDATE drivers 
                        SET name = %s, phone = %s, address = %s, city = %s, license_number = %s, vehicle_plate = %s 
                        WHERE driver_id = %s
                    """, (name, phone, address, city, license_number, vehicle_plate, driver_record[0]))
                    conn.commit()
                    st.success("资料提交成功!")
                    st.write(driver_record)

        else:  # drivers表不存在数据行
            cur.execute("INSERT INTO drivers (name) VALUES (%s) RETURNING driver_id", (username,))
            driver_id = cur.fetchone()[0]
            conn.commit()
            st.success("您已经是城际专车的一名专车司机了!")
            st.write(f"您的专车司机号码：, {driver_id}")

    # Page 2: 订单管理
    def order_management(conn, username):
        st.title("订单管理")

        # Check if driver has any orders
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE driver_id IN (SELECT driver_id FROM drivers WHERE name = %s)",
                    (username,))
        orders = cur.fetchall()

        if orders:
            # Display completed orders
            completed_orders = [order for order in orders if order[7] == '已完成']  # Assuming 'status' is at index 7
            st.write("您的已完成订单:")
            for order in completed_orders:
                st.write(order)

            # Display orders with status '待确认'
            pending_orders = [order for order in orders if order[7] == '待确认']
            if pending_orders:
                st.write("您的待确认订单:")
                for order in pending_orders:
                    st.write(order)
                    # Display buttons to accept or reject the order
                    if st.button("接单"):
                        # Update the order status to '进行中' and create a new service report
                        cur.execute("""
                            UPDATE orders 
                            SET status = '进行中' 
                            WHERE order_id = %s
                        """, (order[0],))  # Assuming 'order_id' is at index 0
                        conn.commit()

                        # Update the corresponding trip status to '进行中'
                        cur.execute("""
                            UPDATE trips 
                            SET status = '进行中' 
                            WHERE order_id = %s
                        """, (order[0],))  # Assuming 'order_id' is the foreign key in trips table
                        conn.commit()

                        st.success("接单成功，请按时开始行程。")

                        # Assuming service_reports is another table
                        cur.execute("""
                            INSERT INTO service_reports (user_id, driver_id, report_details) 
                            VALUES (%s, %s, '')
                        """, (order[1], username))
                        conn.commit()
                        st.write("已创建服务报告。")
                    elif st.button("拒绝订单"):
                        # 检查并删除 reviews 表中引用 trips 表中要删除的记录
                        cur.execute(
                            "DELETE FROM reviews WHERE trip_id IN (SELECT trip_id FROM trips WHERE order_id = %s)",
                            (order[0],))
                        conn.commit()

                        # 现在，可以安全地删除 trips 表中引用该订单的所有记录
                        cur.execute("DELETE FROM trips WHERE order_id = %s", (order[0],))
                        conn.commit()

                        # 最后，删除 orders 表中的记录
                        cur.execute("DELETE FROM orders WHERE order_id = %s", (order[0],))
                        conn.commit()
                        st.success("已拒绝订单。")

                        # 刷新页面
                        st.experimental_rerun()
        else:
            st.write("您目前没有订单。")

        cur.close()

    # Page 3: 服务反馈
    def service_feedback(conn, username):
        st.title("服务反馈")

        # 订单管理
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM orders 
            WHERE driver_id IN (SELECT driver_id FROM drivers WHERE name = %s) 
            AND status = '进行中'
        """, (username,))
        ongoing_orders = cur.fetchall()

        if ongoing_orders:
            st.write("请为以下行程填写服务反馈:")
            for order in ongoing_orders:
                # 使用订单ID作为键的一部分
                feedback_key = f"feedback_{order[0]}"
                feedback = st.text_area("服务反馈：", key=feedback_key)
                if st.button("提交反馈"):
                    # 插入服务评价
                    cur.execute("INSERT INTO service_reports (order_id, driver_id, report_details) VALUES (%s, %s, %s)",
                                (order[0], order[2], feedback))
                    # 更新 trips 表的 status 列为“已完成”
                    cur.execute("UPDATE trips SET status = '已完成' WHERE order_id = %s", (order[0],))
                    # 更新 orders 表的 status 列为“已完成”
                    cur.execute("UPDATE orders SET status = '已完成' WHERE order_id = %s", (order[0],))
                    conn.commit()
                    st.success("已成功提交反馈！")
        else:
            st.write("你没有待反馈的订单")

    conn = connect_to_db()
    # 获取username
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()

    # 检查是否获取到了username
    if result:
        username = result[0]
    else:
        username = None

    # 主程序
    page = st.sidebar.selectbox("专车司机", ["申请入会", "订单管理", "服务反馈"])

    if user_id:  # 检查username是否存在
        if page == "申请入会":
            apply_for_membership(conn, username)
        elif page == "订单管理":
            order_management(conn, username)
        elif page == "服务反馈":
            service_feedback(conn, username)
        '''
        elif page == "退出登录":
            from chengji_special_car_script import session_init
            session_init()
            st.experimental_rerun()  # 强制刷新
            cur.close()
            conn.close()
        '''

    else:
        st.warning("无法识别user_id")

    conn.close()
