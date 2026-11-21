import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 确保可以直接导入根目录下的 common 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.config_loader import CFG
from common.db_client import DBClient

TOTAL_ROWS = 200_000
BATCH_SIZE = 5_000


def seed_orders():
    db = DBClient()
    start_time = time.time()

    # 1. 查询主力测试账号的真实 user_id
    user_row = db.query_one(
        "SELECT user_id FROM tb_newbee_mall_user WHERE login_name = %s AND is_deleted = 0",
        (CFG["account"]["login_name"],),
    )
    assert user_row is not None, "未找到测试账号，请检查数据库"
    target_user_id = user_row["user_id"]

    # 先清理可能残留的旧压测数据，防止重复造数主键/单号冲突
    db.execute("DELETE FROM tb_newbee_mall_order WHERE order_no LIKE 'PERF%'")

    insert_sql = """
        INSERT INTO tb_newbee_mall_order
        (order_no, user_id, total_price, pay_status, pay_type, pay_time,
         order_status, extra_info, is_deleted, create_time, update_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    base_time = datetime(2026, 1, 1, 0, 0, 0)
    batch_data = []
    inserted = 0

    print(f">>> 开始向 MySQL 批量写入 {TOTAL_ROWS} 条历史订单数据...")

    with db.conn.cursor() as cursor:
        for i in range(1, TOTAL_ROWS + 1):
            # 前 2000 条分配给主力测试账号（模拟重度买家），其余分散给虚拟用户
            uid = target_user_id if i <= 2000 else random.randint(10000, 30000)
            order_no = f"PERF{i:012d}"
            price = random.choice([99, 199, 599, 1299, 3999, 6999])
            created_at = (base_time + timedelta(seconds=i * 3)).strftime("%Y-%m-%d %H:%M:%S")

            batch_data.append(
                (order_no, uid, price, 1, 1, created_at, 4, "", 0, created_at, created_at)
            )

            if len(batch_data) >= BATCH_SIZE:
                cursor.executemany(insert_sql, batch_data)
                inserted += len(batch_data)
                batch_data.clear()
                print(f"    已写入: {inserted} / {TOTAL_ROWS} 条 ({inserted * 100 // TOTAL_ROWS}%)")

    cost = round(time.time() - start_time, 2)
    count_row = db.query_one("SELECT COUNT(*) AS cnt FROM tb_newbee_mall_order")
    db.close()
    print(f">>> 造数完成！总耗时: {cost} 秒，当前订单表总行数: {count_row['cnt']}")


if __name__ == "__main__":
    seed_orders()