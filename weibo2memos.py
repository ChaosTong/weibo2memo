# 迁移 weibo 数据库到 memos 数据库
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
    SELECT id, user_id, text, created_at
    FROM weibo
""")
rows = source_cursor.fetchall()

for row in rows:
    weibo_id, creator_id, content, created_at = row

    updated_at = created_at
    # 检查并处理 creator_id
    if not creator_id or creator_id == '':
        creator_id = 1  # 设置默认值为 1
    else:
        creator_id = int(creator_id) % (2**31)  # 取余以限制在 int32 范围内

    html_content = f"""```__html
{content}
```"""
    
    # 插入到 memo 表
    try:
        target_cursor.execute("""
            INSERT INTO memo (uid, creator_id, created_ts, updated_ts, content, visibility, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (weibo_id, creator_id, created_at, updated_at, html_content, "PUBLIC", "{}"))
        print(f"插入成功{weibo_id}")
    except pymysql.MySQLError as e:
        pass
        # print(f"插入失败，跳过此记录。错误信息: {e}")

# 提交更改并关闭连接
source_cursor.close()
source_conn.close()

target_conn.commit()
target_cursor.close()
target_conn.close()
