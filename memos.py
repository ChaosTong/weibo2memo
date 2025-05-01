import sqlite3
import json
from datetime import datetime

rootPath = '/Users/mini4chaos/Developer/weibo-crawler/'

# 连接到第一个数据库（源数据库）
source_conn = sqlite3.connect(rootPath + 'weibo/weibodata.db')  # 替换为源数据库文件路径
source_cursor = source_conn.cursor()

# 连接到第二个数据库（目标数据库）
target_conn = sqlite3.connect(rootPath + 'memos/memos_prod.db')  # 替换为目标数据库文件路径
target_cursor = target_conn.cursor()

# 查询源数据库中的 weibo 表数据
source_cursor.execute("""
    SELECT id, user_id, text, created_at, bid
    FROM weibo
""")
rows = source_cursor.fetchall()

# 将数据插入到目标数据库的 memo 表
for row in rows:
    weibo_id, creator_id, content, created_at, bid = row

    # 转换 created_at 为时间戳
    created_ts = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').timestamp()) if created_at else int(datetime.now().timestamp())
    updated_ts = created_ts

    # 检查并处理 creator_id
    if not creator_id or creator_id == '':
        creator_id = 1  # 设置默认值为 0 或其他适合的值
    else:
        creator_id = int(creator_id) % (2**31)  # 取余以限制在 int32 范围内

    # 构造 payload 字段
    payload = json.dumps({
        "weibo_id": weibo_id
    })
    html_content = f"""```__html
{content}
```"""
    # 插入到 memo 表
    try:
        target_cursor.execute("""
            INSERT INTO memo (uid, creator_id, created_ts, updated_ts, content, payload, visibility)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (bid, creator_id, created_ts, updated_ts, html_content, payload, "PUBLIC"))
    except sqlite3.Error as e:
        print(f"插入失败，跳过此记录。错误信息: {e}")

# 提交更改并关闭连接
target_conn.commit()
source_conn.close()
target_conn.close()