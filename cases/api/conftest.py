import pytest
from common.api_client import APIClient
from common.db_client import DBClient
from common.config_loader import CFG


@pytest.fixture(scope="session")
def api_client():
    """全局复用同一个已登录的 API 客户端"""
    return APIClient()


@pytest.fixture(scope="session")
def db_client():
    """全局数据库连接"""
    db = DBClient()
    yield db
    db.close()


@pytest.fixture(scope="session")
def test_user_id(db_client):
    """动态查询当前测试账号的 user_id"""
    row = db_client.query_one(
        "SELECT user_id FROM tb_newbee_mall_user WHERE login_name = %s AND is_deleted = 0",
        (CFG["account"]["login_name"],),
    )
    assert row is not None, "测试账号在数据库中不存在"
    return row["user_id"]


@pytest.fixture(autouse=True)
def clean_user_cart(db_client, test_user_id):
    """每条用例运行前自动清理该用户的购物车，保证 100% 幂等可重复运行"""
    db_client.execute(
        "DELETE FROM tb_newbee_mall_shopping_cart_item WHERE user_id = %s",
        (test_user_id,),
    )
    yield


@pytest.fixture(scope="session")
def default_address_id(api_client):
    """获取测试账号默认收货地址ID，若不存在则自动通过接口创建"""
    res = api_client.get("/address/default")
    if res.get("resultCode") == 200 and res.get("data"):
        return res["data"]["addressId"]

    create_res = api_client.post(
        "/address",
        json_data={
            "userName": "自动化测试员",
            "userPhone": CFG["account"]["login_name"],
            "defaultFlag": 1,
            "provinceName": "广东省",
            "cityName": "深圳市",
            "regionName": "南山区",
            "detailAddress": "科技园南区测试大厦101室",
        },
    )
    assert create_res.get("resultCode") == 200, f"创建默认地址失败: {create_res}"

    retry_res = api_client.get("/address/default")
    return retry_res["data"]["addressId"]


@pytest.fixture
def stock_guard(db_client, test_user_id):
    """库存与订单守卫：记录用例执行前库存，用例结束后自动还原库存并清理测试脏订单"""
    goods_id = 10700
    row = db_client.query_one(
        "SELECT stock_num FROM tb_newbee_mall_goods_info WHERE goods_id = %s",
        (goods_id,),
    )
    assert row is not None, f"商品 {goods_id} 不存在"
    origin_stock = row["stock_num"]

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