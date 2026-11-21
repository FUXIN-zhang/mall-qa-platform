from pages.base_page import BasePage
from common.config_loader import CFG


class GoodsDetailPage(BasePage):
    BTN_ADD_CART = "text=加入购物车"

    def open_goods(self, goods_id: int):
        # 必须等待商品详情接口返回 200，确保页面拿到 goodsId 后再执行加购点击
        with self.page.expect_response(
            lambda r: f"/api/v1/goods/detail/{goods_id}" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.open(f"{CFG['env']['web_base_url']}/#/product/{goods_id}")

    def add_to_cart(self):
        # 同时校验 HTTP 状态码与业务 resultCode == 200，防止参数异常静默跳过
        with self.page.expect_response(
            lambda r: "/api/v1/shop-cart" in r.url
            and r.request.method == "POST"
            and r.status == 200,
            timeout=8000,
        ) as resp_info:
            self.click(self.BTN_ADD_CART)

        body = resp_info.value.json()
        assert body.get("resultCode") == 200, f"UI 加购接口业务失败: {body}"


class CartPage(BasePage):
    URL = f"{CFG['env']['web_base_url']}/#/cart"
    BTN_SETTLE = ".van-submit-bar__button, button:has-text('结算')"

    def proceed_to_checkout(self):
        with self.page.expect_response(
            lambda r: "/api/v1/shop-cart" in r.url
            and r.request.method == "GET"
            and r.status == 200,
            timeout=8000,
        ):
            self.open(self.URL)

        with self.page.expect_response(
            lambda r: "/api/v1/shop-cart/settle" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_SETTLE)


class OrderConfirmPage(BasePage):
    BTN_CREATE_ORDER = "button:has-text('生成订单')"
    BTN_ALIPAY = "button:has-text('支付宝支付')"

    def submit_and_pay_order(self):
        with self.page.expect_response(
            lambda r: "/api/v1/saveOrder" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_CREATE_ORDER)

        with self.page.expect_response(
            lambda r: "/api/v1/paySuccess" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_ALIPAY)