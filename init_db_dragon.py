#!/usr/bin/env python3
"""
龙头战法数据库初始化脚本

参考龙头战法思想，重点分析龙头股(半导体，芯片，AI，航天，机器人，算力，消费等)，
及其供应链，突出供应链公司中的具备技术护城河的企业。
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


def clear_database(client):
    """清空数据库"""
    print("🗑️ 清理现有数据...")
    with client.session() as session:
        # 删除所有节点和关系
        session.run("MATCH (n) DETACH DELETE n")
        # 删除所有约束
        constraints = session.run("SHOW CONSTRAINTS").data()
        for constraint in constraints:
            name = constraint.get("name")
            if name:
                session.run(f"DROP CONSTRAINT {name}")
    print("✓ 数据库已清理")


def init_constraints(client):
    """初始化约束"""
    print("\n🔧 创建约束...")
    constraints = [
        "CREATE CONSTRAINT company_stock_code IF NOT EXISTS FOR (c:Company) REQUIRE c.stockCode IS UNIQUE",
        "CREATE CONSTRAINT industry_code IF NOT EXISTS FOR (i:Industry) REQUIRE i.code IS UNIQUE",
        "CREATE CONSTRAINT investor_id IF NOT EXISTS FOR (inv:Investor) REQUIRE inv.investorId IS UNIQUE",
        "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:MarketEvent) REQUIRE e.eventId IS UNIQUE",
        "CREATE CONSTRAINT concept_code IF NOT EXISTS FOR (c:Concept) REQUIRE c.code IS UNIQUE",
    ]
    
    with client.session() as session:
        for constraint in constraints:
            try:
                session.run(constraint)
                print(f"✓ 创建约束: {constraint[:50]}...")
            except Exception as e:
                print(f"⚠ 约束已存在: {e}")


def init_industry_data(client):
    """初始化行业数据（重点关注龙头战法相关行业）"""
    print("\n🏭 初始化行业数据...")
    industries = [
        # 半导体产业链
        {"code": "IND001", "name": "半导体", "description": "半导体芯片设计、制造、封装测试", "level": 1, "isCore": True},
        {"code": "IND002", "name": "芯片设计", "description": "集成电路设计行业", "level": 2, "parent": "IND001"},
        {"code": "IND003", "name": "晶圆制造", "description": "芯片晶圆代工制造", "level": 2, "parent": "IND001"},
        {"code": "IND004", "name": "封装测试", "description": "芯片封装与测试", "level": 2, "parent": "IND001"},
        {"code": "IND005", "name": "半导体设备", "description": "半导体生产设备制造", "level": 2, "parent": "IND001"},
        {"code": "IND006", "name": "半导体材料", "description": "半导体制造原材料", "level": 2, "parent": "IND001"},
        
        # AI产业链
        {"code": "IND007", "name": "人工智能", "description": "AI算法、模型、应用", "level": 1, "isCore": True},
        {"code": "IND008", "name": "大模型", "description": "大型语言模型开发", "level": 2, "parent": "IND007"},
        {"code": "IND009", "name": "AI应用", "description": "人工智能应用服务", "level": 2, "parent": "IND007"},
        
        # 算力产业链
        {"code": "IND010", "name": "算力", "description": "数据中心、云计算、服务器", "level": 1, "isCore": True},
        {"code": "IND011", "name": "数据中心", "description": "IDC数据中心服务", "level": 2, "parent": "IND010"},
        {"code": "IND012", "name": "服务器", "description": "服务器硬件制造", "level": 2, "parent": "IND010"},
        {"code": "IND013", "name": "光模块", "description": "光通信模块", "level": 2, "parent": "IND010"},
        
        # 机器人产业链
        {"code": "IND014", "name": "机器人", "description": "工业机器人、服务机器人", "level": 1, "isCore": True},
        {"code": "IND015", "name": "工业机器人", "description": "工业自动化机器人", "level": 2, "parent": "IND014"},
        {"code": "IND016", "name": "伺服系统", "description": "机器人伺服电机与控制系统", "level": 2, "parent": "IND014"},
        {"code": "IND017", "name": "减速器", "description": "精密减速器制造", "level": 2, "parent": "IND014"},
        
        # 航天军工
        {"code": "IND018", "name": "航天军工", "description": "航空航天、国防军工", "level": 1, "isCore": True},
        {"code": "IND019", "name": "卫星制造", "description": "卫星研发与制造", "level": 2, "parent": "IND018"},
        {"code": "IND020", "name": "导弹装备", "description": "导弹武器系统", "level": 2, "parent": "IND018"},
        {"code": "IND021", "name": "军工电子", "description": "军用电子元器件", "level": 2, "parent": "IND018"},
        
        # 消费行业
        {"code": "IND022", "name": "消费", "description": "消费品、零售", "level": 1, "isCore": True},
        {"code": "IND023", "name": "白酒", "description": "白酒制造", "level": 2, "parent": "IND022"},
        {"code": "IND024", "name": "食品饮料", "description": "食品饮料制造", "level": 2, "parent": "IND022"},
        {"code": "IND025", "name": "家电", "description": "家用电器", "level": 2, "parent": "IND022"},
        
        # 新能源
        {"code": "IND026", "name": "新能源", "description": "光伏、风电、储能", "level": 1, "isCore": True},
        {"code": "IND027", "name": "光伏", "description": "太阳能光伏", "level": 2, "parent": "IND026"},
        {"code": "IND028", "name": "锂电池", "description": "动力电池与储能", "level": 2, "parent": "IND026"},
    ]
    
    cypher = """
    MERGE (i:Industry {code: $code})
    SET i.name = $name,
        i.description = $description,
        i.level = $level,
        i.isCore = $isCore
    """
    
    with client.session() as session:
        for ind in industries:
            session.run(cypher, code=ind["code"], name=ind["name"], 
                       description=ind["description"], level=ind["level"],
                       isCore=ind.get("isCore", False))
        
        # 创建行业层级关系
        for ind in industries:
            if ind.get("parent"):
                session.run("""
                    MATCH (child:Industry {code: $child_code})
                    MATCH (parent:Industry {code: $parent_code})
                    MERGE (child)-[:BELONGS_TO]->(parent)
                """, child_code=ind["code"], parent_code=ind["parent"])
    
    print(f"✓ 已创建 {len(industries)} 个行业节点")


def init_concept_data(client):
    """初始化概念板块数据"""
    print("\n📊 初始化概念板块...")
    concepts = [
        {"code": "CON001", "name": "国产替代", "description": "半导体国产替代概念", "hotLevel": 5},
        {"code": "CON002", "name": "AI算力", "description": "人工智能算力需求", "hotLevel": 5},
        {"code": "CON003", "name": "机器人", "description": "机器人产业升级", "hotLevel": 4},
        {"code": "CON004", "name": "卫星互联网", "description": "低轨卫星通信", "hotLevel": 4},
        {"code": "CON005", "name": "CPO", "description": "共封装光学技术", "hotLevel": 5},
        {"code": "CON006", "name": "液冷", "description": "数据中心液冷技术", "hotLevel": 4},
        {"code": "CON007", "name": "MR/VR", "description": "混合现实/虚拟现实", "hotLevel": 3},
        {"code": "CON008", "name": "算力租赁", "description": "GPU算力租赁服务", "hotLevel": 5},
        {"code": "CON009", "name": "汽车智能化", "description": "智能驾驶、座舱", "hotLevel": 4},
        {"code": "CON010", "name": "国企改革", "description": "国有企业改革", "hotLevel": 3},
    ]
    
    cypher = """
    MERGE (c:Concept {code: $code})
    SET c.name = $name,
        c.description = $description,
        c.hotLevel = $hotLevel
    """
    
    with client.session() as session:
        for concept in concepts:
            session.run(cypher, **concept)
    
    print(f"✓ 已创建 {len(concepts)} 个概念板块")


def init_company_data(client):
    """初始化龙头企业数据"""
    print("\n👑 初始化龙头企业数据...")
    
    # 半导体/芯片龙头
    companies = [
        # === 半导体芯片 ===
        {"stockCode": "600745", "stockName": "闻泰科技", "market": "SH", "industry": "IND002",
         "description": "全球领先的半导体IDM企业，安世半导体母公司", "employees": 32000,
         "isLeader": True, "moatLevel": 5, "moatType": "技术壁垒+规模优势",
         "marketCap": 1500, "peRatio": 45, "roe": 15},
        {"stockCode": "002049", "stockName": "紫光国微", "market": "SZ", "industry": "IND002",
         "description": "国内领先的集成电路设计企业，特种芯片龙头", "employees": 4500,
         "isLeader": True, "moatLevel": 5, "moatType": "技术壁垒+资质壁垒",
         "marketCap": 800, "peRatio": 60, "roe": 20},
        {"stockCode": "300661", "stockName": "圣邦股份", "market": "SZ", "industry": "IND002",
         "description": "模拟芯片设计龙头企业", "employees": 1200,
         "isLeader": True, "moatLevel": 4, "moatType": "技术积累",
         "marketCap": 300, "peRatio": 55, "roe": 18},
        {"stockCode": "603986", "stockName": "兆易创新", "market": "SH", "industry": "IND002",
         "description": "国内存储器芯片设计龙头", "employees": 4000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+市场份额",
         "marketCap": 600, "peRatio": 40, "roe": 12},
        {"stockCode": "002156", "stockName": "通富微电", "market": "SZ", "industry": "IND004",
         "description": "国内领先的芯片封装测试企业", "employees": 18000,
         "isLeader": True, "moatLevel": 4, "moatType": "规模优势",
         "marketCap": 250, "peRatio": 50, "roe": 8},
        {"stockCode": "600584", "stockName": "长电科技", "market": "SH", "industry": "IND004",
         "description": "全球领先的集成电路封装测试企业", "employees": 25000,
         "isLeader": True, "moatLevel": 5, "moatType": "规模+技术",
         "marketCap": 400, "peRatio": 65, "roe": 10},
        {"stockCode": "300373", "stockName": "扬杰科技", "market": "SZ", "industry": "IND006",
         "description": "功率半导体龙头企业", "employees": 8000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+渠道",
         "marketCap": 200, "peRatio": 45, "roe": 15},
        {"stockCode": "688008", "stockName": "澜起科技", "market": "SH", "industry": "IND002",
         "description": "内存接口芯片全球龙头", "employees": 1200,
         "isLeader": True, "moatLevel": 5, "moatType": "技术垄断",
         "marketCap": 500, "peRatio": 50, "roe": 18},
        
        # === AI ===
        {"stockCode": "300229", "stockName": "拓尔思", "market": "SZ", "industry": "IND009",
         "description": "国内领先的AI语义分析企业", "employees": 3500,
         "isLeader": True, "moatLevel": 4, "moatType": "技术积累+数据",
         "marketCap": 150, "peRatio": 120, "roe": 8},
        {"stockCode": "603019", "stockName": "中科曙光", "market": "SH", "industry": "IND012",
         "description": "国内领先的高性能计算企业", "employees": 8000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+渠道",
         "marketCap": 500, "peRatio": 70, "roe": 10},
        {"stockCode": "000977", "stockName": "浪潮信息", "market": "SZ", "industry": "IND012",
         "description": "全球领先的服务器制造商", "employees": 30000,
         "isLeader": True, "moatLevel": 5, "moatType": "规模+技术",
         "marketCap": 800, "peRatio": 80, "roe": 12},
        {"stockCode": "600536", "stockName": "中国软件", "market": "SH", "industry": "IND009",
         "description": "国产操作系统龙头", "employees": 8000,
         "isLeader": True, "moatLevel": 4, "moatType": "资质壁垒",
         "marketCap": 300, "peRatio": 200, "roe": 5},
        
        # === 算力 ===
        {"stockCode": "300502", "stockName": "新易盛", "market": "SZ", "industry": "IND013",
         "description": "光模块龙头企业", "employees": 4000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+客户",
         "marketCap": 400, "peRatio": 60, "roe": 20},
        {"stockCode": "002819", "stockName": "东方雨虹", "market": "SZ", "industry": "IND011",
         "description": "防水行业龙头", "employees": 15000,
         "isLeader": True, "moatLevel": 4, "moatType": "品牌+渠道",
         "marketCap": 500, "peRatio": 25, "roe": 25},
        {"stockCode": "600703", "stockName": "三安光电", "market": "SH", "industry": "IND006",
         "description": "国内LED芯片龙头，布局化合物半导体", "employees": 15000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+规模",
         "marketCap": 1000, "peRatio": 80, "roe": 8},
        {"stockCode": "300032", "stockName": "金龙机电", "market": "SZ", "industry": "IND016",
         "description": "微电机领域龙头", "employees": 5000,
         "isLeader": False, "moatLevel": 3, "moatType": "细分龙头",
         "marketCap": 50, "peRatio": None, "roe": 5},
        
        # === 机器人 ===
        {"stockCode": "300024", "stockName": "机器人", "market": "SZ", "industry": "IND015",
         "description": "国内工业机器人龙头", "employees": 6000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+品牌",
         "marketCap": 300, "peRatio": 150, "roe": 5},
        {"stockCode": "002527", "stockName": "新时达", "market": "SZ", "industry": "IND015",
         "description": "工业机器人与运动控制龙头", "employees": 3500,
         "isLeader": True, "moatLevel": 4, "moatType": "技术积累",
         "marketCap": 150, "peRatio": 100, "roe": 8},
        {"stockCode": "603789", "stockName": "星光农机", "market": "SH", "industry": "IND017",
         "description": "精密减速器制造商", "employees": 1200,
         "isLeader": False, "moatLevel": 3, "moatType": "细分领域",
         "marketCap": 50, "peRatio": None, "roe": 3},
        {"stockCode": "300124", "stockName": "汇川技术", "market": "SZ", "industry": "IND016",
         "description": "工业自动化控制龙头", "employees": 12000,
         "isLeader": True, "moatLevel": 5, "moatType": "技术+渠道",
         "marketCap": 800, "peRatio": 50, "roe": 20},
        {"stockCode": "002008", "stockName": "大族激光", "market": "SZ", "industry": "IND015",
         "description": "激光设备龙头，布局机器人业务", "employees": 15000,
         "isLeader": True, "moatLevel": 4, "moatType": "技术+品牌",
         "marketCap": 400, "peRatio": 40, "roe": 12},
        
        # === 航天军工 ===
        {"stockCode": "600118", "stockName": "中国卫星", "market": "SH", "industry": "IND019",
         "description": "卫星制造与应用龙头", "employees": 4000,
         "isLeader": True, "moatLevel": 5, "moatType": "资质壁垒+技术",
         "marketCap": 300, "peRatio": 100, "roe": 8},
        {"stockCode": "000625", "stockName": "长安汽车", "market": "SZ", "industry": "IND021",
         "description": "汽车制造龙头，军工背景", "employees": 45000,
         "isLeader": True, "moatLevel": 4, "moatType": "规模+品牌",
         "marketCap": 1500, "peRatio": 30, "roe": 15},
        {"stockCode": "600879", "stockName": "航天电子", "market": "SH", "industry": "IND021",
         "description": "航天电子设备龙头", "employees": 12000,
         "isLeader": True, "moatLevel": 5, "moatType": "资质壁垒",
         "marketCap": 250, "peRatio": 80, "roe": 6},
        {"stockCode": "002025", "stockName": "航天电器", "market": "SZ", "industry": "IND021",
         "description": "军用连接器龙头", "employees": 4000,
         "isLeader": True, "moatLevel": 5, "moatType": "资质壁垒+技术",
         "marketCap": 200, "peRatio": 70, "roe": 15},
        
        # === 消费 ===
        {"stockCode": "600519", "stockName": "贵州茅台", "market": "SH", "industry": "IND023",
         "description": "中国白酒龙头，品牌价值突出", "employees": 30000,
         "isLeader": True, "moatLevel": 5, "moatType": "品牌壁垒+稀缺性",
         "marketCap": 25000, "peRatio": 30, "roe": 30},
        {"stockCode": "000858", "stockName": "五粮液", "market": "SZ", "industry": "IND023",
         "description": "浓香型白酒龙头", "employees": 25000,
         "isLeader": True, "moatLevel": 5, "moatType": "品牌壁垒",
         "marketCap": 8000, "peRatio": 25, "roe": 25},
        {"stockCode": "600887", "stockName": "伊利股份", "market": "SH", "industry": "IND024",
         "description": "乳制品行业龙头", "employees": 60000,
         "isLeader": True, "moatLevel": 5, "moatType": "品牌+渠道",
         "marketCap": 2000, "peRatio": 20, "roe": 20},
        {"stockCode": "000333", "stockName": "美的集团", "market": "SZ", "industry": "IND025",
         "description": "家电行业龙头", "employees": 160000,
         "isLeader": True, "moatLevel": 5, "moatType": "品牌+规模",
         "marketCap": 3500, "peRatio": 15, "roe": 22},
        {"stockCode": "002594", "stockName": "比亚迪", "market": "SZ", "industry": "IND028",
         "description": "新能源汽车龙头，垂直整合", "employees": 650000,
         "isLeader": True, "moatLevel": 5, "moatType": "技术+产业链整合",
         "marketCap": 8000, "peRatio": 40, "roe": 18},
        {"stockCode": "300750", "stockName": "宁德时代", "market": "SZ", "industry": "IND028",
         "description": "全球动力电池龙头", "employees": 80000,
         "isLeader": True, "moatLevel": 5, "moatType": "技术+规模+客户",
         "marketCap": 12000, "peRatio": 35, "roe": 25},
    ]
    
    cypher = """
    MERGE (c:Company {stockCode: $stockCode})
    SET c.stockName = $stockName,
        c.market = $market,
        c.description = $description,
        c.employees = $employees,
        c.isLeader = $isLeader,
        c.moatLevel = $moatLevel,
        c.moatType = $moatType,
        c.marketCap = $marketCap,
        c.peRatio = $peRatio,
        c.roe = $roe,
        c.createdAt = datetime()
    WITH c
    MATCH (i:Industry {code: $industry})
    MERGE (c)-[:BELONGS_TO]->(i)
    """
    
    with client.session() as session:
        for company in companies:
            session.run(cypher, **company)
    
    print(f"✓ 已创建 {len(companies)} 个龙头企业节点")
    print(f"  - 其中行业龙头: {sum(1 for c in companies if c['isLeader'])} 家")
    print(f"  - 具备高护城河(≥4): {sum(1 for c in companies if c['moatLevel'] >= 4)} 家")


def init_supply_chain(client):
    """初始化供应链关系（龙头战法核心）"""
    print("\n🔗 初始化供应链关系...")
    
    # 供应链关系定义
    supply_chain = [
        # 半导体供应链
        {"supplier": "600745", "customer": "000977", "relation": "SUPPLIES", "description": "供应芯片"},
        {"supplier": "600745", "customer": "603019", "relation": "SUPPLIES", "description": "供应芯片"},
        {"supplier": "002049", "customer": "600745", "relation": "SUPPLIES", "description": "供应特种芯片"},
        {"supplier": "300661", "customer": "600745", "relation": "SUPPLIES", "description": "供应模拟芯片"},
        {"supplier": "603986", "customer": "000977", "relation": "SUPPLIES", "description": "供应存储芯片"},
        {"supplier": "600584", "customer": "600745", "relation": "SUPPLIES", "description": "封装测试"},
        {"supplier": "002156", "customer": "300661", "relation": "SUPPLIES", "description": "封装测试"},
        {"supplier": "300373", "customer": "002594", "relation": "SUPPLIES", "description": "供应功率器件"},
        {"supplier": "688008", "customer": "000977", "relation": "SUPPLIES", "description": "供应内存接口芯片"},
        {"supplier": "600703", "customer": "300502", "relation": "SUPPLIES", "description": "供应光芯片"},
        
        # AI/算力供应链
        {"supplier": "000977", "customer": "300229", "relation": "SUPPLIES", "description": "供应服务器"},
        {"supplier": "603019", "customer": "300229", "relation": "SUPPLIES", "description": "供应算力设备"},
        {"supplier": "300502", "customer": "000977", "relation": "SUPPLIES", "description": "供应光模块"},
        {"supplier": "300502", "customer": "603019", "relation": "SUPPLIES", "description": "供应光模块"},
        
        # 机器人供应链
        {"supplier": "300124", "customer": "300024", "relation": "SUPPLIES", "description": "供应伺服系统"},
        {"supplier": "300124", "customer": "002527", "relation": "SUPPLIES", "description": "供应控制器"},
        {"supplier": "603789", "customer": "300024", "relation": "SUPPLIES", "description": "供应减速器"},
        {"supplier": "002008", "customer": "300024", "relation": "SUPPLIES", "description": "供应激光设备"},
        
        # 航天军工供应链
        {"supplier": "002025", "customer": "600118", "relation": "SUPPLIES", "description": "供应连接器"},
        {"supplier": "600879", "customer": "600118", "relation": "SUPPLIES", "description": "供应电子设备"},
        
        # 新能源供应链
        {"supplier": "300750", "customer": "002594", "relation": "SUPPLIES", "description": "供应动力电池"},
        
        # 行业竞争关系
        {"supplier": "600519", "customer": "000858", "relation": "COMPETES_WITH", "description": "白酒竞争"},
        {"supplier": "000977", "customer": "603019", "relation": "COMPETES_WITH", "description": "服务器竞争"},
        {"supplier": "300024", "customer": "002527", "relation": "COMPETES_WITH", "description": "机器人竞争"},
    ]
    
    cypher = """
    MATCH (supplier:Company {stockCode: $supplier_code})
    MATCH (customer:Company {stockCode: $customer_code})
    MERGE (supplier)-[:SUPPLIES {description: $description}]->(customer)
    """
    
    cypher_compete = """
    MATCH (a:Company {stockCode: $supplier_code})
    MATCH (b:Company {stockCode: $customer_code})
    MERGE (a)-[:COMPETES_WITH {description: $description}]->(b)
    """
    
    with client.session() as session:
        for chain in supply_chain:
            if chain["relation"] == "SUPPLIES":
                session.run(cypher, supplier_code=chain["supplier"], 
                           customer_code=chain["customer"], description=chain["description"])
            else:
                session.run(cypher_compete, supplier_code=chain["supplier"], 
                           customer_code=chain["customer"], description=chain["description"])
    
    print(f"✓ 已创建 {len(supply_chain)} 条供应链关系")


def init_concept_relations(client):
    """初始化概念与公司关联"""
    print("\n🔗 初始化概念关联...")
    
    concept_relations = [
        # 国产替代概念
        {"concept": "CON001", "stockCode": "600745"},
        {"concept": "CON001", "stockCode": "002049"},
        {"concept": "CON001", "stockCode": "300661"},
        {"concept": "CON001", "stockCode": "603986"},
        {"concept": "CON001", "stockCode": "600584"},
        {"concept": "CON001", "stockCode": "002156"},
        
        # AI算力概念
        {"concept": "CON002", "stockCode": "000977"},
        {"concept": "CON002", "stockCode": "603019"},
        {"concept": "CON002", "stockCode": "300502"},
        {"concept": "CON002", "stockCode": "300229"},
        {"concept": "CON002", "stockCode": "688008"},
        
        # 机器人概念
        {"concept": "CON003", "stockCode": "300024"},
        {"concept": "CON003", "stockCode": "002527"},
        {"concept": "CON003", "stockCode": "300124"},
        {"concept": "CON003", "stockCode": "002008"},
        
        # 卫星互联网
        {"concept": "CON004", "stockCode": "600118"},
        {"concept": "CON004", "stockCode": "600879"},
        {"concept": "CON004", "stockCode": "002025"},
        
        # CPO概念
        {"concept": "CON005", "stockCode": "300502"},
        {"concept": "CON005", "stockCode": "600703"},
        
        # 算力租赁
        {"concept": "CON008", "stockCode": "603019"},
        {"concept": "CON008", "stockCode": "000977"},
        
        # 汽车智能化
        {"concept": "CON009", "stockCode": "002594"},
        {"concept": "CON009", "stockCode": "300124"},
    ]
    
    cypher = """
    MATCH (c:Company {stockCode: $stockCode})
    MATCH (co:Concept {code: $concept_code})
    MERGE (c)-[:BELONGS_TO_CONCEPT]->(co)
    """
    
    with client.session() as session:
        for rel in concept_relations:
            session.run(cypher, stockCode=rel["stockCode"], concept_code=rel["concept"])
    
    print(f"✓ 已创建 {len(concept_relations)} 条概念关联")


def init_stock_data(client):
    """初始化股票交易数据"""
    print("\n📈 初始化股票交易数据...")
    
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(60, 0, -1)]
    
    companies = [
        {"stockCode": "600745", "stockName": "闻泰科技", "base_price": 55},
        {"stockCode": "002049", "stockName": "紫光国微", "base_price": 140},
        {"stockCode": "300661", "stockName": "圣邦股份", "base_price": 120},
        {"stockCode": "603986", "stockName": "兆易创新", "base_price": 85},
        {"stockCode": "000977", "stockName": "浪潮信息", "base_price": 60},
        {"stockCode": "603019", "stockName": "中科曙光", "base_price": 45},
        {"stockCode": "300502", "stockName": "新易盛", "base_price": 80},
        {"stockCode": "300024", "stockName": "机器人", "base_price": 18},
        {"stockCode": "300124", "stockName": "汇川技术", "base_price": 65},
        {"stockCode": "600118", "stockName": "中国卫星", "base_price": 28},
        {"stockCode": "600519", "stockName": "贵州茅台", "base_price": 1800},
        {"stockCode": "000858", "stockName": "五粮液", "base_price": 150},
        {"stockCode": "002594", "stockName": "比亚迪", "base_price": 250},
        {"stockCode": "300750", "stockName": "宁德时代", "base_price": 200},
        {"stockCode": "688008", "stockName": "澜起科技", "base_price": 80},
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
                # 龙头股可能有更高的波动性
                volatility = random.uniform(-0.05, 0.05) if company["stockCode"] in ["600745", "000977", "300502"] else random.uniform(-0.03, 0.03)
                close = base * (1 + volatility)
                open_price = base * (1 + random.uniform(-0.02, 0.02))
                high = max(open_price, close) * (1 + random.uniform(0, 0.03))
                low = min(open_price, close) * (1 - random.uniform(0, 0.03))
                volume = random.randint(5000000, 100000000)
                amount = volume * close
                change_pct = round(volatility * 100, 2)
                
                session.run(cypher, stockCode=company["stockCode"], date=date,
                           open=round(open_price, 2), high=round(high, 2),
                           low=round(low, 2), close=round(close, 2),
                           volume=volume, amount=round(amount, 2),
                           change_pct=change_pct)
                total += 1
    
    print(f"✓ 已创建 {total} 条股票交易数据")


def init_events(client):
    """初始化市场事件数据"""
    print("\n📰 初始化市场事件...")
    
    events = [
        {"eventId": "EV001", "title": "国产芯片突破7nm工艺", "eventType": "技术突破", 
         "eventDate": "2026-05-15", "impactLevel": "high", "description": "国内某龙头企业宣布成功量产7nm芯片"},
        {"eventId": "EV002", "title": "AI大模型发布", "eventType": "产品发布",
         "eventDate": "2026-05-20", "impactLevel": "high", "description": "国内AI领军企业发布新一代大模型"},
        {"eventId": "EV003", "title": "算力需求爆发", "eventType": "行业趋势",
         "eventDate": "2026-05-25", "impactLevel": "high", "description": "数据中心建设加速，算力需求激增"},
        {"eventId": "EV004", "title": "机器人产业政策支持", "eventType": "政策利好",
         "eventDate": "2026-05-10", "impactLevel": "medium", "description": "国家出台机器人产业发展规划"},
        {"eventId": "EV005", "title": "卫星互联网组网完成", "eventType": "技术突破",
         "eventDate": "2026-05-18", "impactLevel": "high", "description": "国内低轨卫星互联网星座完成部署"},
        {"eventId": "EV006", "title": "CPO技术获得突破", "eventType": "技术突破",
         "eventDate": "2026-05-22", "impactLevel": "high", "description": "共封装光学技术取得重大进展"},
        {"eventId": "EV007", "title": "消费复苏信号", "eventType": "宏观经济",
         "eventDate": "2026-05-28", "impactLevel": "medium", "description": "消费数据超预期，内需回暖"},
        {"eventId": "EV008", "title": "新能源汽车销量创新高", "eventType": "行业趋势",
         "eventDate": "2026-05-30", "impactLevel": "high", "description": "新能源汽车月度销量突破百万"},
    ]
    
    cypher = """
    MERGE (e:MarketEvent {eventId: $eventId})
    SET e.title = $title,
        e.eventType = $eventType,
        e.eventDate = date($eventDate),
        e.impactLevel = $impactLevel,
        e.description = $description
    """
    
    with client.session() as session:
        for event in events:
            session.run(cypher, **event)
    
        # 创建事件与公司关联
        event_impacts = [
            ("EV001", "600745"), ("EV001", "002049"), ("EV001", "300661"),
            ("EV002", "300229"), ("EV002", "000977"), ("EV002", "603019"),
            ("EV003", "000977"), ("EV003", "603019"), ("EV003", "300502"),
            ("EV004", "300024"), ("EV004", "002527"), ("EV004", "300124"),
            ("EV005", "600118"), ("EV005", "600879"),
            ("EV006", "300502"), ("EV006", "600703"),
            ("EV007", "600519"), ("EV007", "000858"), ("EV007", "600887"),
            ("EV008", "002594"), ("EV008", "300750"),
        ]
    
        impact_cypher = """
        MATCH (e:MarketEvent {eventId: $eventId})
        MATCH (c:Company {stockCode: $stockCode})
        MERGE (e)-[:IMPACTS]->(c)
        """
    
        for event_id, stock_code in event_impacts:
            session.run(impact_cypher, eventId=event_id, stockCode=stock_code)
    
    print(f"✓ 已创建 {len(events)} 个市场事件，{len(event_impacts)} 条影响关系")


def print_statistics(client):
    """打印数据库统计信息"""
    print("\n📊 数据库统计信息:")
    with client.session() as session:
        # 节点统计
        result = session.run("""
            MATCH (n) 
            RETURN labels(n)[0] as label, count(*) as count 
            ORDER BY count DESC
        """).data()
        
        for row in result:
            print(f"  {row['label']}: {row['count']} 条")
        
        # 关系统计
        result = session.run("""
            MATCH ()-[r]->() 
            RETURN type(r) as relation, count(*) as count 
            ORDER BY count DESC
        """).data()
        
        print("\n  关系类型:")
        for row in result:
            print(f"    {row['relation']}: {row['count']} 条")
        
        # 龙头企业统计
        result = session.run("""
            MATCH (c:Company {isLeader: true})
            RETURN count(*) as leader_count, avg(c.moatLevel) as avg_moat
        """).data()[0]
        
        print(f"\n  龙头企业: {result['leader_count']} 家")
        print(f"  平均护城河等级: {round(result['avg_moat'], 2)}")


def main():
    """主函数"""
    print("=" * 60)
    print("      StockOntology 龙头战法数据库初始化")
    print("=" * 60)
    
    client = None
    try:
        # 连接数据库
        client = get_neo4j_client()
        print("\n🔌 连接到 Neo4j: " + NEO4J_URI)
        
        # 清空数据库
        clear_database(client)
        
        # 初始化约束
        init_constraints(client)
        
        # 初始化行业数据
        init_industry_data(client)
        
        # 初始化概念板块
        init_concept_data(client)
        
        # 初始化公司数据
        init_company_data(client)
        
        # 初始化供应链关系
        init_supply_chain(client)
        
        # 初始化概念关联
        init_concept_relations(client)
        
        # 初始化股票数据
        init_stock_data(client)
        
        # 初始化事件数据
        init_events(client)
        
        # 打印统计信息
        print_statistics(client)
        
        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
