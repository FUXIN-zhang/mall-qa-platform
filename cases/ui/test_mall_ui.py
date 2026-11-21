import re
import allure
from playwright.sync_api import expect
from common.config_loader import CFG
from pages.login_page import LoginPage
from pages.trade_pages import GoodsDetailPage, CartPage, OrderConfirmPage


@allure.feature("Web UI 端到端自动化模块")
class TestMallWebUI:

    @allure.story("用户前台登录流程")
    def test_ui_login_success(self, page):
        login_page = LoginPage(page)
        login_page.login_via_ui(
            phone=CFG["account"]["login_name"],
            password=CFG["account"]["password"],
        )

        # 断言登录成功后 URL 跳转回商城首页（兼容 /#/ 或 /#/home），且 localStorage 已保存 token
        expect(page).to_have_url(re.compile(r".*/#/(home)?$"), timeout=8000)
        token = page.evaluate("window.localStorage.getItem('token');")
        assert token is not None and len(token) > 10, "前端登录成功但未在 localStorage 生成 token"

    @allure.story("商品加购至下单支付全链路")
    def test_ui_checkout_and_pay_order(
        self, page, api_client, db_client, test_user_id, ensure_default_address, ui_clean_guard
    ):
        origin_stock = ui_clean_guard
        goods_id = 10700

        login_page = LoginPage(page)
        login_page.inject_login_token(api_client.token)

        detail_page = GoodsDetailPage(page)
        detail_page.open_goods(goods_id)
        detail_page.add_to_cart()

        cart_page = CartPage(page)
        cart_page.proceed_to_checkout()

        order_page = OrderConfirmPage(page)
        order_page.submit_and_pay_order()

        # 断言前端自动跳转到我的订单列表页（Hash 路由）
        expect(page).to_have_url(f"{CFG['env']['web_base_url']}/#/order", timeout=8000)

        # 数据库双端校验
        order_row = db_client.query_one(
            "SELECT order_status FROM tb_newbee_mall_order WHERE user_id = %s ORDER BY order_id DESC LIMIT 1",
            (test_user_id,),
        )
        assert order_row is not None, "前端支付完成但数据库未查到订单记录"
        assert order_row["order_status"] == 1, f"期望订单状态为 1（已支付），实际为 {order_row['order_status']}"

        goods_row = db_client.query_one(
            "SELECT stock_num FROM tb_newbee_mall_goods_info WHERE goods_id = %s",
            (goods_id,),
        )
        assert goods_row["stock_num"] == origin_stock - 1, "UI 下单支付后商品库存未正确扣减"