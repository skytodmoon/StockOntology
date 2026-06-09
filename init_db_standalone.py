#!/usr/bin/env python3
"""
独立的Neo4j数据库初始化脚本

该脚本不依赖项目的其他模块，直接连接到Neo4j并初始化数据。
"""

import sys
import os
from datetime import datetime, timedelta
import random

try:
    from neo4j import GraphDatabase
except ImportError:
    print("❌ 需要安装neo4j库: pip install neo4j")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ 需要安装python-dotenv库: pip install python-dotenv")
    sys.exit(1)

# 加载环境变量
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def get_neo4j_client():
    """获取Neo4j客户端"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def init_ontology_schema(client):
    """初始化本体模式约束"""
    constraints = [
        "CREATE CONSTRAINT company_code IF NOT EXISTS FOR (c:Company) REQUIRE c.stockCode IS UNIQUE",
        "CREATE CONSTRAINT industry_code IF NOT EXISTS FOR (i:Industry) REQUIRE i.code IS UNIQUE",
        "CREATE CONSTRAINT investor_id IF NOT EXISTS FOR (inv:Investor) REQUIRE inv.investorId IS UNIQUE",
        "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
    ]
    
    with client.session() as session:
        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"✓ 创建约束: {constraint[:50]}...")
            except Exception as e:
                print(f"⚠ 约束已存在或创建失败: {e}")


def init_industry_data(client):
    """初始化行业数据"""
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
    MERGE (i:Industry {code: $code})
    SET i.name = $name,
        i.description = $description,
        i.level = $level
    """
    
    with client.session() as session:
        for ind in industries:
            session.run(cypher, code=ind["code"], name=ind["name"], 
                       description=ind["description"], level=ind["level"])
    
    print(f"✓ 已创建 {len(industries)} 个行业节点")


def init_company_data(client):
    """初始化公司数据"""
    companies = [
        {"stockCode": "600519", "stockName": "贵州茅台", "market": "SH", "industry": "IND001", 
         "description": "中国白酒龙头企业，主要生产茅台酒", "employees": 30000},
        {"stockCode": "000858", "stockName": "五粮液", "market": "SZ", "industry": "IND001",
         "description": "浓香型白酒代表企业", "employees": 25000},
        {"stockCode": "000568", "stockName": "泸州老窖", "market": "SZ", "industry": "IND001",
         "description": "浓香型白酒发源地", "employees": 20000},
        {"stockCode": "600887", "stockName": "伊利股份", "market": "SH", "industry": "IND003",
         "description": "中国乳制品行业领导者", "employees": 60000},
        {"stockCode": "002557", "stockName": "洽洽食品", "market": "SZ", "industry": "IND002",
         "description": "坚果零食龙头企业", "employees": 15000},
        {"stockCode": "603288", "stockName": "海天味业", "market": "SH", "industry": "IND002",
         "description": "调味品行业龙头企业", "employees": 12000},
        {"stockCode": "600276", "stockName": "恒瑞医药", "market": "SH", "industry": "IND004",
         "description": "创新药研发领先企业", "employees": 40000},
        {"stockCode": "000538", "stockName": "云南白药", "market": "SZ", "industry": "IND004",
         "description": "中药行业知名企业", "employees": 25000},
        {"stockCode": "000002", "stockName": "万科A", "market": "SZ", "industry": "IND008",
         "description": "房地产龙头企业", "employees": 130000},
        {"stockCode": "601318", "stockName": "中国平安", "market": "SH", "industry": "IND007",
         "description": "综合性金融集团", "employees": 360000},
        {"stockCode": "600036", "stockName": "招商银行", "market": "SH", "industry": "IND007",
         "description": "股份制商业银行", "employees": 90000},
        {"stockCode": "300750", "stockName": "宁德时代", "market": "SZ", "industry": "IND010",
         "description": "动力电池行业领先企业", "employees": 80000},
        {"stockCode": "002594", "stockName": "比亚迪", "market": "SZ", "industry": "IND009",
         "description": "新能源汽车领导者", "employees": 650000},
    ]
    
    cypher = """
    MERGE (c:Company {stockCode: $stockCode})
    SET c.stockName = $stockName,
        c.market = $market,
        c.description = $description,
        c.employees = $employees,
        c.createdAt = datetime()
    WITH c
    MATCH (i:Industry {industry_code: $industry})
    MERGE (c)-[:BELONGS_TO]->(i)
    """
    
    with client.session() as session:
        for company in companies:
            session.run(cypher, **company)
    
    print(f"✓ 已创建 {len(companies)} 个公司节点")


