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
    SELECT id, user_id, text, created_at, bid, retweet_id
    FROM weibo WHERE retweet_id IS NOT NULL
""")
rows = source_cursor.fetchall()

# 处理数据并插入到 memo_relation 表
for row in rows:
    weibo_id, creator_id, content, created_at, bid, retweet_id = row

    # 检查并处理 creator_id
    if not creator_id or creator_id == '':
        creator_id = 1  # 设置默认值为 1
    else:
        creator_id = int(creator_id) % (2**31)  # 取余以限制在 int32 范围内
    
    source_cursor.execute("""
        SELECT bid FROM weibo WHERE id = ?
    """, (retweet_id,))
    re_bid = source_cursor.fetchone()
    re_bid = re_bid[0] if re_bid else None
    if re_bid is None:
        continue
    print(f"re_bid: {re_bid}, bid: {bid}")
    target_cursor.execute("""
        SELECT id FROM memo WHERE uid = ?
    """, (bid,))
    memo_id = target_cursor.fetchone()
    memo_id = memo_id[0] if memo_id else None
    if memo_id is None:
        continue
    
    target_cursor.execute("""
        SELECT id FROM memo WHERE uid = ?
    """, (re_bid,))
    related_memo_id = target_cursor.fetchone()
    related_memo_id = related_memo_id[0] if related_memo_id else None
    if related_memo_id is None:
        continue
    
    print(f"插入数据: {memo_id}, {related_memo_id}")
    # 插入到 memo_relation 表
    try:
        target_cursor.execute("""
            INSERT INTO memo_relation (memo_id, related_memo_id, type)
            VALUES (?, ?, ?)
        """, (memo_id, related_memo_id, "REFERENCE"))
    except sqlite3.IntegrityError as e:
        print(f"插入失败，跳过此记录。错误信息: {e}")

# 提交更改并关闭连接
target_conn.commit()
source_conn.close()
target_conn.close()