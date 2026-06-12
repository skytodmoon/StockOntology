"""
龙头战法全赛道数据库初始化 + 行情数据拉取

根据《龙头股及供应链技术壁垒企业清单》初始化：
1. 行业分类（10大赛道）
2. 龙头公司 + 供应链企业（30+只）
3. 供应链关系
4. 拉取每只股票近半年行情数据 → 写入 Neo4j StockPrice 节点
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from loguru import logger
from app.core.database import get_neo4j_client
from app.core.graph import GraphBuilder

logger.info("=" * 60)
logger.info("龙头战法全赛道数据库初始化")
logger.info("=" * 60)


# ==================== 行业定义 ====================
INDUSTRIES = [
    # 一级行业
    {"code": "SEMICON", "name": "半导体", "level": 1},
    {"code": "AI", "name": "人工智能", "level": 1},
    {"code": "COMPUTING", "name": "算力", "level": 1},
    {"code": "AEROSPACE", "name": "航天", "level": 1},
    {"code": "ROBOT", "name": "机器人", "level": 1},
    {"code": "CONSUMER_ELEC", "name": "消费电子", "level": 1},
    {"code": "INDUSTRIAL_SW", "name": "工业软件", "level": 1},
    {"code": "NEW_MATERIAL", "name": "高端新材料", "level": 1},
    {"code": "BIOMED", "name": "生物医药", "level": 1},
    {"code": "PRECISION_EQUIP", "name": "精密装备", "level": 1},

    # 二级行业
    {"code": "CHIP_DESIGN", "name": "芯片设计", "level": 2},
    {"code": "CHIP_FOUNDRY", "name": "晶圆代工", "level": 2},
    {"code": "CHIP_EQUIP", "name": "半导体设备", "level": 2},
    {"code": "CHIP_MATERIAL", "name": "半导体材料", "level": 2},
    {"code": "AI_SOFTWARE", "name": "AI软件", "level": 2},
    {"code": "AI_CHIP", "name": "AI芯片", "level": 2},
    {"code": "OPTICAL", "name": "光模块", "level": 2},
    {"code": "SATELLITE", "name": "卫星", "level": 2},
    {"code": "INDUSTRIAL_ROBOT", "name": "工业机器人", "level": 2},
    {"code": "SUPPLY_CHAIN", "name": "供应链配套", "level": 2},
]

INDUSTRY_HIERARCHIES = [
    ("CHIP_DESIGN", "SEMICON"),
    ("CHIP_FOUNDRY", "SEMICON"),
    ("CHIP_EQUIP", "SEMICON"),
    ("CHIP_MATERIAL", "SEMICON"),
    ("AI_SOFTWARE", "AI"),
    ("AI_CHIP", "AI"),
    ("OPTICAL", "COMPUTING"),
    ("SATELLITE", "AEROSPACE"),
    ("INDUSTRIAL_ROBOT", "ROBOT"),
]


# ==================== 全赛道公司清单 ====================
COMPANIES = [
    # ---------- 半导体/芯片 ----------
    {
        "stockCode": "688981", "stockName": "中芯国际", "market": "SH",
        "industry": "晶圆代工", "industryCode": "CHIP_FOUNDRY",
        "marketCap": 10201.18 * 1e8, "leaderTag": "半导体龙头",
        "moat": "国内最大晶圆代工厂，覆盖成熟制程到先进制程，板块市值龙头",
        "moatType": "技术壁垒+国产替代",
    },
    {
        "stockCode": "002371", "stockName": "北方华创", "market": "SZ",
        "industry": "半导体设备", "industryCode": "CHIP_EQUIP",
        "marketCap": 1800 * 1e8, "leaderTag": "半导体设备龙头",
        "moat": "国内半导体设备龙头，覆盖刻蚀、沉积等核心设备，打破海外垄断",
        "moatType": "技术壁垒+客户粘性",
    },
    {
        "stockCode": "688012", "stockName": "中微公司", "market": "SH",
        "industry": "半导体设备", "industryCode": "CHIP_EQUIP",
        "marketCap": 1200 * 1e8, "leaderTag": "刻蚀设备龙头",
        "moat": "刻蚀设备龙头，突破5nm刻蚀技术，打破海外厂商技术封锁",
        "moatType": "技术壁垒+国际认证",
    },
    {
        "stockCode": "688072", "stockName": "拓荆科技", "market": "SH",
        "industry": "半导体设备", "industryCode": "CHIP_EQUIP",
        "marketCap": 350 * 1e8, "leaderTag": "薄膜沉积设备龙头",
        "moat": "国内唯一掌握PECVD核心技术的企业，薄膜沉积设备国产替代龙头",
        "moatType": "技术壁垒+唯一性",
    },
    {
        "stockCode": "002428", "stockName": "云南锗业", "market": "SZ",
        "industry": "半导体材料", "industryCode": "CHIP_MATERIAL",
        "marketCap": 120 * 1e8, "leaderTag": "锗材料龙头",
        "moat": "国内唯一磷化铟稳定量产企业，锗战略金属龙头，全球产能高度集中",
        "moatType": "资源垄断+技术壁垒",
    },
    {
        "stockCode": "688019", "stockName": "安集科技", "market": "SH",
        "industry": "半导体材料", "industryCode": "CHIP_MATERIAL",
        "marketCap": 200 * 1e8, "leaderTag": "CMP抛光液龙头",
        "moat": "国内CMP抛光液绝对龙头，率先完成先进制程全流程验证量产",
        "moatType": "技术壁垒+国产替代",
    },
    {
        "stockCode": "688047", "stockName": "龙芯中科", "market": "SH",
        "industry": "芯片设计", "industryCode": "CHIP_DESIGN",
        "marketCap": 500 * 1e8, "leaderTag": "自主CPU龙头",
        "moat": "A股唯一拥有完全自主可控CPU指令集根技术的企业",
        "moatType": "根技术壁垒+不可复刻",
    },
    {
        "stockCode": "688269", "stockName": "景嘉微", "market": "SZ",
        "industry": "芯片设计", "industryCode": "CHIP_DESIGN",
        "marketCap": 250 * 1e8, "leaderTag": "国产GPU龙头",
        "moat": "国内唯一实现民用+军用通用GPU规模化量产的企业",
        "moatType": "技术壁垒+军工壁垒",
    },

    # ---------- AI（纯算法/软件/大模型） ----------
    {
        "stockCode": "002230", "stockName": "科大讯飞", "market": "SZ",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 1289.62 * 1e8, "leaderTag": "AI软件龙头",
        "moat": "自研星火通用大模型，语音NLP算法、多场景AI软件落地，A股纯正AI算法龙头",
        "moatType": "技术壁垒+场景生态",
    },
    {
        "stockCode": "300033", "stockName": "同花顺", "market": "SZ",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 916.35 * 1e8, "leaderTag": "金融AI龙头",
        "moat": "金融AI算法、问财大模型，智能投研，用户壁垒极高",
        "moatType": "用户壁垒+数据壁垒",
    },
    {
        "stockCode": "688111", "stockName": "金山办公", "market": "SH",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 892.76 * 1e8, "leaderTag": "AI办公龙头",
        "moat": "WPS AI大模型，办公文生图、文档解析，用户基数壁垒深厚",
        "moatType": "用户壁垒+AI赋能",
    },
    {
        "stockCode": "300624", "stockName": "万兴科技", "market": "SZ",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 168.23 * 1e8, "leaderTag": "AIGC软件龙头",
        "moat": "天幕AIGC大模型，视频生成、图像创意，海外营收占比高",
        "moatType": "技术壁垒+海外渠道",
    },
    {
        "stockCode": "300229", "stockName": "拓尔思", "market": "SZ",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 100 * 1e8, "leaderTag": "NLP算法标杆",
        "moat": "国内NLP算法标杆，深耕语义理解二十余年，政务AI市占率领先",
        "moatType": "算法壁垒+数据壁垒",
    },
    {
        "stockCode": "688078", "stockName": "虹软科技", "market": "SH",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 80 * 1e8, "leaderTag": "端侧视觉AI龙头",
        "moat": "全球手机端视觉算法龙头，纯软件授权盈利模式，绑定华为小米",
        "moatType": "技术壁垒+客户绑定",
    },

    # ---------- 算力 ----------
    {
        "stockCode": "688041", "stockName": "海光信息", "market": "SH",
        "industry": "AI芯片", "industryCode": "AI_CHIP",
        "marketCap": 6233.41 * 1e8, "leaderTag": "国产算力龙头",
        "moat": "国产CPU+AI DCU芯片，x86架构授权，算力芯片双布局",
        "moatType": "技术壁垒+国产替代",
    },
    {
        "stockCode": "300308", "stockName": "中际旭创", "market": "SZ",
        "industry": "光模块", "industryCode": "OPTICAL",
        "marketCap": 1189.20 * 1e8, "leaderTag": "光模块龙头",
        "moat": "全球光模块绝对龙头，800G市占率超30%，1.6T率先量产",
        "moatType": "技术壁垒+全球份额",
    },
    {
        "stockCode": "688008", "stockName": "澜起科技", "market": "SH",
        "industry": "芯片设计", "industryCode": "CHIP_DESIGN",
        "marketCap": 850 * 1e8, "leaderTag": "内存接口芯片龙头",
        "moat": "全球内存接口芯片龙头，DDR5技术领先，配套算力芯片核心零部件",
        "moatType": "技术壁垒+全球份额",
    },
    {
        "stockCode": "603185", "stockName": "沪电股份", "market": "SZ",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 500 * 1e8, "leaderTag": "AI服务器PCB龙头",
        "moat": "突破高端AI服务器PCB卡脖子技术，适配1.6T光模块高频需求",
        "moatType": "技术壁垒+客户认证",
    },

    # ---------- 航天 ----------
    {
        "stockCode": "600118", "stockName": "中国卫星", "market": "SH",
        "industry": "卫星", "industryCode": "SATELLITE",
        "marketCap": 380.5 * 1e8, "leaderTag": "航天卫星龙头",
        "moat": "卫星研制、卫星应用，航天卫星领域龙头",
        "moatType": "技术壁垒+资质壁垒",
    },
    {
        "stockCode": "300503", "stockName": "昊志机电", "market": "SZ",
        "industry": "精密装备", "industryCode": "PRECISION_EQUIP",
        "marketCap": 60 * 1e8, "leaderTag": "特种电机龙头",
        "moat": "蓝箭航天液氧甲烷发动机独家电机供应商，机器人核心功能部件龙头",
        "moatType": "技术壁垒+独家供应",
    },
    {
        "stockCode": "688592", "stockName": "索辰科技", "market": "SH",
        "industry": "工业软件", "industryCode": "INDUSTRIAL_SW",
        "marketCap": 80 * 1e8, "leaderTag": "CAE仿真软件龙头",
        "moat": "国内唯一打破海外CAE软件垄断的厂商，航空航天CAE市占率72%",
        "moatType": "技术壁垒+国产唯一",
    },
    {
        "stockCode": "688308", "stockName": "欧科亿", "market": "SH",
        "industry": "精密装备", "industryCode": "PRECISION_EQUIP",
        "marketCap": 40 * 1e8, "leaderTag": "高精度刀具龙头",
        "moat": "高精度硬质合金刀具，可加工火箭耐高温合金部件",
        "moatType": "技术壁垒+工艺壁垒",
    },

    # ---------- 机器人 ----------
    {
        "stockCode": "002747", "stockName": "埃斯顿", "market": "SZ",
        "industry": "工业机器人", "industryCode": "INDUSTRIAL_ROBOT",
        "marketCap": 320.2 * 1e8, "leaderTag": "工业机器人龙头",
        "moat": "工业机器人整机、运动控制，国内工业机器人龙头",
        "moatType": "技术壁垒+规模效应",
    },
    {
        "stockCode": "688017", "stockName": "绿的谐波", "market": "SH",
        "industry": "工业机器人", "industryCode": "INDUSTRIAL_ROBOT",
        "marketCap": 150 * 1e8, "leaderTag": "谐波减速器龙头",
        "moat": "国产谐波减速器龙头，打破海外长期垄断，国内市占率超60%",
        "moatType": "技术壁垒+国产替代",
    },
    {
        "stockCode": "688716", "stockName": "中研股份", "market": "SH",
        "industry": "高端新材料", "industryCode": "NEW_MATERIAL",
        "marketCap": 60 * 1e8, "leaderTag": "PEEK材料龙头",
        "moat": "国内唯一实现人形机器人专用PEEK材料规模化量产的企业",
        "moatType": "技术壁垒+唯一量产",
    },
    {
        "stockCode": "300124", "stockName": "汇川技术", "market": "SZ",
        "industry": "工业机器人", "industryCode": "INDUSTRIAL_ROBOT",
        "marketCap": 2000 * 1e8, "leaderTag": "伺服系统龙头",
        "moat": "国内伺服系统绝对龙头，市占率第一，打破海外伺服技术垄断",
        "moatType": "技术壁垒+规模效应",
    },

    # ---------- 消费电子 ----------
    {
        "stockCode": "002475", "stockName": "立讯精密", "market": "SZ",
        "industry": "消费电子", "industryCode": "CONSUMER_ELEC",
        "marketCap": 3650.6 * 1e8, "leaderTag": "消费电子龙头",
        "moat": "消费电子精密制造，苹果全品类供应商，AI终端代工",
        "moatType": "客户粘性+精密制造",
    },
    {
        "stockCode": "002938", "stockName": "鹏鼎控股", "market": "SZ",
        "industry": "消费电子", "industryCode": "CONSUMER_ELEC",
        "marketCap": 800 * 1e8, "leaderTag": "FPC龙头",
        "moat": "全球PCB/FPC绝对龙头，苹果FPC核心供应商，市占率超60%",
        "moatType": "技术壁垒+客户绑定",
    },
    {
        "stockCode": "300433", "stockName": "蓝思科技", "market": "SZ",
        "industry": "消费电子", "industryCode": "CONSUMER_ELEC",
        "marketCap": 500 * 1e8, "leaderTag": "精密结构件龙头",
        "moat": "精密制造龙头，消费电子玻璃面板龙头，同时布局航天精密加工",
        "moatType": "技术壁垒+多元化",
    },

    # ---------- 海外巨头供应链 ----------
    {
        "stockCode": "002454", "stockName": "拓普集团", "market": "SZ",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 800 * 1e8, "leaderTag": "特斯拉执行器独家供应商",
        "moat": "特斯拉人形机器人执行器总成独家一级供应商，配套壁垒不可替代",
        "moatType": "独家供应+客户绑定",
    },
    {
        "stockCode": "002050", "stockName": "三花智控", "market": "SZ",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 1000 * 1e8, "leaderTag": "特斯拉热管理龙头",
        "moat": "特斯拉热管理核心Tier1龙头，人形机器人关节总成核心供应商",
        "moatType": "技术壁垒+客户绑定",
    },
    {
        "stockCode": "300136", "stockName": "信维通信", "market": "SZ",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 200 * 1e8, "leaderTag": "SpaceX连接器独家供应商",
        "moat": "SpaceX星链地面终端高频连接器独家供应商，毫米波天线市占率近100%",
        "moatType": "独家供应+技术壁垒",
    },
    {
        "stockCode": "002149", "stockName": "西部材料", "market": "SZ",
        "industry": "高端新材料", "industryCode": "NEW_MATERIAL",
        "marketCap": 150 * 1e8, "leaderTag": "航天铌合金独家供应商",
        "moat": "全球仅两家可供应SpaceX猛禽发动机铌合金材料，国内独家",
        "moatType": "资源垄断+技术壁垒",
    },
    {
        "stockCode": "605123", "stockName": "派克新材", "market": "SH",
        "industry": "精密装备", "industryCode": "PRECISION_EQUIP",
        "marketCap": 120 * 1e8, "leaderTag": "航空航天锻件龙头",
        "moat": "国内唯一批量供货SpaceX、NASA的高端锻件企业",
        "moatType": "认证壁垒+工艺壁垒",
    },
    {
        "stockCode": "301051", "stockName": "超捷股份", "market": "SZ",
        "industry": "精密装备", "industryCode": "PRECISION_EQUIP",
        "marketCap": 50 * 1e8, "leaderTag": "航空航天紧固件龙头",
        "moat": "A股极少数通过SpaceX、波音认证的精密连接件企业",
        "moatType": "认证壁垒+技术壁垒",
    },

    # ---------- 生物医药 ----------
    {
        "stockCode": "688180", "stockName": "君实生物", "market": "SH",
        "industry": "生物医药", "industryCode": "BIOMED",
        "marketCap": 400 * 1e8, "leaderTag": "创新药龙头",
        "moat": "国内首批自主研发PD-1药企，拥有全球专利布局",
        "moatType": "研发壁垒+专利壁垒",
    },
    {
        "stockCode": "300142", "stockName": "沃森生物", "market": "SZ",
        "industry": "生物医药", "industryCode": "BIOMED",
        "marketCap": 300 * 1e8, "leaderTag": "mRNA疫苗龙头",
        "moat": "A股稀缺掌握完整mRNA技术平台的企业，底层技术自主可控",
        "moatType": "技术壁垒+平台壁垒",
    },

    # ---------- 通信/光模块补充 ----------
    {
        "stockCode": "603989", "stockName": "艾华集团", "market": "SH",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 150 * 1e8, "leaderTag": "车载电容龙头",
        "moat": "特斯拉车载电容核心供应商，攻克车规级高压电容国产技术瓶颈",
        "moatType": "技术壁垒+客户认证",
    },
    {
        "stockCode": "300058", "stockName": "蓝色光标", "market": "SZ",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 200 * 1e8, "leaderTag": "营销AI龙头",
        "moat": "营销AI算法落地龙头，自研营销大模型，海量营销数据训练壁垒",
        "moatType": "数据壁垒+算法壁垒",
    },
    {
        "stockCode": "601360", "stockName": "三六零", "market": "SH",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 800 * 1e8, "leaderTag": "安全AI龙头",
        "moat": "国内网络安全AI算法绝对龙头，独有海量安全数据训练模型",
        "moatType": "数据壁垒+技术壁垒",
    },
    {
        "stockCode": "002405", "stockName": "四维图新", "market": "SZ",
        "industry": "AI软件", "industryCode": "AI_SOFTWARE",
        "marketCap": 200 * 1e8, "leaderTag": "自动驾驶算法龙头",
        "moat": "国内唯一具备全栈车规级AI导航与自动驾驶算法能力企业",
        "moatType": "技术壁垒+车规认证",
    },
    {
        "stockCode": "688599", "stockName": "天合光能", "market": "SH",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 500 * 1e8, "leaderTag": "光伏组件龙头",
        "moat": "苹果移动设备柔性光伏供电独家供应商，攻克超薄柔性发电技术",
        "moatType": "技术壁垒+客户绑定",
    },
    {
        "stockCode": "300750", "stockName": "宁德时代", "market": "SZ",
        "industry": "供应链配套", "industryCode": "SUPPLY_CHAIN",
        "marketCap": 8000 * 1e8, "leaderTag": "动力电池龙头",
        "moat": "全球动力电池龙头，苹果高端电池核心供应商，技术壁垒深厚",
        "moatType": "技术壁垒+规模效应",
    },
    {
        "stockCode": "688090", "stockName": "安博通", "market": "SH",
        "industry": "工业软件", "industryCode": "INDUSTRIAL_SW",
        "marketCap": 30 * 1e8, "leaderTag": "工控安全软件龙头",
        "moat": "国内工控安全软件稀缺标的，自主研发底层架构",
        "moatType": "技术壁垒+稀缺性",
    },
]


# ==================== 供应链关系 ====================
SUPPLY_CHAINS = [
    # 半导体供应链
    ("688012", "688981", "刻蚀设备供应"),      # 中微 → 中芯
    ("002371", "688981", "半导体设备供应"),    # 北方华创 → 中芯
    ("688072", "688981", "薄膜设备供应"),      # 拓荆 → 中芯
    ("688019", "688981", "CMP抛光液供应"),    # 安集 → 中芯
    ("002428", "688981", "锗材料供应"),        # 云南锗业 → 中芯

    # AI/算力供应链
    ("688041", "688008", "内存接口配套"),      # 海光 ↔ 澜起
    ("688008", "603185", "PCB配套"),           # 澜起 → 沪电
    ("300308", "688041", "光模块互联"),        # 中际旭创 → 海光

    # 机器人供应链
    ("688017", "002747", "谐波减速器供应"),    # 绿的谐波 → 埃斯顿
    ("300124", "002747", "伺服系统供应"),      # 汇川 → 埃斯顿
    ("688716", "002747", "PEEK材料供应"),      # 中研 → 埃斯顿

    # 特斯拉供应链
    ("002454", "002050", "执行器配套"),        # 拓普 ↔ 三花
    ("603989", "002050", "电容供应"),          # 艾华 → 三花

    # SpaceX供应链
    ("300136", "600118", "星链连接器供应"),    # 信维 → 中国卫星
    ("002149", "605123", "航天材料供应"),      # 西部材料 → 派克

    # 苹果供应链
    ("002938", "002475", "FPC供应"),           # 鹏鼎 → 立讯
    ("300433", "002475", "玻璃面板供应"),      # 蓝思 → 立讯
    ("300750", "002475", "电池供应"),          # 宁德 → 立讯
]


def create_industries(builder: GraphBuilder):
    """创建行业"""
    logger.info("创建行业分类...")
    count = builder.batch_create_industries(INDUSTRIES)
    logger.info(f"  创建 {count} 个行业")

    for child, parent in INDUSTRY_HIERARCHIES:
        builder.create_industry_hierarchy(parent, child)
    logger.info(f"  创建 {len(INDUSTRY_HIERARCHIES)} 个行业层级关系")


def create_companies(builder: GraphBuilder):
    """创建公司"""
    logger.info("创建公司...")
    count = 0
    for company in COMPANIES:
        if builder.create_company(company):
            builder.create_company_industry_relationship(
                company["stockCode"], company["industryCode"]
            )
            count += 1
    logger.info(f"  创建 {count} 个公司")


def create_supply_chains(builder: GraphBuilder):
    """创建供应链关系"""
    logger.info("创建供应链关系...")
    count = 0
    for supplier, customer, stype in SUPPLY_CHAINS:
        if builder.create_company_supply_relationship(supplier, customer, stype):
            count += 1
    logger.info(f"  创建 {count} 个供应链关系")


def fetch_and_store_price_data(builder: GraphBuilder):
    """
    拉取每只股票近半年行情数据，写入 Neo4j StockPrice 节点
    使用 AKShare 免费数据源
    """
    logger.info("拉取行情数据（AKShare）...")

    try:
        import akshare as ak
    except ImportError:
        logger.error("AKShare 未安装，请运行: pip install akshare")
        return

    stock_codes = [c["stockCode"] for c in COMPANIES]
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")

    success_count = 0
    fail_count = 0
    total_records = 0

    for i, code in enumerate(stock_codes):
        logger.info(f"  [{i+1}/{len(stock_codes)}] 拉取 {code} ...")
        try:
            # AKShare 获取历史行情
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if df is None or df.empty:
                logger.warning(f"    {code} 无数据")
                fail_count += 1
                continue

            # 写入 Neo4j
            records = 0
            for _, row in df.iterrows():
                trade_date = str(row["日期"])
                price_data = {
                    "stock_code": code,
                    "stockCode": code,
                    "trade_date": trade_date,
                    "tradeDate": trade_date,
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"]),
                    "change_pct": float(row["涨跌幅"]),
                    "turnover": float(row.get("换手率", 0)),
                }
                builder.create_stock_price(price_data)
                records += 1

            total_records += records
            success_count += 1
            logger.info(f"    {code} 写入 {records} 条")

            # 避免请求过快被限流
            time.sleep(0.5)

        except Exception as e:
            logger.warning(f"    {code} 失败: {e}")
            fail_count += 1
            time.sleep(1)

    logger.info(f"行情数据拉取完成: 成功 {success_count}, 失败 {fail_count}, 总记录 {total_records}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始初始化...")
    logger.info("=" * 60)

    builder = GraphBuilder()

    # 1. Schema
    logger.info("\n[Step 1/5] 初始化 Schema...")
    builder.init_schema()

    # 2. 行业
    logger.info("\n[Step 2/5] 创建行业分类...")
    create_industries(builder)

    # 3. 公司
    logger.info("\n[Step 3/5] 创建公司...")
    create_companies(builder)

    # 4. 供应链
    logger.info("\n[Step 4/5] 创建供应链关系...")
    create_supply_chains(builder)

    # 5. 行情数据
    logger.info("\n[Step 5/5] 拉取行情数据...")
    fetch_and_store_price_data(builder)

    # 完成
    logger.info("\n" + "=" * 60)
    logger.info("初始化完成！")
    logger.info("=" * 60)
    logger.info(f"\n总计：")
    logger.info(f"  行业: {len(INDUSTRIES)} 个")
    logger.info(f"  公司: {len(COMPANIES)} 只")
    logger.info(f"  供应链: {len(SUPPLY_CHAINS)} 条")
    logger.info(f"\n赛道分布：")
    sectors = {}
    for c in COMPANIES:
        tag = c.get("leaderTag", "其他")
        sector = tag.split("龙头")[0] if "龙头" in tag else tag
        sectors[sector] = sectors.get(sector, 0) + 1
    for sector, count in sorted(sectors.items(), key=lambda x: -x[1]):
        logger.info(f"  {sector}: {count} 只")


if __name__ == "__main__":
    main()
