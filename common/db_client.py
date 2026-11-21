import pymysql
from common.config_loader import CFG


class DBClient:
    def __init__(self):
        self.conn = pymysql.connect(**CFG["mysql"], autocommit=True)

    def query_one(self, sql: str, params: tuple | None = None) -> dict | None:
        """查询单条记录，返回字典格式"""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def execute(self, sql: str, params: tuple | None = None) -> int:
        """执行增删改 SQL（用于测试前清理脏数据）"""
        with self.conn.cursor() as cursor:
            return cursor.execute(sql, params)

    def close(self):
        self.conn.close()