import pymysql
import json
import os
import mimetypes
from datetime import datetime

rootPath = '/Users/mini4chaos/Developer/weibo-crawler/'

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
    SELECT id, user_id, text, created_at, bid, retweet_id, pics
    FROM weibo WHERE pics IS NOT NULL AND pics != '' limit 10
""")
rows = source_cursor.fetchall()

# 遍历根目录及其子目录
for dirpath, dirnames, filenames in os.walk(rootPath):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for filename in filenames:
            if filename.lower().endswith(('.jpg', '.png', '.gif', 'mov', 'mp4', 'flv', 'mp3')):
                file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(os.path.join(dirpath, filename), rootPath)
                file_name = os.path.basename(file_path)
                if file_name.count('_') > 0:
                    weiboid = file_name.split('_')[1].split('.')[0]
                    file_size = os.path.getsize(file_path)  # 获取文件大小（以字节为单位）
                    # print(file_path, file_name, weiboid, file_size)

                    # 根据文件名获取 MIME 类型
                    mime_type, _ = mimetypes.guess_type(file_name)
                    mime_type = mime_type if mime_type else 'application/octet-stream'  # 默认值

                    source_cursor.execute("""
                        SELECT id, user_id, text, created_at, retweet_id, pics
                        FROM weibo WHERE id = %s
                    """, (weiboid,))
                    rows = source_cursor.fetchall()

                    for row in rows:
                        weibo_id, creator_id, content, created_at, retweet_id, pics = row
                        
                        # 检查并处理 creator_id
                        if not creator_id or creator_id == '':
                            creator_id = 1  # 设置默认值为 1
                        else:
                            creator_id = int(creator_id) % (2**31)  # 取余以限制在 int32 范围内

                        target_cursor.execute("""
                            SELECT id FROM memo WHERE uid = %s
                        """, (weibo_id,))
                        memo_id = target_cursor.fetchone()
                        memo_id = memo_id[0] if memo_id else None
                        if memo_id is None:
                            continue

                        # 构造 SQL 语句和参数
                        sql = """
                            INSERT INTO resource (uid, creator_id, created_ts, updated_ts, filename, type, memo_id, storage_type, reference, size, payload)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        params = (
                            os.path.splitext(filename)[0],  # uid os.path.splitext(filename)[0]
                            creator_id,  # creator_id
                            created_at,
                            created_at,
                            filename,  # filename
                            mime_type,  # type (MIME 类型)
                            memo_id,  # memo_id
                            'LOCAL',  # storage_type
                            f"assets/{relative_path}",  # 使用 matching_files 的路径作为 reference
                            file_size, # 文件大小
                            "{}"
                        )
                        # print(f"SQL: {sql}")
                        # print(f"Params: {params}")

                        # 执行 SQL 语句
                        try:
                            target_cursor.execute(sql, params)
                            print(file_path, file_name, weiboid)
                            print(f"Inserted resource: {filename}, mime_type: {mime_type}, memo_id: {memo_id}")
                        except pymysql.MySQLError as e:
                            pass
                            # print(f"插入失败，跳过此记录。错误信息: {e}")
# 提交更改并关闭连接
source_cursor.close()
source_conn.close()

target_conn.commit()
target_cursor.close()
target_conn.close()