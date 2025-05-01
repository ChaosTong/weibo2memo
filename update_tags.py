import pymysql
import json 

source_config = {
    "host": "",
    "port": 3306,
    "user": "root",
    "password": "hukpon-9pappA-qyhqow",
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
    SELECT id, topics
    FROM weibo WHERE topics != ""
""")
rows = source_cursor.fetchall()
count = 0
total_count = len(rows)
print(f"rows: {total_count}")
# 处理数据并插入到 memo_relation 表
for row in rows:
    weibo_id, tags = row
    tags = tags.split(",")
    
    target_cursor.execute("""
        SELECT id, payload FROM memo WHERE uid = %s
    """, (weibo_id,))
    memo_row = target_cursor.fetchone()
    memo_id = memo_row[0] if memo_row else None
    payload = memo_row[1] if memo_row else None

    if memo_id is None:
        continue

    try:
        # 解析 payload 并更新 tags
        payload_data = json.loads(payload) if payload else {}
        payload_data["tags"] = tags  # 更新 tags 字段
        updated_payload = json.dumps(payload_data, ensure_ascii=False)

        # 更新 memo 表中的 payload
        target_cursor.execute("""
            UPDATE memo SET payload = %s WHERE id = %s
        """, (updated_payload, memo_id))

        count += 1
        print(f"更新数据{count}/{total_count}: {weibo_id}, {updated_payload}")
    except (json.JSONDecodeError, pymysql.MySQLError) as e:
        count += 1
        pass
        # print(f"更新失败{count}/{total_count}，跳过此记录。错误信息: {e}")


# 提交更改并关闭连接
source_cursor.close()
source_conn.close()

target_conn.commit()
target_cursor.close()
target_conn.close()