"""
龙头战法数据库初始化脚本

基于"龙头战法"思想，重点初始化：
1. 半导体/芯片产业链龙头
2. AI/算力产业链龙头
3. 消费领域龙头
4. 供应链关系（突出技术护城河企业）
5. 行业事件和传导关系
6. 财务数据

使用方式：
    python init_leader_strategy.py
"""

import sys
import os
from pathlib import Path

# 添加 backend 目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

from loguru import logger
from app.core.database import get_neo4j_client
from app.core.graph import GraphBuilder
from app.core.reasoning import OntologyReasoner
from app.core.reasoning.causal_chain import CausalChain, ReasoningStep

logger.info("=" * 60)
logger.info("龙头战法数据库初始化")
logger.info("=" * 60)


def init_schema(builder: GraphBuilder):
    """初始化数据库 Schema"""
    logger.info("Step 1: 初始化 Schema...")
    builder.init_schema()
    logger.info("Schema 初始化完成")


def create_industries(builder: GraphBuilder):
    """创建行业分类（龙头战法核心赛道）"""
    logger.info("Step 2: 创建行业分类...")

    industries = [
        # 一级行业
        {"code": "SEMICON", "name": "半导体", "level": 1},
        {"code": "AI", "name": "人工智能", "level": 1},
        {"code": "COMPUTING", "name": "算力", "level": 1},
        {"code": "CONSUMER", "name": "消费", "level": 1},
        {"code": "NEWENERGY", "name": "新能源", "level": 1},
        {"code": "MEDICAL", "name": "医药", "level": 1},

        # 二级行业 - 半导体
        {"code": "CHIP_DESIGN", "name": "芯片设计", "level": 2},
        {"code": "CHIP_FOUNDRY", "name": "晶圆代工", "level": 2},
        {"code": "CHIP_PACKAGE", "name": "封装测试", "level": 2},
        {"code": "CHIP_EQUIP", "name": "半导体设备", "level": 2},
        {"code": "CHIP_MATERIAL", "name": "半导体材料", "level": 2},

        # 二级行业 - AI
        {"code": "AI_CHIP", "name": "AI芯片", "level": 2},
        {"code": "AI_SOFTWARE", "name": "AI软件", "level": 2},
        {"code": "AI_APPLICATION", "name": "AI应用", "level": 2},

        # 二级行业 - 算力
        {"code": "SERVER", "name": "服务器", "level": 2},
        {"code": "DATA_CENTER", "name": "数据中心", "level": 2},
        {"code": "CLOUD", "name": "云计算", "level": 2},

        # 二级行业 - 消费
        {"code": "LIQUOR", "name": "白酒", "level": 2},
        {"code": "HOME_APPLIANCE", "name": "家电", "level": 2},
        {"code": "CONSUMER_ELECTRONICS", "name": "消费电子", "level": 2},
    ]

    count = builder.batch_create_industries(industries)
    logger.info(f"创建 {count} 个行业")

    # 行业层级关系
    hierarchies = [
        ("CHIP_DESIGN", "SEMICON"),
        ("CHIP_FOUNDRY", "SEMICON"),
        ("CHIP_PACKAGE", "SEMICON"),
        ("CHIP_EQUIP", "SEMICON"),
        ("CHIP_MATERIAL", "SEMICON"),
        ("AI_CHIP", "AI"),
        ("AI_SOFTWARE", "AI"),
        ("AI_APPLICATION", "AI"),
        ("SERVER", "COMPUTING"),
        ("DATA_CENTER", "COMPUTING"),
        ("CLOUD", "COMPUTING"),
        ("LIQUOR", "CONSUMER"),
        ("HOME_APPLIANCE", "CONSUMER"),
        ("CONSUMER_ELECTRONICS", "CONSUMER"),
    ]

    for child, parent in hierarchies:
        builder.create_industry_hierarchy(parent, child)
    logger.info(f"创建 {len(hierarchies)} 个行业层级关系")


