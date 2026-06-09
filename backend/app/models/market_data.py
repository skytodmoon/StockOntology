"""
行情数据模型

定义股票行情数据的结构。
"""

from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


class MarketDataBase(BaseModel):
    """行情数据基础模型"""
    stock_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")

    # OHLCV 数据
    open: float = Field(..., description="开盘价", ge=0)
    high: float = Field(..., description="最高价", ge=0)
    low: float = Field(..., description="最低价", ge=0)
    close: float = Field(..., description="收盘价", ge=0)
    volume: float = Field(..., description="成交量（股）", ge=0)
    amount: float = Field(..., description="成交额（元）", ge=0)

    # 涨跌幅
    change: Optional[float] = Field(None, description="涨跌额")
    change_pct: Optional[float] = Field(None, description="涨跌幅（%）")

    # 换手率
    turn_rate: Optional[float] = Field(None, description="换手率（%）", ge=0, le=100)

    # 市值
    market_cap: Optional[float] = Field(None, description="总市值（元）")
    float_market_cap: Optional[float] = Field(None, description="流通市值（元）")

    @validator("high")
    def validate_high(cls, v, values):
        """验证最高价"""
        if "low" in values and v < values["low"]:
            raise ValueError("High price must be greater than or equal to low price")
        return v

    @validator("close")
    def validate_close(cls, v, values):
        """验证收盘价"""
        if "low" in values and "high" in values:
            if v < values["low"] or v > values["high"]:
                raise ValueError("Close price must be between low and high")
        return v


class MarketDataCreate(MarketDataBase):
    """创建行情数据请求模型"""
    pass


class MarketData(MarketDataBase):
    """行情数据完整模型"""
    id: Optional[str] = Field(None, description="Neo4j 节点ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    class Config:
        """Pydantic 配置"""
        from_attributes = True


class MarketDataResponse(BaseModel):
    """行情数据响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: Optional[MarketData] = Field(None, description="行情数据")


class MarketDataListResponse(BaseModel):
    """行情数据列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("Success", description="响应消息")
    data: List[MarketData] = Field(default_factory=list, description="行情数据列表")
    total: int = Field(0, description="总数")


class TechnicalIndicator(BaseModel):
    """技术指标模型"""
    stock_code: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日期")

    # 均线
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    ma120: Optional[float] = Field(None, description="120日均线")
    ma250: Optional[float] = Field(None, description="250日均线")

    # MACD
    macd_dif: Optional[float] = Field(None, description="MACD DIF")
    macd_dea: Optional[float] = Field(None, description="MACD DEA")
    macd_hist: Optional[float] = Field(None, description="MACD 柱状")

    # RSI
    rsi_6: Optional[float] = Field(None, description="6日RSI")
    rsi_12: Optional[float] = Field(None, description="12日RSI")
    rsi_24: Optional[float] = Field(None, description="24日RSI")

    # KDJ
    kdj_k: Optional[float] = Field(None, description="KDJ K值")
    kdj_d: Optional[float] = Field(None, description="KDJ D值")
    kdj_j: Optional[float] = Field(None, description="KDJ J值")

    # BOLL
    boll_upper: Optional[float] = Field(None, description="布林带上轨")
    boll_middle: Optional[float] = Field(None, description="布林带中轨")
    boll_lower: Optional[float] = Field(None, description="布林带下轨")

    # 成交量指标
    vol_ma5: Optional[float] = Field(None, description="5日成交量均线")
    vol_ma10: Optional[float] = Field(None, description="10日成交量均线")


class KlineData(BaseModel):
    """K线数据模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    trade_dates: List[date] = Field(default_factory=list, description="交易日期列表")
    opens: List[float] = Field(default_factory=list, description="开盘价列表")
    highs: List[float] = Field(default_factory=list, description="最高价列表")
    lows: List[float] = Field(default_factory=list, description="最低价列表")
    closes: List[float] = Field(default_factory=list, description="收盘价列表")
    volumes: List[float] = Field(default_factory=list, description="成交量列表")
    amounts: List[float] = Field(default_factory=list, description="成交额列表")


class MarketOverview(BaseModel):
    """市场概览模型"""
    trade_date: date = Field(..., description="交易日期")

    # 指数
    sh_index: Optional[float] = Field(None, description="上证指数")
    sh_change_pct: Optional[float] = Field(None, description="上证涨跌幅")
    sz_index: Optional[float] = Field(None, description="深证成指")
    sz_change_pct: Optional[float] = Field(None, description="深证涨跌幅")
    cyb_index: Optional[float] = Field(None, description="创业板指")
    cyb_change_pct: Optional[float] = Field(None, description="创业板涨跌幅")

    # 市场统计
    up_count: int = Field(0, description="上涨家数")
    down_count: int = Field(0, description="下跌家数")
    flat_count: int = Field(0, description="平盘家数")
    limit_up_count: int = Field(0, description="涨停家数")
    limit_down_count: int = Field(0, description="跌停家数")

    # 成交统计
    total_volume: float = Field(0, description="总成交量")
    total_amount: float = Field(0, description="总成交额")

    # 板块统计
    top_sectors: List[Dict[str, Any]] = Field(default_factory=list, description="领涨板块")
    bottom_sectors: List[Dict[str, Any]] = Field(default_factory=list, description="领跌板块")


class StockQuote(BaseModel):
    """股票实时行情模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    current_price: float = Field(..., description="当前价格")
    change: float = Field(0, description="涨跌额")
    change_pct: float = Field(0, description="涨跌幅")
    open: float = Field(0, description="开盘价")
    high: float = Field(0, description="最高价")
    low: float = Field(0, description="最低价")
    pre_close: float = Field(0, description="昨收价")
    volume: float = Field(0, description="成交量")
    amount: float = Field(0, description="成交额")
    time: datetime = Field(default_factory=datetime.now, description="行情时间")


def market_data_to_neo4j(data: MarketData) -> Dict[str, Any]:
    """
    将行情数据模型转换为 Neo4j 节点属性

    Args:
        data: 行情数据模型

    Returns:
        Neo4j 节点属性字典
    """
    return {
        "stockCode": data.stock_code,
        "tradeDate": data.trade_date.isoformat(),
        "open": data.open,
        "high": data.high,
        "low": data.low,
        "close": data.close,
        "volume": data.volume,
        "amount": data.amount,
        "change": data.change,
        "changePct": data.change_pct,
        "turnRate": data.turn_rate,
        "marketCap": data.market_cap,
        "floatMarketCap": data.float_market_cap,
    }


def neo4j_to_market_data(properties: Dict[str, Any]) -> MarketData:
    """
    将 Neo4j 节点属性转换为行情数据模型

    Args:
        properties: Neo4j 节点属性

    Returns:
        行情数据模型
    """
    trade_date = date.today()
    if properties.get("tradeDate"):
        try:
            trade_date = date.fromisoformat(properties["tradeDate"])
        except ValueError:
            pass

    return MarketData(
        stock_code=properties.get("stockCode", ""),
        trade_date=trade_date,
        open=properties.get("open", 0),
        high=properties.get("high", 0),
        low=properties.get("low", 0),
        close=properties.get("close", 0),
        volume=properties.get("volume", 0),
        amount=properties.get("amount", 0),
        change=properties.get("change"),
        change_pct=properties.get("changePct"),
        turn_rate=properties.get("turnRate"),
        market_cap=properties.get("marketCap"),
        float_market_cap=properties.get("floatMarketCap"),
    )
