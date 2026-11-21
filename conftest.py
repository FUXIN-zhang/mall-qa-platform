def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="以有头模式（显示真实浏览器窗口）运行 Playwright UI 测试",
    )
    parser.addoption(
        "--slowmo",
        action="store",
        default=0,
        type=int,
        help="减慢 Playwright 操作速度（单位：毫秒），便于肉眼观察调试",
    )