from pages.base_page import BasePage
from common.config_loader import CFG


class GoodsDetailPage(BasePage):
    BTN_ADD_CART = "text=加入购物车"

    def open_goods(self, goods_id: int):
        self.open(f"{CFG['env']['web_base_url']}/#/product/{goods_id}")

    def add_to_cart(self):
        # 等待 POST /api/v1/shop-cart 加购接口成功落库后再跳转购物车
        with self.page.expect_response(
            lambda r: "/api/v1/shop-cart" in r.url
            and r.request.method == "POST"
            and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_ADD_CART)


class CartPage(BasePage):
    URL = f"{CFG['env']['web_base_url']}/#/cart"
    BTN_SETTLE = "button:has-text('结算')"

    def proceed_to_checkout(self):
        # 等待购物车列表数据加载渲染完成后，再点击结算
        with self.page.expect_response(
            lambda r: "/api/v1/shop-cart" in r.url
            and r.request.method == "GET"
            and r.status == 200,
            timeout=8000,
        ):
            self.open(self.URL)

        # 点击结算后等待确认订单页的结算清单与默认地址加载完成
        with self.page.expect_response(
            lambda r: "/api/v1/shop-cart/settle" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_SETTLE)


class OrderConfirmPage(BasePage):
    BTN_CREATE_ORDER = "button:has-text('生成订单')"
    BTN_ALIPAY = "button:has-text('支付宝支付')"

    def submit_and_pay_order(self):
        # 等待创建订单接口成功返回并弹出支付弹窗
        with self.page.expect_response(
            lambda r: "/api/v1/saveOrder" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_CREATE_ORDER)

        # 等待模拟支付接口完成
        with self.page.expect_response(
            lambda r: "/api/v1/paySuccess" in r.url and r.status == 200,
            timeout=8000,
        ):
            self.click(self.BTN_ALIPAY)