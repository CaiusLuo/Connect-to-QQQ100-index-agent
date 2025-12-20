# 封装 yfinance 获取数据的逻辑
from crewai.tools import tool
import yfinance as yf


@tool("nasdaq_data_tool")
def get_nasdaq_data() -> str:
    """获取纳斯达克100指数(QQQ)的最新价格和今日涨跌幅"""
    ticker = yf.Ticker("QQQ")
    data = ticker.history(period="1d")
    latest_price = data["Close"].iloc[-1]
    change = data["Close"].iloc[-1] - data["Open"].iloc[0]
    pct_change = (change / data["Open"].iloc[0]) * 100
    return (
        f"最新价: {latest_price:.2f}, 涨跌额: {change:.2f}, 涨跌幅: {pct_change:.2f}%"
    )
