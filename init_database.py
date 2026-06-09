"""
Neo4j 数据库初始化脚本

该脚本用于初始化股票知识图谱数据，包括：
- 行业节点
- 公司节点
- 股票节点
- 投资者节点
- 事件节点
- 以及它们之间的关系
"""

import sys
import os
from datetime import datetime, timedelta
import random

# 添加backend路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_neo4j_client
from app.config import settings


def init_ontology_schema():
    """初始化本体模式约束"""
    client = get_neo4j_client()
    
    # 使用复合键约束
    constraints = [
        "CREATE CONSTRAINT company_code IF NOT EXISTS FOR (c:Company) REQUIRE c.stock_code IS UNIQUE",
        "CREATE CONSTRAINT industry_code IF NOT EXISTS FOR (i:Industry) REQUIRE i.industry_code IS UNIQUE",
        "CREATE CONSTRAINT investor_id IF NOT EXISTS FOR (inv:Investor) REQUIRE inv.investor_id IS UNIQUE",
        "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
    ]
    
    with client.get_session() as session:
        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"✓ 创建约束: {constraint[:50]}...")
            except Exception as e:
                print(f"⚠ 约束已存在或创建失败: {e}")
    
    client.close()


def init_industry_data():
    """初始化行业数据"""
    client = get_neo4j_client()
    
    industries = [
        {"code": "IND001", "name": "白酒", "description": "白酒制造行业", "level": 1},
        {"code": "IND002", "name": "食品制造", "description": "食品制造行业", "level": 1},
        {"code": "IND003", "name": "饮料制造", "description": "饮料制造行业", "level": 1},
        {"code": "IND004", "name": "医药生物", "description": "医药生物行业", "level": 1},
        {"code": "IND005", "name": "电子信息", "description": "电子信息技术行业", "level": 1},
        {"code": "IND006", "name": "软件服务", "description": "软件服务行业", "level": 1},
        {"code": "IND007", "name": "银行", "description": "银行金融行业", "level": 1},
        {"code": "IND008", "name": "房地产", "description": "房地产行业", "level": 1},
        {"code": "IND009", "name": "汽车制造", "description": "汽车制造行业", "level": 1},
        {"code": "IND010", "name": "新能源", "description": "新能源行业", "level": 1},
    ]
    
    cypher = """
    MERGE (i:Industry {industry_code: $code})
    SET i.name = $name,
        i.description = $description,
        i.level = $level,
        i.created_at = datetime()
    """
    
    with client.get_session() as session:
        for ind in industries:
            session.run(cypher, code=ind["code"], name=ind["name"], 
                       description=ind["description"], level=ind["level"])
    
    print(f"✓ 已创建 {len(industries)} 个行业节点")
    client.close()


def init_company_data():
    """初始化公司数据"""
    client = get_neo4j_client()
    
    companies = [
        # 白酒行业
        {"code": "600519", "name": "贵州茅台", "industry": "IND001", 
         "description": "中国白酒龙头企业，主要生产茅台酒", "employees": 30000},
        {"code": "000858", "name": "五粮液", "industry": "IND001",
         "description": "浓香型白酒代表企业", "employees": 25000},
        {"code": "000568", "name": "泸州老窖", "industry": "IND001",
         "description": "浓香型白酒发源地", "employees": 20000},
        
        # 食品饮料行业
        {"code": "600887", "name": "伊利股份", "industry": "IND003",
         "description": "中国乳制品行业领导者", "employees": 60000},
        {"code": "002557", "name": "洽洽食品", "industry": "IND002",
         "description": "坚果零食龙头企业", "employees": 15000},
        {"code": "603288", "name": "海天味业", "industry": "IND002",
         "description": "调味品行业龙头企业", "employees": 12000},
        
        # 医药行业
        {"code": "600276", "name": "恒瑞医药", "industry": "IND004",
         "description": "创新药研发领先企业", "employees": 40000},
        {"code": "000538", "name": "云南白药", "industry": "IND004",
         "description": "中药行业知名企业", "employees": 25000},
        
        # 科技行业
        {"code": "000002", "name": "万科A", "industry": "IND008",
         "description": "房地产龙头企业", "employees": 130000},
        {"code": "601318", "name": "中国平安", "industry": "IND007",
         "description": "综合性金融集团", "employees": 360000},
        {"code": "600036", "name": "招商银行", "industry": "IND007",
         "description": "股份制商业银行", "employees": 90000},
        
        # 新能源
        {"code": "300750", "name": "宁德时代", "industry": "IND010",
         "description": "动力电池行业领先企业", "employees": 80000},
        {"code": "002594", "name": "比亚迪", "industry": "IND009",
         "description": "新能源汽车领导者", "employees": 650000},
    ]
    
    cypher = """
    MERGE (c:Company {stock_code: $code})
    SET c.name = $name,
        c.description = $description,
        c.employees = $employees,
        c.created_at = datetime()
    WITH c
    MATCH (i:Industry {industry_code: $industry})
    MERGE (c)-[:BELONGS_TO]->(i)
    """
    
    with client.get_session() as session:
        for company in companies:
            session.run(cypher, code=company["code"], name=company["name"],
                       description=company["description"], employees=company["employees"],
                       industry=company["industry"])
    
    print(f"✓ 已创建 {len(companies)} 个公司节点")
    client.close()


