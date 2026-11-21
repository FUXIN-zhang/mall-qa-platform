import hashlib
import requests
from common.config_loader import CFG


class APIClient:
    def __init__(self):
        self.base_url = CFG["env"]["api_base_url"]
        self.session = requests.Session()
        self.token = self._login()
        self.session.headers.update({"token": self.token})

    def _login(self) -> str:
        raw_pwd = CFG["account"]["password"]
        pwd_md5 = hashlib.md5(raw_pwd.encode("utf-8")).hexdigest()

        resp = self.session.post(
            url=f"{self.base_url}/user/login",
            json={
                "loginName": CFG["account"]["login_name"],
                "passwordMd5": pwd_md5,
            },
            timeout=5,
        ).json()

        assert resp.get("resultCode") == 200, f"初始化登录失败，请检查账号或网络: {resp}"
        return resp["data"]

    def post(self, path: str, json_data: dict = None) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", json=json_data, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str, params: dict = None) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()