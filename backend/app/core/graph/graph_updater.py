"""
图谱更新器

提供知识图谱的增量更新功能。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from app.core.database import get_neo4j_client


class GraphUpdater:
    """图谱更新器"""

    def __init__(self):
        """初始化图谱更新器"""
        self._neo4j = None
        self._update_log = []

    @property
    def neo4j(self):
        """获取 Neo4j 客户端"""
        if self._neo4j is None:
            self._neo4j = get_neo4j_client()
        return self._neo4j

    def update_company(self, stock_code: str, data: Dict[str, Any]) -> bool:
        """
        更新公司信息

        Args:
            stock_code: 股票代码
            data: 更新数据

        Returns:
            是否更新成功
        """
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            SET c += $properties
            RETURN c
        """
        try:
            self.neo4j.execute_write(
                query,
                {"stockCode": stock_code, "properties": data}
            )
            self._log_update("Company", stock_code, "update")
            return True
        except Exception as e:
            logger.error(f"Failed to update company {stock_code}: {e}")
            return False

    def update_industry(self, code: str, data: Dict[str, Any]) -> bool:
        """
        更新行业信息

        Args:
            code: 行业代码
            data: 更新数据

        Returns:
            是否更新成功
        """
        query = """
            MATCH (i:Industry {code: $code})
            SET i += $properties
            RETURN i
        """
        try:
            self.neo4j.execute_write(
                query,
                {"code": code, "properties": data}
            )
            self._log_update("Industry", code, "update")
            return True
        except Exception as e:
            logger.error(f"Failed to update industry {code}: {e}")
            return False

    def update_financial_report(
        self,
        stock_code: str,
        report_date: str,
        report_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        更新财务报告

        Args:
            stock_code: 股票代码
            report_date: 报告日期
            report_type: 报告类型
            data: 更新数据

        Returns:
            是否更新成功
        """
        query = """
            MATCH (f:FinancialReport {
                stockCode: $stockCode,
                reportDate: $reportDate,
                reportType: $reportType
            })
            SET f += $properties
            RETURN f
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "stockCode": stock_code,
                    "reportDate": report_date,
                    "reportType": report_type,
                    "properties": data,
                }
            )
            self._log_update("FinancialReport", f"{stock_code}_{report_date}", "update")
            return True
        except Exception as e:
            logger.error(f"Failed to update financial report: {e}")
            return False

    def update_event(self, event_id: str, data: Dict[str, Any]) -> bool:
        """
        更新事件信息

        Args:
            event_id: 事件ID
            data: 更新数据

        Returns:
            是否更新成功
        """
        query = """
            MATCH (e:MarketEvent {eventId: $eventId})
            SET e += $properties
            RETURN e
        """
        try:
            self.neo4j.execute_write(
                query,
                {"eventId": event_id, "properties": data}
            )
            self._log_update("MarketEvent", event_id, "update")
            return True
        except Exception as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            return False

    def update_investor(self, investor_id: str, data: Dict[str, Any]) -> bool:
        """
        更新投资者信息

        Args:
            investor_id: 投资者ID
            data: 更新数据

        Returns:
            是否更新成功
        """
        query = """
            MATCH (inv:Investor {investorId: $investorId})
            SET inv += $properties
            RETURN inv
        """
        try:
            self.neo4j.execute_write(
                query,
                {"investorId": investor_id, "properties": data}
            )
            self._log_update("Investor", investor_id, "update")
            return True
        except Exception as e:
            logger.error(f"Failed to update investor {investor_id}: {e}")
            return False

    def update_market_cap(self, stock_code: str, market_cap: float) -> bool:
        """
        更新市值

        Args:
            stock_code: 股票代码
            market_cap: 市值

        Returns:
            是否更新成功
        """
        return self.update_company(stock_code, {"marketCap": market_cap})

    def update_stock_price(
        self,
        stock_code: str,
        price_data: Dict[str, Any],
    ) -> bool:
        """
        更新股价信息

        Args:
            stock_code: 股票代码
            price_data: 价格数据

        Returns:
            是否更新成功
        """
        data = {
            "currentPrice": price_data.get("close"),
            "preClose": price_data.get("preClose"),
            "change": price_data.get("change"),
            "changePct": price_data.get("changePct"),
            "volume": price_data.get("volume"),
            "amount": price_data.get("amount"),
            "lastUpdated": datetime.now().isoformat(),
        }
        return self.update_company(stock_code, data)

    def update_holding(
        self,
        investor_id: str,
        stock_code: str,
        holding_data: Dict[str, Any],
    ) -> bool:
        """
        更新持仓信息

        Args:
            investor_id: 投资者ID
            stock_code: 股票代码
            holding_data: 持仓数据

        Returns:
            是否更新成功
        """
        query = """
            MATCH (inv:Investor {investorId: $investorId})-[h:HOLDS]->(c:Company {stockCode: $stockCode})
            SET h += $properties
            RETURN inv, h, c
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "investorId": investor_id,
                    "stockCode": stock_code,
                    "properties": holding_data,
                }
            )
            self._log_update("Holding", f"{investor_id}_{stock_code}", "update")
            return True
        except Exception as e:
            logger.error(f"Failed to update holding: {e}")
            return False

    def add_impact_relationship(
        self,
        event_id: str,
        target_code: str,
        target_type: str,
        impact_data: Dict[str, Any],
    ) -> bool:
        """
        添加事件影响关系

        Args:
            event_id: 事件ID
            target_code: 目标代码
            target_type: 目标类型
            impact_data: 影响数据

        Returns:
            是否添加成功
        """
        query = f"""
            MATCH (e:MarketEvent {{eventId: $eventId}})
            MATCH (t:{target_type} {{stockCode: $targetCode}})
            MERGE (e)-[:IMPACTS]->(t)
            SET e += $properties
        """
        try:
            self.neo4j.execute_write(
                query,
                {
                    "eventId": event_id,
                    "targetCode": target_code,
                    "properties": impact_data,
                }
            )
            self._log_update("Impact", f"{event_id}_{target_code}", "create")
            return True
        except Exception as e:
            logger.error(f"Failed to add impact relationship: {e}")
            return False

    def remove_impact_relationship(
        self,
        event_id: str,
        target_code: str,
        target_type: str,
    ) -> bool:
        """
        移除事件影响关系

        Args:
            event_id: 事件ID
            target_code: 目标代码
            target_type: 目标类型

        Returns:
            是否移除成功
        """
        query = f"""
            MATCH (e:MarketEvent {{eventId: $eventId}})-[r:IMPACTS]->(t:{target_type} {{stockCode: $targetCode}})
            DELETE r
        """
        try:
            self.neo4j.execute_write(
                query,
                {"eventId": event_id, "targetCode": target_code}
            )
            self._log_update("Impact", f"{event_id}_{target_code}", "delete")
            return True
        except Exception as e:
            logger.error(f"Failed to remove impact relationship: {e}")
            return False

    def batch_update_companies(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新公司

        Args:
            updates: 更新数据列表（每项包含 stockCode 和其他属性）

        Returns:
            更新成功的数量
        """
        count = 0
        for update in updates:
            stock_code = update.pop("stockCode", None)
            if stock_code and self.update_company(stock_code, update):
                count += 1
        return count

    def batch_update_market_caps(self, caps: Dict[str, float]) -> int:
        """
        批量更新市值

        Args:
            caps: 市值字典（stock_code -> market_cap）

        Returns:
            更新成功的数量
        """
        count = 0
        for stock_code, market_cap in caps.items():
            if self.update_market_cap(stock_code, market_cap):
                count += 1
        return count

    def _log_update(self, entity_type: str, entity_id: str, action: str):
        """记录更新日志"""
        self._update_log.append({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
        })

    def get_update_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取更新日志

        Args:
            limit: 返回数量

        Returns:
            更新日志
        """
        return self._update_log[-limit:]

    def clear_update_log(self):
        """清空更新日志"""
        self._update_log.clear()