def init_stock_data():
    """初始化股票数据"""
    client = get_neo4j_client()
    
    # 生成过去30天的股票数据
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    
    companies = [
        {"code": "600519", "name": "贵州茅台", "base_price": 1800},
        {"code": "000858", "name": "五粮液", "base_price": 150},
        {"code": "000568", "name": "泸州老窖", "base_price": 200},
        {"code": "600887", "name": "伊利股份", "base_price": 30},
        {"code": "603288", "name": "海天味业", "base_price": 60},
        {"code": "600276", "name": "恒瑞医药", "base_price": 45},
        {"code": "300750", "name": "宁德时代", "base_price": 200},
        {"code": "002594", "name": "比亚迪", "base_price": 250},
    ]
    
    cypher = """
    MATCH (c:Company {stock_code: $stock_code})
    MERGE (s:Stock {stock_code: $stock_code, trade_date: date($date)})
    SET s.open = $open,
        s.high = $high,
        s.low = $low,
        s.close = $close,
        s.volume = $volume,
        s.amount = $amount,
        s.change_pct = $change_pct
    MERGE (c)-[:HAS_TRADE]->(s)
    """
    
    total = 0
    with client.get_session() as session:
        for company in companies:
            for date in dates:
                # 模拟股价波动
                base = company["base_price"]
                volatility = random.uniform(-0.03, 0.03)
                close = base * (1 + volatility)
                open_price = base * (1 + random.uniform(-0.01, 0.01))
                high = max(open_price, close) * (1 + random.uniform(0, 0.02))
                low = min(open_price, close) * (1 - random.uniform(0, 0.02))
                volume = random.randint(1000000, 50000000)
                amount = volume * close
                change_pct = round(volatility * 100, 2)
                
                session.run(cypher, stock_code=company["code"], date=date,
                           open=round(open_price, 2), high=round(high, 2),
                           low=round(low, 2), close=round(close, 2),
                           volume=volume, amount=round(amount, 2),
                           change_pct=change_pct)
                total += 1
    
    print(f"✓ 已创建 {total} 条股票交易数据")
    client.close()


def init_investor_data():
    """初始化投资者数据"""
    client = get_neo4j_client()
    
    investors = [
        {"id": "INV001", "name": "张伟", "type": "机构投资者", "region": "北京"},
        {"id": "INV002", "name": "李娜", "type": "机构投资者", "region": "上海"},
        {"id": "INV003", "name": "王强", "type": "个人投资者", "region": "深圳"},
        {"id": "INV004", "name": "赵敏", "type": "QFII", "region": "香港"},
        {"id": "INV005", "name": "刘洋", "type": "机构投资者", "region": "北京"},
    ]
    
    holdings = [
        {"investor": "INV001", "stock": "600519", "shares": 5000000, "ratio": 0.4},
        {"investor": "INV001", "stock": "000858", "shares": 3000000, "ratio": 0.2},
        {"investor": "INV002", "stock": "600519", "shares": 4000000, "ratio": 0.3},
        {"investor": "INV003", "stock": "000858", "shares": 2000000, "ratio": 0.15},
        {"investor": "INV004", "stock": "600887", "shares": 8000000, "ratio": 1.2},
        {"investor": "INV005", "stock": "300750", "shares": 2000000, "ratio": 0.5},
    ]
    
    # 创建投资者节点
    investor_cypher = """
    MERGE (inv:Investor {investor_id: $id})
    SET inv.name = $name,
        inv.investor_type = $type,
        inv.region = $region,
        inv.created_at = datetime()
    """
    
    with client.get_session() as session:
        for inv in investors:
            session.run(investor_cypher, id=inv["id"], name=inv["name"],
                       type=inv["type"], region=inv["region"])
    
    # 创建持仓关系
    holding_cypher = """
    MATCH (inv:Investor {investor_id: $investor})
    MATCH (c:Company {stock_code: $stock})
    MERGE (inv)-[r:HOLDS]->(c)
    SET r.shares = $shares,
        r.holding_ratio = $ratio,
        r.updated_at = datetime()
    """
    
    with client.get_session() as session:
        for holding in holdings:
            session.run(holding_cypher, investor=holding["investor"],
                       stock=holding["stock"], shares=holding["shares"],
                       ratio=holding["ratio"])
    
    print(f"✓ 已创建 {len(investors)} 个投资者节点")
    print(f"✓ 已创建 {len(holdings)} 个持仓关系")
    client.close()