def create_leader_companies(builder: GraphBuilder):
    """创建龙头公司（重点突出技术护城河）"""
    logger.info("Step 3: 创建龙头公司...")

    companies = [
        # ==================== 半导体龙头 ====================
        {
            "stockCode": "688981", "stockName": "中芯国际",
            "market": "SH", "industry": "晶圆代工", "industryCode": "CHIP_FOUNDRY",
            "marketCap": 450000000000, "peRatio": 85, "pbRatio": 2.1,
            "listDate": "2020-07-16",
            "moat": "国内最先进的晶圆代工厂，14nm量产，7nm研发中，国产替代核心标的",
            "moatType": "技术壁垒+国产替代",
            "leaderTag": "半导体龙头",
        },
        {
            "stockCode": "002371", "stockName": "北方华创",
            "market": "SZ", "industry": "半导体设备", "industryCode": "CHIP_EQUIP",
            "marketCap": 180000000000, "peRatio": 65, "pbRatio": 8.5,
            "listDate": "2010-03-31",
            "moat": "国内半导体设备龙头，刻蚀机、PVD、CVD等多款设备进入产线，国产替代加速",
            "moatType": "技术壁垒+客户粘性",
            "leaderTag": "半导体设备龙头",
        },
        {
            "stockCode": "688012", "stockName": "中微公司",
            "market": "SH", "industry": "半导体设备", "industryCode": "CHIP_EQUIP",
            "marketCap": 120000000000, "peRatio": 90, "pbRatio": 12,
            "listDate": "2019-07-22",
            "moat": "刻蚀设备国际领先，5nm刻蚀机已通过台积电验证，技术护城河深厚",
            "moatType": "技术壁垒+国际认证",
            "leaderTag": "刻蚀设备龙头",
        },
        {
            "stockCode": "688008", "stockName": "澜起科技",
            "market": "SH", "industry": "芯片设计", "industryCode": "CHIP_DESIGN",
            "marketCap": 85000000000, "peRatio": 45, "pbRatio": 6.2,
            "listDate": "2019-07-08",
            "moat": "内存接口芯片全球龙头，DDR5技术领先，AI服务器内存升级核心受益",
            "moatType": "技术壁垒+全球份额",
            "leaderTag": "内存接口芯片龙头",
        },
        {
            "stockCode": "688396", "stockName": "华峰测控",
            "market": "SH", "industry": "半导体设备", "industryCode": "CHIP_EQUIP",
            "marketCap": 25000000000, "peRatio": 55, "pbRatio": 8,
            "listDate": "2020-02-18",
            "moat": "模拟及混合信号测试设备龙头，国产替代唯一标的，客户覆盖主流封测厂",
            "moatType": "技术壁垒+稀缺性",
            "leaderTag": "测试设备龙头",
        },

        # ==================== AI/算力龙头 ====================
        {
            "stockCode": "002230", "stockName": "科大讯飞",
            "market": "SZ", "industry": "AI软件", "industryCode": "AI_SOFTWARE",
            "marketCap": 120000000000, "peRatio": 120, "pbRatio": 8,
            "listDate": "2008-05-12",
            "moat": "国内AI语音技术龙头，星火大模型核心标的，教育+医疗+政务多场景落地",
            "moatType": "技术壁垒+场景生态",
            "leaderTag": "AI语音龙头",
        },
        {
            "stockCode": "688256", "stockName": "寒武纪",
            "market": "SH", "industry": "AI芯片", "industryCode": "AI_CHIP",
            "marketCap": 200000000000, "peRatio": -1, "pbRatio": 25,
            "listDate": "2020-07-20",
            "moat": "国内AI芯片设计龙头，思元系列芯片对标英伟达，国产算力核心标的",
            "moatType": "技术壁垒+国产替代",
            "leaderTag": "AI芯片龙头",
        },
        {
            "stockCode": "002415", "stockName": "海康威视",
            "market": "SZ", "industry": "AI应用", "industryCode": "AI_APPLICATION",
            "marketCap": 350000000000, "peRatio": 22, "pbRatio": 4.5,
            "listDate": "2010-05-28",
            "moat": "全球安防AI龙头，AIoT平台型企业，视觉AI技术领先，海外收入占比高",
            "moatType": "技术壁垒+规模效应",
            "leaderTag": "AI安防龙头",
        },
        {
            "stockCode": "603019", "stockName": "中科曙光",
            "market": "SH", "industry": "服务器", "industryCode": "SERVER",
            "marketCap": 80000000000, "peRatio": 35, "pbRatio": 4,
            "listDate": "2014-11-06",
            "moat": "国产服务器龙头，与AMD合资海光信息，国产CPU核心标的，算力基建受益",
            "moatType": "技术壁垒+国产替代",
            "leaderTag": "国产算力龙头",
        },
        {
            "stockCode": "688111", "stockName": "金山办公",
            "market": "SH", "industry": "AI软件", "industryCode": "AI_SOFTWARE",
            "marketCap": 150000000000, "peRatio": 80, "pbRatio": 15,
            "listDate": "2019-11-18",
            "moat": "国产办公软件龙头，WPS AI核心标的，4亿用户基础，AI+办公生态",
            "moatType": "用户壁垒+AI赋能",
            "leaderTag": "AI办公龙头",
        },

        # ==================== 消费龙头 ====================
        {
            "stockCode": "600519", "stockName": "贵州茅台",
            "market": "SH", "industry": "白酒", "industryCode": "LIQUOR",
            "marketCap": 2100000000000, "peRatio": 28, "pbRatio": 8,
            "listDate": "2001-08-27",
            "moat": "白酒之王，品牌护城河极深，定价权强，现金流充沛，消费升级核心标的",
            "moatType": "品牌壁垒+定价权",
            "leaderTag": "白酒龙头",
        },
        {
            "stockCode": "000858", "stockName": "五粮液",
            "market": "SZ", "industry": "白酒", "industryCode": "LIQUOR",
            "marketCap": 500000000000, "peRatio": 20, "pbRatio": 5,
            "listDate": "1998-04-27",
            "moat": "浓香型白酒龙头，品牌力强，渠道改革效果显著，高端白酒第二极",
            "moatType": "品牌壁垒+渠道",
            "leaderTag": "浓香白酒龙头",
        },
        {
            "stockCode": "000651", "stockName": "格力电器",
            "market": "SZ", "industry": "家电", "industryCode": "HOME_APPLIANCE",
            "marketCap": 200000000000, "peRatio": 8, "pbRatio": 2.5,
            "listDate": "1996-11-18",
            "moat": "空调行业绝对龙头，市占率第一，技术积累深厚，渠道覆盖全国",
            "moatType": "规模效应+渠道",
            "leaderTag": "空调龙头",
        },
        {
            "stockCode": "000333", "stockName": "美的集团",
            "market": "SZ", "industry": "家电", "industryCode": "HOME_APPLIANCE",
            "marketCap": 400000000000, "peRatio": 12, "pbRatio": 3.5,
            "listDate": "2013-09-18",
            "moat": "白电龙头，多元化布局领先，机器人+楼宇科技第二增长曲线",
            "moatType": "规模效应+多元化",
            "leaderTag": "白电龙头",
        },

        # ==================== 供应链关键企业（技术护城河） ====================
        {
            "stockCode": "002475", "stockName": "立讯精密",
            "market": "SZ", "industry": "消费电子", "industryCode": "CONSUMER_ELECTRONICS",
            "marketCap": 250000000000, "peRatio": 25, "pbRatio": 5,
            "listDate": "2010-09-15",
            "moat": "苹果供应链核心企业，精密制造能力领先，汽车电子+通信第二增长曲线",
            "moatType": "客户粘性+精密制造",
            "leaderTag": "精密制造龙头",
        },
        {
            "stockCode": "300750", "stockName": "宁德时代",
            "market": "SZ", "industry": "新能源", "industryCode": "NEWENERGY",
            "marketCap": 800000000000, "peRatio": 20, "pbRatio": 4,
            "listDate": "2018-06-11",
            "moat": "全球动力电池龙头，市占率35%+，技术领先（麒麟电池），客户覆盖主流车企",
            "moatType": "技术壁垒+规模效应",
            "leaderTag": "动力电池龙头",
        },
        {
            "stockCode": "601012", "stockName": "隆基绿能",
            "market": "SH", "industry": "新能源", "industryCode": "NEWENERGY",
            "marketCap": 200000000000, "peRatio": 15, "pbRatio": 2.5,
            "listDate": "2012-04-11",
            "moat": "全球光伏龙头，单晶硅片技术领先，BC电池技术路线引领者",
            "moatType": "技术壁垒+规模效应",
            "leaderTag": "光伏龙头",
        },
        {
            "stockCode": "688036", "stockName": "传音控股",
            "market": "SH", "industry": "消费电子", "industryCode": "CONSUMER_ELECTRONICS",
            "marketCap": 80000000000, "peRatio": 15, "pbRatio": 4,
            "listDate": "2019-09-30",
            "moat": "非洲手机之王，新兴市场龙头，本地化能力极强，AI手机布局领先",
            "moatType": "市场壁垒+本地化",
            "leaderTag": "新兴市场手机龙头",
        },
        {
            "stockCode": "002241", "stockName": "歌尔股份",
            "market": "SZ", "industry": "消费电子", "industryCode": "CONSUMER_ELECTRONICS",
            "marketCap": 60000000000, "peRatio": 30, "pbRatio": 3,
            "listDate": "2008-05-22",
            "moat": "VR/AR设备代工龙头，苹果Vision Pro供应链，声学技术领先",
            "moatType": "技术壁垒+客户绑定",
            "leaderTag": "VR设备龙头",
        },

        # ==================== 医药龙头 ====================
        {
            "stockCode": "600276", "stockName": "恒瑞医药",
            "market": "SH", "industry": "医药", "industryCode": "MEDICAL",
            "marketCap": 300000000000, "peRatio": 50, "pbRatio": 8,
            "listDate": "2000-10-18",
            "moat": "国内创新药龙头，研发管线丰富，PD-1+ADC+GLP-1多靶点布局",
            "moatType": "研发壁垒+管线",
            "leaderTag": "创新药龙头",
        },
    ]

    count = 0
    for company in companies:
        if builder.create_company(company):
            builder.create_company_industry_relationship(
                company["stockCode"], company["industryCode"]
            )
            count += 1
    logger.info(f"创建 {count} 个龙头公司")


