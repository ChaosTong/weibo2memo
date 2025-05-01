import pymysql

source_config = {
    "host": "",
    "port": 3306,
    "user": "root",
    "password": "",
    "charset": "utf8mb4",
    "database": "weibo"
}

target_config = {
    "host": "",
    "port": 3306,
    "user": "root",
    "password": "",
    "charset": "utf8mb4",
    "database": "memos_prod"
}

source_conn = pymysql.connect(**source_config)
source_cursor = source_conn.cursor()

target_conn = pymysql.connect(**target_config)
target_cursor = target_conn.cursor()

# 查询源数据库中的 weibo 表数据
source_cursor.execute("""
    SELECT DISTINCT
    user_id,
    screen_name
FROM
    weibo;
""")
rows = source_cursor.fetchall()

print(f"rows: {len(rows)}")
count = 0
# 处理数据并插入到 memo_relation 表
for row in rows:
    creator_id, screen_name = row

    # 检查并处理 creator_id
    if not creator_id or creator_id == '':
        creator_id = 1  # 设置默认值为 1
    else:
        creator_id = int(creator_id) % (2**31)  # 取余以限制在 int32 范围内
    
    try:
        count += 1
        target_cursor.execute("""
            INSERT INTO user (id, username, nickname, avatar_url, description, password_hash, role, row_status, created_ts, updated_ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            creator_id,  # id
            screen_name,  # nick_name -> username
            screen_name,  # nick_name -> nickname
            "", # avatar_url
            "",  # bio -> description
            "$2a$10$ShUdEdojUEt2Olrh4M0/MutSAw4K/u3wl/SM/5LZJ5zioVfazu1lq",
            "USER",
            "NORMAL",
        ))
        # print(f"插入数据{count}: {creator_id}, {screen_name}")
    except pymysql.MySQLError as e:
        count += 1
        print(f"插入失败{count}，跳过此记录。错误信息: {e}")

# 提交更改并关闭连接
source_cursor.close()
source_conn.close()

target_conn.commit()
target_cursor.close()
target_conn.close()