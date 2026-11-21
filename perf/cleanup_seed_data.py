import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.db_client import DBClient


def cleanup():
    db = DBClient()
    deleted = db.execute("DELETE FROM tb_newbee_mall_order WHERE order_no LIKE 'PERF%'")
    db.close()
    print(f">>> 已清理 {deleted} 条压测造数订单，数据库已恢复初始轻量状态。")


if __name__ == "__main__":
    cleanup()