def init_stock_data(client):
    """初始化股票数据"""
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
    
    companies = [
        {"stockCode": "600519", "stockName": "贵州茅台", "base_price": 1800},
        {"stockCode": "000858", "stockName": "五粮液", "base_price": 150},
        {"stockCode": "000568", "stockName": "泸州老窖", "base_price": 200},
        {"stockCode": "600887", "stockName": "伊利股份", "base_price": 30},
        {"stockCode": "603288", "stockName": "海天味业", "base_price": 60},
        {"stockCode": "600276", "stockName": "恒瑞医药", "base_price": 45},
        {"stockCode": "300750", "stockName": "宁德时代", "base_price": 200},
        {"stockCode": "002594", "stockName": "比亚迪", "base_price": 250},
    ]
    
    cypher = """
    MATCH (c:Company {stockCode: $stockCode})
    MERGE (s:Stock {stockCode: $stockCode, tradeDate: date($date)})
    SET s.open = $open,
        s.high = $high,
        s.low = $low,
        s.close = $close,
        s.volume = $volume,
        s.amount = $amount,
        s.changePct = $change_pct
    MERGE (c)-[:HAS_TRADE]->(s)
    """
    
    total = 0
    with client.session() as session:
        for company in companies:
            for date in dates:
                base = company["base_price"]
                volatility = random.uniform(-0.03, 0.03)
                close = base * (1 + volatility)
                open_price = base * (1 + random.uniform(-0.01, 0.01))
                high = max(open_price, close) * (1 + random.uniform(0, 0.02))
                low = min(open_price, close) * (1 - random.uniform(0, 0.02))
                volume = random.randint(1000000, 50000000)
                amount = volume * close
                change_pct = round(volatility * 100, 2)
                
                session.run(cypher, stockCode=company["stockCode"], date=date,
                           open=round(open_price, 2), high=round(high, 2),
                           low=round(low, 2), close=round(close, 2),
                           volume=volume, amount=round(amount, 2),
                           change_pct=change_pct)
                total += 1
    
    print(f"✓ 已创建 {total} 条股票交易数据")


def init_investor_data(client):
    """初始化投资者数据"""
    investors = [
        {"investorId": "INV001", "name": "张伟", "investorType": "Fund", "region": "北京"},
        {"investorId": "INV002", "name": "李娜", "investorType": "Insurance", "region": "上海"},
        {"investorId": "INV003", "name": "王强", "investorType": "Retail", "region": "深圳"},
        {"investorId": "INV004", "name": "赵敏", "investorType": "QFII", "region": "香港"},
        {"investorId": "INV005", "name": "刘洋", "investorType": "Private", "region": "北京"},
    ]
    
    holdings = [
        {"investor": "INV001", "stock": "600519", "shares": 5000000, "ratio": 0.4},
        {"investor": "INV001", "stock": "000858", "shares": 3000000, "ratio": 0.2},
        {"investor": "INV002", "stock": "600519", "shares": 4000000, "ratio": 0.3},
        {"investor": "INV003", "stock": "000858", "shares": 2000000, "ratio": 0.15},
        {"investor": "INV004", "stock": "600887", "shares": 8000000, "ratio": 1.2},
        {"investor": "INV005", "stock": "300750", "shares": 2000000, "ratio": 0.5},
    ]
    
    investor_cypher = """
    MERGE (inv:Investor {investorId: $investorId})
    SET inv.name = $name,
        inv.investorType = $investorType,
        inv.region = $region
    """
    
    with client.session() as session:
        for inv in investors:
            session.run(investor_cypher, **inv)
    
    holding_cypher = """
    MATCH (inv:Investor {investor_id: $investor})
    MATCH (c:Company {stockCode: $stock})
    MERGE (inv)-[r:HOLDS]->(c)
    SET r.shares = $shares,
        r.holding_ratio = $ratio
    """
    
    with client.session() as session:
        for holding in holdings:
            session.run(holding_cypher, investor=holding["investor"],
                       stock=holding["stock"], shares=holding["shares"],
                       ratio=holding["ratio"])
    
    print(f"✓ 已创建 {len(investors)} 个投资者节点")
    print(f"✓ 已创建 {len(holdings)} 个持仓关系")


