import hashlib
import sys
from pathlib import Path
from locust import HttpUser, between, task

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.config_loader import CFG


class MallUser(HttpUser):
    wait_time = between(0.5, 1.5)
    host = f"http://{CFG['mysql']['host']}:28019"

    def on_start(self):
        raw_pwd = CFG["account"]["password"]
        pwd_md5 = hashlib.md5(raw_pwd.encode("utf-8")).hexdigest()

        res = self.client.post(
            "/api/v1/user/login",
            json={
                "loginName": CFG["account"]["login_name"],
                "passwordMd5": pwd_md5,
            },
            name="00_用户登录",
        ).json()

        token = res.get("data", "")
        self.client.headers.update({"token": token})

    @task(5)
    def view_index_infos(self):
        with self.client.get("/api/v1/index-infos", name="01_首页推荐查询", catch_response=True) as resp:
            if resp.status_code != 200 or resp.json().get("resultCode") != 200:
                resp.failure(f"首页接口异常: {resp.text[:100]}")

    @task(3)
    def view_goods_detail(self):
        with self.client.get("/api/v1/goods/detail/10700", name="02_商品详情查询", catch_response=True) as resp:
            if resp.status_code != 200 or resp.json().get("resultCode") != 200:
                resp.failure(f"详情接口异常: {resp.text[:100]}")

    @task(2)
    def query_my_orders(self):
        with self.client.get("/api/v1/order?pageNumber=1", name="03_历史订单分页查询", catch_response=True) as resp:
            if resp.status_code != 200 or resp.json().get("resultCode") != 200:
                resp.failure(f"订单查询异常: {resp.text[:100]}")