from pages.base_page import BasePage
from common.config_loader import CFG


class LoginPage(BasePage):
    URL = f"{CFG['env']['web_base_url']}/#/login"

    INPUT_PHONE = "input[placeholder*='用户名']"
    INPUT_PASSWORD = "input[placeholder*='密码']"
    INPUT_CAPTCHA = "input[placeholder*='验证码']"
    CANVAS_CAPTCHA = "canvas"
    BTN_LOGIN = "button:has-text('登录')"

    def login_via_ui(self, phone: str, password: str):
        """方式一：完整模拟真人在界面输入账号、密码、识别验证码并点击登录"""
        self.open(self.URL)
        self.fill(self.INPUT_PHONE, phone)
        self.fill(self.INPUT_PASSWORD, password)

        verify_code = self.get_attribute(self.CANVAS_CAPTCHA, "data-code")
        assert verify_code, "未检测到验证码 data-code 属性，请确认前端已完成可测性改造"
        self.fill(self.INPUT_CAPTCHA, verify_code)
        self.click(self.BTN_LOGIN)

    def inject_login_token(self, token: str):
        """方式二：接口辅助 UI 鉴权，直接将 Token 注入浏览器 localStorage"""
        self.open(f"{CFG['env']['web_base_url']}/#/home")
        self.page.evaluate(f"window.localStorage.setItem('token', '{token}');")
        self.page.reload(wait_until="domcontentloaded")