def create_supply_chain(builder: GraphBuilder):
    """创建供应链关系（突出技术护城河企业）"""
    logger.info("Step 4: 创建供应链关系...")

    supply_chains = [
        # 半导体供应链
        ("688012", "688981", "设备供应"),      # 中微 → 中芯（刻蚀设备）
        ("002371", "688981", "设备供应"),      # 北方华创 → 中芯（多种设备）
        ("688396", "688981", "设备供应"),      # 华峰测控 → 中芯（测试设备）
        ("002371", "002371", "设备供应"),      # 北方华创 → 各大晶圆厂

        # AI/算力供应链
        ("688256", "603019", "芯片供应"),      # 寒武纪 → 曙光（AI芯片）
        ("688008", "603019", "芯片供应"),      # 澜起 → 曙光（内存接口）
        ("002230", "002415", "技术合作"),      # 讯飞 → 海康（AI算法）

        # 消费电子供应链
        ("002475", "600519", "包装供应"),      # 立讯 → 茅台（举例：精密包装）
        ("002475", "000333", "组件供应"),      # 立讯 → 美的（连接器）
        ("002241", "002475", "组件供应"),      # 歌尔 → 立讯（声学组件）

        # 新能源供应链
        ("300750", "000333", "电池供应"),      # 宁德 → 美的（储能电池）
        ("601012", "300750", "材料供应"),      # 隆基 → 宁德（光伏+储能）
    ]

    count = 0
    for supplier, customer, stype in supply_chains:
        if builder.create_company_supply_relationship(supplier, customer, stype):
            count += 1
    logger.info(f"创建 {count} 个供应链关系")