def init_event_data():
    """初始化事件数据"""
    client = get_neo4j_client()
    
    events = [
        {
            "id": "EVT001",
            "title": "茅台集团营收突破千亿",
            "type": "业绩公告",
            "date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            "impact": "正面",
            "description": "茅台集团发布年度业绩预告，营收首次突破千亿大关"
        },
        {
            "id": "EVT002",
            "title": "五粮液启动数字化转型",
            "type": "战略发布",
            "date": (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            "impact": "正面",
            "description": "五粮液宣布启动全面数字化转型战略"
        },
        {
            "id": "EVT003",
            "title": "医药集采政策调整",
            "type": "政策变动",
            "date": (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            "impact": "中性",
            "description": "国家医保局调整药品集中采购政策"
        },
        {
            "id": "EVT004",
            "title": "新能源汽车补贴退坡",
            "type": "政策变动",
            "date": (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
            "impact": "负面",
            "description": "新能源汽车购置补贴政策逐步退坡"
        },
    ]
    
    event_cypher = """
    MERGE (e:Event {event_id: $id})
    SET e.title = $title,
        e.event_type = $type,
        e.event_date = date($date),
        e.impact = $impact,
        e.description = $description,
        e.created_at = datetime()
    """
    
    affect_cypher = """
    MATCH (e:Event {event_id: $event_id})
    MATCH (c:Company {stock_code: $stock_code})
    MERGE (e)-[:AFFECTS]->(c)
    SET e.impact_level = $impact_level
    """
    
    with client.get_session() as session:
        for event in events:
            session.run(event_cypher, id=event["id"], title=event["title"],
                       type=event["type"], date=event["date"],
                       impact=event["impact"], description=event["description"])
        
        # 关联事件影响的公司
        session.run(affect_cypher, event_id="EVT001", stock_code="600519", impact_level="高")
        session.run(affect_cypher, event_id="EVT002", stock_code="000858", impact_level="中")
        session.run(affect_cypher, event_id="EVT003", stock_code="600276", impact_level="中")
        session.run(affect_cypher, event_id="EVT004", stock_code="002594", impact_level="高")
        session.run(affect_cypher, event_id="EVT004", stock_code="300750", impact_level="高")
    
    print(f"✓ 已创建 {len(events)} 个事件节点")
    client.close()


def init_relationships():
    """初始化公司间关系"""
    client = get_neo4j_client()
    
    relationships = [
        # 竞争对手关系
        {"from": "600519", "to": "000858", "type": "COMPETES_WITH"},
        {"from": "600519", "to": "000568", "type": "COMPETES_WITH"},
        {"from": "000858", "to": "000568", "type": "COMPETES_WITH"},
        
        # 上下游关系
        {"from": "600519", "to": "002557", "type": "SUPPLIES_TO"},
        {"from": "300750", "to": "002594", "type": "SUPPLIES_TO"},
        
        # 参股关系
        {"from": "601318", "to": "600519", "type": "HOLDS_SHARES"},
    ]
    
    rel_cypher = """
    MATCH (a:Company {stock_code: $from_code})
    MATCH (b:Company {stock_code: $to_code})
    MERGE (a)-[r:RELATES_TO]->(b)
    SET r.relationship_type = $type,
        r.created_at = datetime()
    """
    
    with client.get_session() as session:
        for rel in relationships:
            session.run(rel_cypher, from_code=rel["from"], to_code=rel["to"], type=rel["type"])
    
    print(f"✓ 已创建 {len(relationships)} 个公司间关系")
    client.close()


def print_statistics():
    """打印数据库统计信息"""
    client = get_neo4j_client()
    
    queries = [
        ("行业", "MATCH (i:Industry) RETURN count(i) as count"),
        ("公司", "MATCH (c:Company) RETURN count(c) as count"),
        ("股票数据", "MATCH (s:Stock) RETURN count(s) as count"),
        ("投资者", "MATCH (inv:Investor) RETURN count(inv) as count"),
        ("事件", "MATCH (e:Event) RETURN count(e) as count"),
        ("关系", "MATCH ()-[r]->() RETURN count(r) as count"),
    ]
    
    print("\n📊 数据库统计信息:")
    print("-" * 50)
    
    with client.get_session() as session:
        for name, query in queries:
            result = session.run(query)
            count = result.single()["count"]
            print(f"  {name:12s}: {count:>6} 条")
    
    client.close()


def main():
    """主函数"""
    print("=" * 60)
    print("StockOntology 数据库初始化")
    print("=" * 60)
    print()
    
    try:
        print("🔧 开始初始化...")
        print()
        
        # 1. 初始化本体约束
        print("1️⃣ 初始化本体约束...")
        init_ontology_schema()
        print()
        
        # 2. 初始化行业数据
        print("2️⃣ 初始化行业数据...")
        init_industry_data()
        print()
        
        # 3. 初始化公司数据
        print("3️⃣ 初始化公司数据...")
        init_company_data()
        print()
        
        # 4. 初始化股票数据
        print("4️⃣ 初始化股票数据...")
        init_stock_data()
        print()
        
        # 5. 初始化投资者数据
        print("5️⃣ 初始化投资者数据...")
        init_investor_data()
        print()
        
        # 6. 初始化事件数据
        print("6️⃣ 初始化事件数据...")
        init_event_data()
        print()
        
        # 7. 初始化公司间关系
        print("7️⃣ 初始化公司间关系...")
        init_relationships()
        print()
        
        # 8. 打印统计信息
        print_statistics()
        
        print()
        print("=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 初始化失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
