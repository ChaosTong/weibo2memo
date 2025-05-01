import sqlite3
import json
import os
import mimetypes
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
    SELECT id, user_id, text, created_at, bid, retweet_id, pics
    FROM weibo WHERE pics IS NOT NULL AND pics != ''
""")
rows = source_cursor.fetchall()

# 遍历根目录及其子目录
for dirpath, dirnames, filenames in os.walk(rootPath):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for filename in filenames:
            # 检查文件扩展名是否不是 .csv
            if filename.lower().endswith(('.jpg', '.png', '.gif', 'mov')):
                file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(os.path.join(dirpath, filename), rootPath)
                file_name = os.path.basename(file_path)
                print(file_path, file_name)
                try:
                    weiboid = file_name.split('_')[1]
                    # print(file_path, file_name, weiboid)

                    # 根据文件名获取 MIME 类型
                    mime_type, _ = mimetypes.guess_type(file_name)
                    mime_type = mime_type if mime_type else 'application/octet-stream'  # 默认值

                    source_cursor.execute("""
                        SELECT id, user_id, text, created_at, bid, retweet_id, pics
                        FROM weibo WHERE id = ?
                    """, (weiboid,))
                    rows = source_cursor.fetchall()

                    for row in rows:
                        weibo_id, creator_id, content, created_at, bid, retweet_id, pics = row
                        
                        # 检查并处理 creator_id
                        if not creator_id or creator_id == '':
                            creator_id = 1  # 设置默认值为 1
                        else:
                            creator_id = int(creator_id) % (2**31)  # 取余以限制在 int32 范围内

                        target_cursor.execute("""
                            SELECT id FROM memo WHERE uid = ?
                        """, (bid,))
                        memo_id = target_cursor.fetchone()
                        memo_id = memo_id[0] if memo_id else None
                        if memo_id is None:
                            continue

                        # 构造 SQL 语句和参数
                        sql = """
                            INSERT INTO resource (uid, creator_id, created_ts, updated_ts, filename, type, memo_id, storage_type, reference)
                            VALUES (?, ?, strftime('%s', 'now'), strftime('%s', 'now'), ?, ?, ?, ?, ?)
                        """
                        
                        params = (
                            os.path.splitext(filename)[0],  # uid os.path.splitext(filename)[0]
                            creator_id,  # creator_id
                            filename,  # filename
                            mime_type,  # type (MIME 类型)
                            memo_id,  # memo_id
                            'LOCAL',  # storage_type
                            f"assets/{relative_path}"  # 使用 matching_files 的路径作为 reference
                        )
                        # print(f"SQL: {sql}")
                        # print(f"Params: {params}")

                        # 执行 SQL 语句
                        try:
                            target_cursor.execute(sql, params)
                            print(file_path, file_name, weiboid)
                            print(f"Inserted resource: {filename}, mime_type: {mime_type}, memo_id: {memo_id}")
                        except sqlite3.Error as e:
                            pass
                        #     print(f"插入失败，跳过此记录。错误信息: {e}")
                except PermissionError as e:
                    print(f"无法访问文件夹: {dirpath}, 错误: {e}")
# 提交更改并关闭连接
target_conn.commit()
source_conn.close()
target_conn.close()