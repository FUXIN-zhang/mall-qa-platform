import allure
import pytest
import yaml
from common.config_loader import ROOT_DIR


def load_cart_cases():
    with open(ROOT_DIR / "data" / "cart_cases.yaml", mode="r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@allure.feature("购物车核心业务模块")
class TestShoppingCart:

    @allure.story("添加商品至购物车")
    @pytest.mark.parametrize(
        "case",
        load_cart_cases(),
        ids=lambda c: f"{c['case_id']}_{c['case_name']}",
    )
    def test_add_goods_to_cart(self, api_client, db_client, test_user_id, case):
        allure.dynamic.title(f"{case['case_id']} - {case['case_name']}")

        # 1. 调用业务接口
        with allure.step("调用添加购物车接口 POST /shop-cart"):
            res = api_client.post(
                path="/shop-cart",
                json_data={
                    "goodsId": case["goods_id"],
                    "goodsCount": case["goods_count"],
                },
            )

        # 2. 第一重断言：校验接口返回的 JSON 状态码与提示语
        with allure.step("断言接口返回状态码与提示语"):
            assert res["resultCode"] == case["expect_code"], f"状态码不符: {res}"
            assert case["expect_msg"] in res["message"], f"提示信息不符: {res}"

        # 3. 第二重断言：直连云端 MySQL 校验数据库真实落库状态
        with allure.step("直连 MySQL 校验购物车表数据一致性"):
            db_row = db_client.query_one(
                "SELECT goods_id, goods_count FROM tb_newbee_mall_shopping_cart_item "
                "WHERE user_id = %s AND goods_id = %s AND is_deleted = 0",
                (test_user_id, case["goods_id"]),
            )

            if case["expect_in_db"]:
                assert db_row is not None, "接口返回成功，但数据库未查询到加购记录！"
                assert db_row["goods_count"] == case["goods_count"], (
                    f"落库数量不一致，期望 {case['goods_count']}，实际 {db_row['goods_count']}"
                )
            else:
                assert db_row is None, f"接口已拦截异常请求，但数据库竟产生了脏数据: {db_row}"