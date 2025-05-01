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
    SELECT id, retweet_id
    FROM weibo WHERE retweet_id != ""
""")
rows = source_cursor.fetchall()
print(f"rows: {len(rows)}")
count = 0
# 处理数据并插入到 memo_relation 表
for row in rows:
    weibo_id, retweet_id = row
    
    target_cursor.execute("""
        SELECT id FROM memo WHERE uid = %s
    """, (weibo_id,))
    memo_id = target_cursor.fetchone()
    memo_id = memo_id[0] if memo_id else None
    if memo_id is None:
        continue
    
    target_cursor.execute("""
        SELECT id FROM memo WHERE uid = %s
    """, (retweet_id,))
    related_memo_id = target_cursor.fetchone()
    related_memo_id = related_memo_id[0] if related_memo_id else None
    if related_memo_id is None:
        continue
    
    # print(f"插入数据: {weibo_id}, {retweet_id}")
    # print(f"插入数据: {memo_id}, {related_memo_id}")
    # 插入到 memo_relation 表
    try:
        count += 1
        target_cursor.execute("""
            INSERT INTO memo_relation (memo_id, related_memo_id, type)
            VALUES (%s, %s, %s)
        """, (memo_id, related_memo_id, "REFERENCE"))
        print(f"插入数据{count}: {weibo_id}, {retweet_id}")
    except pymysql.MySQLError as e:
        count += 1
        pass
        # print(f"插入失败{count}，跳过此记录。错误信息: {e}")

# 提交更改并关闭连接
source_cursor.close()
source_conn.close()

target_conn.commit()
target_cursor.close()
target_conn.close()