def create_competition(builder: GraphBuilder):
    """创建竞争关系"""
    logger.info("Step 5: 创建竞争关系...")

    competitions = [
        # 半导体竞争
        ("688981", "688981", "High"),    # 中芯 vs 国际大厂
        ("002371", "688012", "High"),    # 北方华创 vs 中微（设备领域）

        # AI竞争
        ("688256", "688256", "High"),    # 寒武纪 vs 国际AI芯片
        ("002230", "688111", "Medium"),  # 讯飞 vs 金山（AI应用）

        # 消费竞争
        ("600519", "000858", "High"),    # 茅台 vs 五粮液
        ("000651", "000333", "High"),    # 格力 vs 美的

        # 新能源竞争
        ("300750", "300750", "High"),    # 宁德 vs 国际电池厂
        ("601012", "601012", "High"),    # 隆基 vs 国际光伏
    ]

    count = 0
    for c1, c2, level in competitions:
        if c1 != c2:  # 避免自己和自己竞争
            if builder.create_company_competitor_relationship(c1, c2, level):
                count += 1
    logger.info(f"创建 {count} 个竞争关系")


def create_events(builder: GraphBuilder):
    """创建市场事件（体现传导链）"""
    logger.info("Step 6: 创建市场事件...")

    events = [
        {
            "eventId": "EVT001",
            "title": "美国扩大对华芯片出口管制",
            "eventType": "PolicyEvent",
            "eventDate": "2024-12-02",
            "impactLevel": "High",
            "content": "美国商务部将更多中国半导体企业列入实体清单，限制先进芯片和设备出口",
        },
        {
            "eventId": "EVT002",
            "title": "国务院发布人工智能发展规划",
            "eventType": "PolicyEvent",
            "eventDate": "2024-11-15",
            "impactLevel": "High",
            "content": "国务院发布新一代人工智能发展规划，提出到2030年AI核心产业规模超过1万亿",
        },
        {
            "eventId": "EVT003",
            "title": "英伟达发布新一代AI芯片B200",
            "eventType": "CompanyEvent",
            "eventDate": "2024-11-20",
            "impactLevel": "High",
            "content": "英伟达发布Blackwell架构B200芯片，AI算力提升30倍，推动全球算力基建",
        },
        {
            "eventId": "EVT004",
            "title": "国务院发布促消费政策",
            "eventType": "PolicyEvent",
            "eventDate": "2024-12-01",
            "impactLevel": "Medium",
            "content": "国务院办公厅印发《关于进一步释放消费潜力促进消费持续恢复的意见》",
        },
        {
            "eventId": "EVT005",
            "title": "华为发布昇腾910C AI芯片",
            "eventType": "CompanyEvent",
            "eventDate": "2024-11-25",
            "impactLevel": "High",
            "content": "华为发布昇腾910C AI芯片，性能对标英伟达A100，国产算力迎来突破",
        },
        {
            "eventId": "EVT006",
            "title": "全球半导体设备市场规模创新高",
            "eventType": "MacroEvent",
            "eventDate": "2024-11-10",
            "impactLevel": "Medium",
            "content": "SEMI预计2024年全球半导体设备市场规模将突破1000亿美元，中国大陆占比超30%",
        },
    ]

    count = 0
    for event in events:
        if builder.create_event(event):
            count += 1
    logger.info(f"创建 {count} 个市场事件")

    # 创建事件影响关系
    impacts = [
        # EVT001: 美国芯片管制 → 利好国产替代
        ("EVT001", "688981", "Company", {"impactDirection": "positive", "reason": "国产替代加速"}),
        ("EVT001", "002371", "Company", {"impactDirection": "positive", "reason": "设备国产化需求增加"}),
        ("EVT001", "688012", "Company", {"impactDirection": "positive", "reason": "刻蚀设备国产化"}),
        ("EVT001", "688256", "Company", {"impactDirection": "positive", "reason": "AI芯片国产化"}),
        ("EVT001", "603019", "Company", {"impactDirection": "positive", "reason": "国产算力需求增加"}),

        # EVT002: AI发展规划 → 利好AI产业链
        ("EVT002", "002230", "Company", {"impactDirection": "positive", "reason": "AI政策利好"}),
        ("EVT002", "688256", "Company", {"impactDirection": "positive", "reason": "AI芯片需求增加"}),
        ("EVT002", "688111", "Company", {"impactDirection": "positive", "reason": "AI应用落地加速"}),
        ("EVT002", "002415", "Company", {"impactDirection": "positive", "reason": "AI安防需求增加"}),

        # EVT003: 英伟达B200 → 利好算力产业链
        ("EVT003", "603019", "Company", {"impactDirection": "positive", "reason": "算力基建需求"}),
        ("EVT003", "688008", "Company", {"impactDirection": "positive", "reason": "内存接口需求增加"}),

        # EVT004: 促消费 → 利好消费龙头
        ("EVT004", "600519", "Company", {"impactDirection": "positive", "reason": "消费升级受益"}),
        ("EVT004", "000858", "Company", {"impactDirection": "positive", "reason": "高端白酒需求"}),
        ("EVT004", "000333", "Company", {"impactDirection": "positive", "reason": "家电消费回暖"}),
        ("EVT004", "000651", "Company", {"impactDirection": "positive", "reason": "家电消费回暖"}),

        # EVT005: 华为昇腾 → 利好国产算力
        ("EVT005", "688256", "Company", {"impactDirection": "positive", "reason": "国产AI芯片生态"}),
        ("EVT005", "603019", "Company", {"impactDirection": "positive", "reason": "国产算力服务器"}),

        # EVT006: 半导体设备市场增长 → 利好设备龙头
        ("EVT006", "002371", "Company", {"impactDirection": "positive", "reason": "设备订单增加"}),
        ("EVT006", "688012", "Company", {"impactDirection": "positive", "reason": "刻蚀设备需求"}),
        ("EVT006", "688396", "Company", {"impactDirection": "positive", "reason": "测试设备需求"}),

        # 事件→行业影响（用于传导推理）
        ("EVT001", "SEMICON", "Industry", {"impactDirection": "positive", "reason": "半导体国产化"}),
        ("EVT002", "AI", "Industry", {"impactDirection": "positive", "reason": "AI产业政策"}),
        ("EVT003", "COMPUTING", "Industry", {"impactDirection": "positive", "reason": "算力需求增长"}),
        ("EVT004", "CONSUMER", "Industry", {"impactDirection": "positive", "reason": "消费促进"}),
        ("EVT005", "AI", "Industry", {"impactDirection": "positive", "reason": "国产AI生态"}),
        ("EVT006", "SEMICON", "Industry", {"impactDirection": "positive", "reason": "设备市场增长"}),
    ]

    impact_count = 0
    for event_id, target_code, target_type, data in impacts:
        if builder.create_event_impact_relationship(event_id, target_code, target_type, data):
            impact_count += 1
    logger.info(f"创建 {impact_count} 个事件影响关系")


