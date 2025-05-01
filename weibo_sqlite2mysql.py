# 迁移 SQLite weibo 数据库到 MySQL 数据库
import sqlite3
import pymysql

rootPath = '/Users/mini4chaos/Developer/weibo-crawler/'

mysql_config = {
    "host": "",
    "port": 3306,
    "user": "root",
    "password": "",
    "charset": "utf8mb4",
    "database": "weibo"
}

# 连接到第一个数据库（源数据库）
source_conn = sqlite3.connect(rootPath + 'weibo/weibodata.db')  # 替换为源数据库文件路径
source_cursor = source_conn.cursor()

mysql_conn = pymysql.connect(**mysql_config)
mysql_cursor = mysql_conn.cursor()

# 查询源数据库中的 weibo 表数据
source_cursor.execute("""
    SELECT id, bid, user_id, screen_name, text, article_url, topics, at_users, pics, video_url, location, created_at, source, attitudes_count, comments_count, reposts_count, retweet_id
    FROM weibo
""")
rows = source_cursor.fetchall()

for row in rows:
    id, bid, user_id, screen_name, text, article_url, topics, at_users, pics, video_url, location, created_at, source, attitudes_count, comments_count, reposts_count, retweet_id = row

    # 插入到 weibo 表
    try:
        mysql_cursor.execute("""
        INSERT INTO weibo (id, bid, user_id, screen_name, text, article_url, topics, at_users, pics, video_url, location, created_at, source, attitudes_count, comments_count, reposts_count, retweet_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (id, bid, user_id, screen_name, text, article_url, topics, at_users, pics, video_url, location, created_at, source, attitudes_count, comments_count, reposts_count, retweet_id))
    except pymysql.MySQLError as e:
        print(f"插入失败，跳过此记录。错误信息: {e}")

# 提交更改并关闭连接
source_conn.close()
mysql_conn.commit()
mysql_cursor.close()
mysql_conn.close()
