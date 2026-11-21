import base64
import allure
import pytest
from playwright.sync_api import sync_playwright
from common.api_client import APIClient
from common.db_client import DBClient
from common.config_loader import CFG


@pytest.fixture
def api_client():
    """每次 UI 用例独立获取最新有效 Token，避免被前序 UI 登录用例互踢作废"""
    return APIClient()


@pytest.fixture(scope="session")
def db_client():
    db = DBClient()
    yield db
    db.close()


@pytest.fixture(scope="session")
def test_user_id(db_client):
    row = db_client.query_one(
        "SELECT user_id FROM tb_newbee_mall_user WHERE login_name = %s AND is_deleted = 0",
        (CFG["account"]["login_name"],),
    )
    return row["user_id"]


@pytest.fixture
def ensure_default_address(api_client):
    """确保测试账号拥有默认收货地址，防止 UI 结算页无地址卡住"""
    res = api_client.get("/address/default")
    if res.get("resultCode") == 200 and res.get("data"):
        return res["data"]["addressId"]

    api_client.post(
        "/address",
        json_data={
            "userName": "UI自动化测试员",
            "userPhone": CFG["account"]["login_name"],
            "defaultFlag": 1,
            "provinceName": "广东省",
            "cityName": "深圳市",
            "regionName": "南山区",
            "detailAddress": "科技园南区测试大厦101室",
        },
    )


@pytest.fixture
def ui_clean_guard(db_client, test_user_id):
    """UI 测试前后环境隔离：清理购物车与测试订单，并自动还原商品库存"""
    goods_id = 10700
    row = db_client.query_one(
        "SELECT stock_num FROM tb_newbee_mall_goods_info WHERE goods_id = %s",
        (goods_id,),
    )
    origin_stock = row["stock_num"]

    db_client.execute(
        "DELETE FROM tb_newbee_mall_shopping_cart_item WHERE user_id = %s",
        (test_user_id,),
    )

    yield origin_stock

    db_client.execute(
        "UPDATE tb_newbee_mall_goods_info SET stock_num = %s WHERE goods_id = %s",
        (origin_stock, goods_id),
    )
    db_client.execute(
        "DELETE FROM tb_newbee_mall_order_item WHERE order_id IN "
        "(SELECT order_id FROM tb_newbee_mall_order WHERE user_id = %s)",
        (test_user_id,),
    )
    db_client.execute(
        "DELETE FROM tb_newbee_mall_order WHERE user_id = %s",
        (test_user_id,),
    )


@pytest.fixture
def page(request):
    """管理浏览器实例生命周期，默认开启 1280x800 视口"""
    headless = not request.config.getoption("--headed", default=False)
    slow_mo = request.config.getoption("--slowmo", default=0)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page_obj = context.new_page()
        yield page_obj
        context.close()
        browser.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例执行失败时自动截取浏览器屏幕，并挂载到 pytest-html 与 Allure 报告"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        page_obj = item.funcargs.get("page")
        if page_obj:
            png_bytes = page_obj.screenshot(full_page=True)
            allure.attach(
                png_bytes,
                name="失败现场截图",
                attachment_type=allure.attachment_type.PNG,
            )
            pytest_html = item.config.pluginmanager.getplugin("html")
            if pytest_html:
                b64_img = base64.b64encode(png_bytes).decode("utf-8")
                extra = getattr(rep, "extras", [])
                extra.append(pytest_html.extras.png(b64_img, "失败现场截图"))
                rep.extras = extra