def create_financial_reports(builder: GraphBuilder):
    """创建财务报告"""
    logger.info("Step 7: 创建财务报告...")

    reports = [
        # 半导体龙头
        {"stockCode": "688981", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 45000000000, "netProfit": 8000000000, "eps": 0.45, "roe": 0.06, "peRatio": 85, "pbRatio": 2.1},
        {"stockCode": "002371", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 18000000000, "netProfit": 3500000000, "eps": 1.2, "roe": 0.12, "peRatio": 65, "pbRatio": 8.5},
        {"stockCode": "688012", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 5000000000, "netProfit": 1200000000, "eps": 1.5, "roe": 0.08, "peRatio": 90, "pbRatio": 12},

        # AI/算力龙头
        {"stockCode": "002230", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 15000000000, "netProfit": 1500000000, "eps": 0.65, "roe": 0.05, "peRatio": 120, "pbRatio": 8},
        {"stockCode": "688256", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 2000000000, "netProfit": -500000000, "eps": -1.2, "roe": -0.05, "peRatio": -1, "pbRatio": 25},
        {"stockCode": "603019", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 80000000000, "netProfit": 5000000000, "eps": 1.8, "roe": 0.1, "peRatio": 35, "pbRatio": 4},

        # 消费龙头
        {"stockCode": "600519", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 120000000000, "netProfit": 60000000000, "eps": 48, "roe": 0.25, "peRatio": 28, "pbRatio": 8},
        {"stockCode": "000858", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 60000000000, "netProfit": 22000000000, "eps": 5.8, "roe": 0.18, "peRatio": 20, "pbRatio": 5},
        {"stockCode": "000651", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 150000000000, "netProfit": 20000000000, "eps": 3.5, "roe": 0.2, "peRatio": 8, "pbRatio": 2.5},
        {"stockCode": "000333", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 280000000000, "netProfit": 28000000000, "eps": 4.0, "roe": 0.18, "peRatio": 12, "pbRatio": 3.5},

        # 新能源龙头
        {"stockCode": "300750", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 280000000000, "netProfit": 35000000000, "eps": 8.0, "roe": 0.15, "peRatio": 20, "pbRatio": 4},
        {"stockCode": "601012", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 80000000000, "netProfit": 10000000000, "eps": 1.3, "roe": 0.1, "peRatio": 15, "pbRatio": 2.5},

        # 供应链企业
        {"stockCode": "002475", "reportDate": "2024-09-30", "reportType": "Q3", "revenue": 180000000000, "netProfit": 12000000000, "eps": 1.7, "roe": 0.12, "peRatio": 25, "pbRatio": 5},
    ]

    count = builder.batch_create_financial_reports(reports)
    logger.info(f"创建 {count} 份财务报告")

    # 创建公司-报告关系
    for report in reports:
        builder.create_company_report_relationship(
            report["stockCode"], report["reportDate"], report["reportType"]
        )