def init_event_data(client):
    """初始化事件数据"""
    events = [
        {
            "eventId": "EVT001",
            "title": "茅台集团营收突破千亿",
            "eventType": "CompanyEvent",
            "eventDate": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            "impactLevel": "High",
            "content": "茅台集团发布年度业绩预告，营收首次突破千亿大关",
            "tags": ["业绩", "白酒", "贵州茅台"]
        },
        {
            "eventId": "EVT002",
            "title": "五粮液启动数字化转型",
            "eventType": "CompanyEvent",
            "eventDate": (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            "impactLevel": "Medium",
            "content": "五粮液宣布启动全面数字化转型战略",
            "tags": ["战略", "数字化", "五粮液"]
        },
        {
            "eventId": "EVT003",
            "title": "医药集采政策调整",
            "eventType": "PolicyEvent",
            "eventDate": (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            "impactLevel": "High",
            "content": "国家医保局调整药品集中采购政策",
            "tags": ["政策", "医药", "集采"]
        },
        {
            "eventId": "EVT004",
            "title": "新能源汽车补贴退坡",
            "eventType": "PolicyEvent",
            "eventDate": (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
            "impactLevel": "High",
            "content": "新能源汽车购置补贴政策逐步退坡",
            "tags": ["政策", "新能源", "汽车"]
        },
    ]
    
    event_cypher = """
    MERGE (e:MarketEvent {eventId: $eventId})
    SET e.title = $title,
        e.eventType = $eventType,
        e.eventDate = $eventDate,
        e.impactLevel = $impactLevel,
        e.content = $content,
        e.tags = $tags
    """
    
    with client.session() as session:
        for event in events:
            session.run(event_cypher, **event)
    
    print(f"✓ 已创建 {len(events)} 个事件节点")


def init_relationships(client):
    """初始化公司间关系"""
    relationships = [
        {"from": "600519", "to": "000858", "type": "COMPETES_WITH"},
        {"from": "600519", "to": "000568", "type": "COMPETES_WITH"},
        {"from": "000858", "to": "000568", "type": "COMPETES_WITH"},
        {"from": "600519", "to": "002557", "type": "SUPPLIES_TO"},
        {"from": "300750", "to": "002594", "type": "SUPPLIES_TO"},
        {"from": "601318", "to": "600519", "type": "HOLDS_SHARES"},
    ]
    
    rel_cypher = """
    MATCH (a:Company {stockCode: $from_code})
    MATCH (b:Company {stockCode: $to_code})
    MERGE (a)-[r:RELATES_TO]->(b)
    SET r.relationship_type = $type
    """
    
    with client.session() as session:
        for rel in relationships:
            session.run(rel_cypher, from_code=rel["from"], to_code=rel["to"], type=rel["type"])
    
    print(f"✓ 已创建 {len(relationships)} 个公司间关系")


def print_statistics(client):
    """打印数据库统计信息"""
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
    
    with client.session() as session:
        for name, query in queries:
            result = session.run(query)
            count = result.single()["count"]
            print(f"  {name:12s}: {count:>6} 条")


def main():
    """主函数"""
    print("=" * 60)
    print("StockOntology 数据库初始化")
    print("=" * 60)
    print()
    
    client = None
    try:
        print(f"🔌 连接到 Neo4j: {NEO4J_URI}")
        client = get_neo4j_client()
        
        # 测试连接
        with client.session() as session:
            session.run("RETURN 1")
        print("✓ Neo4j连接成功")
        print()
        
        print("🔧 开始初始化...")
        print()
        
        print("1️⃣ 初始化本体约束...")
        init_ontology_schema(client)
        print()
        
        print("2️⃣ 初始化行业数据...")
        init_industry_data(client)
        print()
        
        print("3️⃣ 初始化公司数据...")
        init_company_data(client)
        print()
        
        print("4️⃣ 初始化股票数据...")
        init_stock_data(client)
        print()
        
        print("5️⃣ 初始化投资者数据...")
        init_investor_data(client)
        print()
        
        print("6️⃣ 初始化事件数据...")
        init_event_data(client)
        print()
        
        print("7️⃣ 初始化公司间关系...")
        init_relationships(client)
        print()
        
        print_statistics(client)
        
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
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
