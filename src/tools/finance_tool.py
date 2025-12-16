# 封装 yfinance 获取数据的逻辑
from typing import Any, Type

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel


class NasdaqDataToolInput(BaseModel):
    """纳斯达克数据工具的输入参数 - 无需参数"""

    pass


class NasdaqDataTool(BaseTool):
    """获取纳斯达克100指数(QQQ)数据的工具"""

    name: str = "nasdaq_data_tool"
    description: str = "获取纳斯达克100指数(QQQ)的最新价格和今日涨跌幅"
    args_schema: Type[BaseModel] = NasdaqDataToolInput

    def _run(self, **kwargs: Any) -> str:
        """执行工具获取纳斯达克数据"""
        ticker = yf.Ticker("QQQ")
        data = ticker.history(period="1d")
        latest_price = data["Close"].iloc[-1]
        change = data["Close"].iloc[-1] - data["Open"].iloc[0]
        pct_change = (change / data["Open"].iloc[0]) * 100
        return f"最新价: {latest_price:.2f}, 涨跌额: {change:.2f}, 涨跌幅: {pct_change:.2f}%"


# 创建工具实例供外部使用
get_nasdaq_data = NasdaqDataTool()