def create_investors(builder: GraphBuilder):
    """创建机构投资者"""
    logger.info("Step 8: 创建机构投资者...")

    investors = [
        {"investorId": "INV001", "name": "易方达蓝筹精选", "type": "Fund"},
        {"investorId": "INV002", "name": "中欧医疗健康", "type": "Fund"},
        {"investorId": "INV003", "name": "华夏芯片ETF", "type": "ETF"},
        {"investorId": "INV004", "name": "国泰CES半导体芯片", "type": "ETF"},
        {"investorId": "INV005", "name": "招商中证白酒", "type": "ETF"},
    ]

    for inv in investors:
        builder.create_investor(inv)
    logger.info(f"创建 {len(investors)} 个机构投资者")

    # 持仓关系
    holdings = [
        ("INV001", "600519", {"shares": 5000000, "ratio": 0.004}),
        ("INV001", "000858", {"shares": 3000000, "ratio": 0.008}),
        ("INV003", "688981", {"shares": 2000000, "ratio": 0.003}),
        ("INV003", "002371", {"shares": 1500000, "ratio": 0.008}),
        ("INV003", "688256", {"shares": 1000000, "ratio": 0.005}),
        ("INV004", "688981", {"shares": 3000000, "ratio": 0.004}),
        ("INV004", "002371", {"shares": 2000000, "ratio": 0.011}),
        ("INV005", "600519", {"shares": 8000000, "ratio": 0.006}),
        ("INV005", "000858", {"shares": 5000000, "ratio": 0.013}),
    ]

    hold_count = 0
    for inv_id, stock_code, data in holdings:
        if builder.create_investor_holding_relationship(inv_id, stock_code, data):
            hold_count += 1
    logger.info(f"创建 {hold_count} 个持仓关系")


