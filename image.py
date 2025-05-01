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


def find_images_by_weibo_id(root_path, weibo_id):
    """在当前路径的所有文件夹中查找包含 weibo_id 的图片文件，并去除 rootPath，同时根据文件名去重"""
    matching_files = {}
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if str(weibo_id) in filename and not filename.lower().endswith('.csv'):
                # 如果文件名已存在，则跳过，确保去重
                if filename not in matching_files:
                    # 转换为相对路径，确保支持中文路径
                    relative_path = os.path.relpath(os.path.join(dirpath, filename), root_path)
                    matching_files[filename] = relative_path

    # 按文件名中的数字部分排序
    sorted_files = sorted(matching_files.values(), key=lambda x: int(x.split('_')[-1].split('.')[0]))
    return sorted_files

# 处理数据并插入到 memo_relation 表
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

    # 分割 pics 并提取文件名
    pic_urls = pics.split(',')
    pic_filenames = [url.split('/')[-1] for url in pic_urls]  # 提取文件名部分

    matching_files = find_images_by_weibo_id(rootPath, weibo_id)

    # if matching_files:
    #     print(f"找到以下包含 weibo_id {weibo_id} 的图片文件：")
    #     for file in matching_files:
    #         print(file)
    # else:
    #     print(f"未找到包含 weibo_id {weibo_id} 的图片文件。")

    # 检查 matching_files 和 pic_filenames 的数量是否一致
    if len(matching_files) != len(pic_filenames):
        print(f"警告: weibo_id {weibo_id} 的图片数量不一致！")
        print(f"匹配到的文件数量: {len(matching_files)}, pics 中的文件数量: {len(pic_filenames)}")
        # continue  # 跳过该条记录

    # 插入到 resource 表
    for matching_file in matching_files:
        # 提取文件名
        filename = os.path.basename(matching_file)

        # 根据文件名获取 MIME 类型
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type if mime_type else 'application/octet-stream'  # 默认值

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
            f"assets/{matching_file}"  # 使用 matching_files 的路径作为 reference
        )
        # print(f"Inserted resource: {filename}, mime_type: {mime_type}, memo_id: {memo_id}")

        # 执行 SQL 语句
        try:
            target_cursor.execute(sql, params)
            # print(f"Inserted resource: {filename}, mime_type: {mime_type}, memo_id: {memo_id}")
        except sqlite3.Error as e:
            pass
            # print(f"插入失败，跳过此记录。错误信息: {e}")



# 提交更改并关闭连接
target_conn.commit()
source_conn.close()
target_conn.close()