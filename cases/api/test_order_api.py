import allure
import pytest
import yaml
from common.config_loader import ROOT_DIR


def load_order_cases():
    with open(ROOT_DIR / "data" / "order_cases.yaml", mode="r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@allure.feature("核心交易订单模块")
class TestOrderFlow:

    @allure.story("购物车结算创建订单全链路")
    @pytest.mark.parametrize(
        "case",
        load_order_cases(),
        ids=lambda c: f"{c['case_id']}_{c['case_name']}",
    )
    def test_create_order_and_deduct_stock(
        self, api_client, db_client, test_user_id, default_address_id, stock_guard, case
    ):
        allure.dynamic.title(f"{case['case_id']} - {case['case_name']}")
        origin_stock = stock_guard
        goods_id = case["goods_id"]
        buy_count = case["buy_count"]

        with allure.step("前置步骤1：调用加购接口添加商品"):
            add_res = api_client.post(
                "/shop-cart",
                json_data={"goodsId": goods_id, "goodsCount": buy_count},
            )
            assert add_res["resultCode"] == 200, f"前置加购失败: {add_res}"

        with allure.step("前置步骤2：查询购物车列表提取动态 cartItemId"):
            cart_res = api_client.get("/shop-cart")
            assert cart_res["resultCode"] == 200
            target_items = [
                item for item in cart_res["data"] if item["goodsId"] == goods_id
            ]
            assert len(target_items) == 1, "购物车中未找到刚添加的商品"
            cart_item_id = target_items[0]["cartItemId"]
            selling_price = target_items[0]["sellingPrice"]

        address_id = default_address_id if case["use_valid_address"] else 999999999

        with allure.step("核心步骤：调用创建订单接口 POST /saveOrder"):
            order_res = api_client.post(
                "/saveOrder",
                json_data={
                    "addressId": address_id,
                    "cartItemIds": [cart_item_id],
                },
            )

        with allure.step("断言接口返回状态码"):
            assert order_res["resultCode"] == case["expect_code"], f"接口返回异常: {order_res}"

        with allure.step("直连 MySQL 校验订单主表、明细表、购物车状态及商品库存"):
            goods_row = db_client.query_one(
                "SELECT stock_num FROM tb_newbee_mall_goods_info WHERE goods_id = %s",
                (goods_id,),
            )
            current_stock = goods_row["stock_num"]

            if case["expect_order_created"]:
                order_no = order_res["data"]
                assert order_no, "接口返回成功但未生成订单号 orderNo"

                order_row = db_client.query_one(
                    "SELECT order_id, order_no, total_price, order_status "
                    "FROM tb_newbee_mall_order WHERE order_no = %s AND user_id = %s",
                    (order_no, test_user_id),
                )
                assert order_row is not None, f"订单表未查到订单号 {order_no}"
                assert order_row["order_status"] == 0, "新建订单状态应为 0（待支付）"
                assert order_row["total_price"] == selling_price * buy_count, (
                    f"订单总价计算错误，期望 {selling_price * buy_count}，实际 {order_row['total_price']}"
                )

                item_row = db_client.query_one(
                    "SELECT goods_id, goods_count FROM tb_newbee_mall_order_item WHERE order_id = %s",
                    (order_row["order_id"],),
                )
                assert item_row is not None and item_row["goods_count"] == buy_count

                expected_stock = origin_stock - buy_count
                assert current_stock == expected_stock, (
                    f"库存扣减异常！下单前 {origin_stock}，购买 {buy_count}，期望剩余 {expected_stock}，实际 {current_stock}"
                )

                cart_row = db_client.query_one(
                    "SELECT is_deleted FROM tb_newbee_mall_shopping_cart_item WHERE cart_item_id = %s",
                    (cart_item_id,),
                )
                assert cart_row["is_deleted"] == 1, "下单成功后购物车项未清除"
            else:
                assert current_stock == origin_stock, (
                    f"下单失败但库存发生了误扣减！原库存 {origin_stock}，现库存 {current_stock}"
                )
                order_row = db_client.query_one(
                    "SELECT order_id FROM tb_newbee_mall_order WHERE user_id = %s",
                    (test_user_id,),
                )
                assert order_row is None, "下单被拦截但数据库产生了脏订单记录"