def run_reasoning_demo():
    """运行推理演示"""
    logger.info("Step 9: 运行推理演示...")

    try:
        reasoner = OntologyReasoner()

        # 演示：推导"美国芯片管制"的影响传导链
        logger.info("\n" + "=" * 60)
        logger.info("演示：推导事件 EVT001 (美国芯片管制) 的影响传导链")
        logger.info("=" * 60)

        chain = reasoner.trace_impact_chain("EVT001")
        logger.info(f"\n{chain.get_chain_text()}")

        # 演示：计算中芯国际的累积影响
        logger.info("\n" + "=" * 60)
        logger.info("演示：计算中芯国际 (688981) 的累积影响")
        logger.info("=" * 60)

        impact = reasoner.get_accumulated_impact("688981", days=90)
        logger.info(f"累积影响分数: {impact.get('accumulated_score', 0)}")
        logger.info(f"事件数量: {impact.get('event_count', 0)}")
        for event in impact.get("events", []):
            logger.info(f"  - {event.get('title', '')}: {event.get('impact_score', 0)}")

    except Exception as e:
        logger.warning(f"推理演示跳过（需要数据库连接）: {e}")


def main():
    """主函数"""
    logger.info("开始初始化龙头战法数据库...")

    try:
        # 初始化图谱构建器
        builder = GraphBuilder()

        # 1. 初始化 Schema
        init_schema(builder)

        # 2. 创建行业
        create_industries(builder)

        # 3. 创建龙头公司
        create_leader_companies(builder)

        # 4. 创建供应链关系
        create_supply_chain(builder)

        # 5. 创建竞争关系
        create_competition(builder)

        # 6. 创建市场事件
        create_events(builder)

        # 7. 创建财务报告
        create_financial_reports(builder)

        # 8. 创建投资者
        create_investors(builder)

        # 9. 运行推理演示
        run_reasoning_demo()

        logger.info("\n" + "=" * 60)
        logger.info("龙头战法数据库初始化完成！")
        logger.info("=" * 60)
        logger.info("\n已创建：")
        logger.info("  - 20+ 行业分类（半导体/AI/算力/消费/新能源）")
        logger.info("  - 20+ 龙头公司（含技术护城河描述）")
        logger.info("  - 13+ 供应链关系（突出技术壁垒企业）")
        logger.info("  - 6 个市场事件（含传导影响关系）")
        logger.info("  - 13+ 份财务报告")
        logger.info("  - 5 个机构投资者 + 9 个持仓关系")
        logger.info("\n龙头战法核心标的：")
        logger.info("  半导体：中芯国际(688981)、北方华创(002371)、中微公司(688012)")
        logger.info("  AI/算力：寒武纪(688256)、科大讯飞(002230)、中科曙光(603019)")
        logger.info("  消费：贵州茅台(600519)、五粮液(000858)、美的集团(000333)")
        logger.info("  新能源：宁德时代(300750)、隆基绿能(601012)")
        logger.info("\n技术护城河企业：")
        logger.info("  - 中微公司：5nm刻蚀机通过台积电验证")
        logger.info("  - 澜起科技：DDR5内存接口全球龙头")
        logger.info("  - 寒武纪：国产AI芯片设计龙头")
        logger.info("  - 北方华创：半导体设备国产替代核心")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
