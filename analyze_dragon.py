#!/usr/bin/env python3
"""
龙头战法分析工具

基于龙头战法思想，分析半导体、芯片、AI、航天、机器人、算力、消费等领域的龙头股及其供应链关系。
"""

import sys
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class DragonAnalysis:
    def __init__(self):
        self.client = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def close(self):
        self.client.close()
    
    def get_dragon_stocks_by_industry(self, industry_code=None):
        """获取龙头股列表"""
        query = """
            MATCH (c:Company {isLeader: true})
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            WHERE $industry_code IS NULL OR i.code = $industry_code
            RETURN c.stockCode, c.stockName, i.name as industry, 
                   c.moatLevel, c.moatType, c.marketCap, c.roe
            ORDER BY c.marketCap DESC
        """
        with self.client.session() as session:
            result = session.run(query, industry_code=industry_code)
            return result.data()
    
    def get_supply_chain(self, stock_code, depth=2):
        """获取供应链关系"""
        query = f"""
            MATCH path = (c:Company {{stockCode: $stockCode}})-[*1..{depth}]-(related)
            WITH nodes(path) as ns, relationships(path) as rs
            UNWIND ns as n
            WITH collect(DISTINCT {{data: n, labels: labels(n), id: elementId(n)}}) as nodes, rs
            UNWIND rs as r
            WITH nodes, collect(DISTINCT {{type: type(r), id: elementId(r), 
                source: elementId(startNode(r)), target: elementId(endNode(r)),
                description: coalesce(r.description, '')}}) as relationships
            RETURN nodes, relationships
        """
        with self.client.session() as session:
            result = session.run(query, stockCode=stock_code).data()
            return result[0] if result else None
    
    def get_hightech_moat_companies(self, min_moat=4):
        """获取具备技术护城河的企业"""
        query = """
            MATCH (c:Company)
            WHERE c.moatLevel >= $min_moat AND c.isLeader = true
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            RETURN c.stockCode, c.stockName, i.name as industry,
                   c.moatLevel, c.moatType, c.description
            ORDER BY c.moatLevel DESC, c.marketCap DESC
        """
        with self.client.session() as session:
            result = session.run(query, min_moat=min_moat)
            return result.data()
    
    def get_concept_stocks(self, concept_code):
        """获取概念板块股票"""
        query = """
            MATCH (c:Company)-[:BELONGS_TO_CONCEPT]->(co:Concept {code: $concept_code})
            RETURN c.stockCode, c.stockName, co.name as concept, c.isLeader
            ORDER BY c.isLeader DESC, c.marketCap DESC
        """
        with self.client.session() as session:
            result = session.run(query, concept_code=concept_code)
            return result.data()
    
    def get_industry_hierarchy(self):
        """获取行业层级"""
        query = """
            MATCH (child:Industry)-[:BELONGS_TO]->(parent:Industry)
            RETURN parent.name as parent, collect(child.name) as children
            ORDER BY parent.name
        """
        with self.client.session() as session:
            result = session.run(query)
            return result.data()
    
    def analyze_dragon_strategy(self):
        """龙头战法综合分析"""
        print("\n" + "="*70)
        print("                    🐉 龙头战法综合分析报告")
        print("="*70)
        
        # 1. 各行业龙头分布
        print("\n📊 一、各行业龙头分布")
        print("-" * 50)
        query = """
            MATCH (c:Company {isLeader: true})-[:BELONGS_TO]->(i:Industry)
            WHERE i.level = 1
            RETURN i.name as industry, count(*) as count, 
                   sum(c.marketCap) as totalMarketCap
            ORDER BY count DESC
        """
        with self.client.session() as session:
            result = session.run(query).data()
            for row in result:
                print(f"  {row['industry']:10s} | 龙头数: {row['count']:2d} | 总市值: {row['totalMarketCap']:6d}亿")
        
        # 2. 高护城河企业分析
        print("\n🛡️ 二、高护城河企业分析(护城河等级≥4)")
        print("-" * 50)
        query = """
            MATCH (c:Company)
            WHERE c.moatLevel >= 4
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            WHERE i.level = 1
            RETURN i.name as industry, count(*) as count, avg(c.moatLevel) as avgMoat
            ORDER BY count DESC
        """
        with self.client.session() as session:
            result = session.run(query).data()
            for row in result:
                print(f"  {row['industry']:10s} | 企业数: {row['count']:2d} | 平均护城河: {row['avgMoat']:.2f}")
        
        # 3. 供应链核心企业
        print("\n🔗 三、供应链核心企业")
        print("-" * 50)
        query = """
            MATCH (supplier)-[:SUPPLIES]->(customer)
            WHERE supplier.isLeader = true AND customer.isLeader = true
            RETURN supplier.stockCode, supplier.stockName, customer.stockCode, customer.stockName
            LIMIT 10
        """
        with self.client.session() as session:
            result = session.run(query).data()
            for row in result:
                print(f"  {row['supplier.stockCode']} {row['supplier.stockName']:10s} --> {row['customer.stockCode']} {row['customer.stockName']}")
        
        # 4. 热门概念板块
        print("\n🔥 四、热门概念板块")
        print("-" * 50)
        query = """
            MATCH (co:Concept)
            RETURN co.code, co.name, co.hotLevel, co.description
            ORDER BY co.hotLevel DESC
        """
        with self.client.session() as session:
            result = session.run(query).data()
            for row in result:
                print(f"  [{row['co.code']}] {row['co.name']:10s} | 热度: {'★'*row['co.hotLevel']}")
        
        print("\n" + "="*70)
    
    def show_dragon_detail(self, stock_code):
        """显示龙头股详情"""
        query = """
            MATCH (c:Company {stockCode: $stockCode})
            OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
            OPTIONAL MATCH (c)-[:BELONGS_TO_CONCEPT]->(co:Concept)
            OPTIONAL MATCH (supplier)-[:SUPPLIES]->(c)
            OPTIONAL MATCH (c)-[:SUPPLIES]->(customer)
            RETURN c, i, collect(DISTINCT co) as concepts, 
                   collect(DISTINCT supplier) as suppliers,
                   collect(DISTINCT customer) as customers
        """
        with self.client.session() as session:
            result = session.run(query, stockCode=stock_code).data()
            if not result:
                print("未找到该股票")
                return
            
            row = result[0]
            c = row['c']
            i = row['i']
            
            print(f"\n📈 {c['stockCode']} {c['stockName']}")
            print("-" * 40)
            print(f"  交易所: {c['market']}")
            print(f"  所属行业: {i['name'] if i else '未知'}")
            print(f"  公司描述: {c['description']}")
            print(f"  是否龙头: {'✅ 是' if c['isLeader'] else '❌ 否'}")
            print(f"  护城河等级: {'⭐'*c['moatLevel']} ({c['moatLevel']})")
            print(f"  护城河类型: {c['moatType']}")
            print(f"  市值: {c['marketCap']} 亿")
            print(f"  PE: {c['peRatio']}")
            print(f"  ROE: {c['roe']}%")
            print(f"  员工数: {c['employees']:,}")
            
            if row['concepts']:
                concepts = [co['name'] for co in row['concepts'] if co]
                print(f"\n  概念板块: {', '.join(concepts)}")
            
            if row['suppliers']:
                suppliers = [f"{s['stockCode']} {s['stockName']}" for s in row['suppliers'] if s]
                print(f"\n  上游供应商: {', '.join(suppliers)}")
            
            if row['customers']:
                customers = [f"{cu['stockCode']} {cu['stockName']}" for cu in row['customers'] if cu]
                print(f"\n  下游客户: {', '.join(customers)}")


def main():
    analyzer = DragonAnalysis()
    
    while True:
        print("\n" + "="*60)
        print("          🐉 龙头战法分析工具 v1.0")
        print("="*60)
        print("1. 查看各行业龙头股")
        print("2. 查看高护城河企业")
        print("3. 查看概念板块股票")
        print("4. 查看股票详情")
        print("5. 龙头战法综合分析")
        print("0. 退出")
        print("-"*60)
        
        choice = input("请输入选择: ")
        
        if choice == "1":
            data = analyzer.get_dragon_stocks_by_industry()
            print("\n🏆 行业龙头股列表")
            print("-"*80)
            print(f"{'代码':<8} {'名称':<12} {'行业':<10} {'市值(亿)':>8} {'ROE%':>6} {'护城河':>6}")
            print("-"*80)
            for row in data:
                moat = '⭐' * row['moatLevel'] if row['moatLevel'] else ''
                print(f"{row['c.stockCode']:<8} {row['c.stockName']:<12} {row['industry']:<10} "
                      f"{row['c.marketCap']:>8} {row['c.roe']:>6} {moat:>6}")
        
        elif choice == "2":
            data = analyzer.get_hightech_moat_companies()
            print("\n🛡️ 高护城河企业")
            print("-"*80)
            print(f"{'代码':<8} {'名称':<12} {'行业':<10} {'护城河':<8} {'护城河类型'}")
            print("-"*80)
            for row in data:
                moat = '⭐' * row['moatLevel'] if row['moatLevel'] else ''
                print(f"{row['c.stockCode']:<8} {row['c.stockName']:<12} {row['industry']:<10} "
                      f"{moat:<8} {row['moatType']}")
        
        elif choice == "3":
            print("\n📊 概念板块列表")
            query = "MATCH (co:Concept) RETURN co.code, co.name ORDER BY co.hotLevel DESC"
            with analyzer.client.session() as session:
                concepts = session.run(query).data()
                for co in concepts:
                    print(f"  [{co['co.code']}] {co['co.name']}")
            
            code = input("\n请输入概念代码(如CON001): ")
            data = analyzer.get_concept_stocks(code)
            if data:
                print(f"\n📈 {data[0]['concept']} 概念成分股")
                print("-"*60)
                for row in data:
                    leader = '🏆' if row['isLeader'] else ''
                    print(f"  {row['c.stockCode']} {row['c.stockName']} {leader}")
        
        elif choice == "4":
            code = input("请输入股票代码: ")
            analyzer.show_dragon_detail(code)
        
        elif choice == "5":
            analyzer.analyze_dragon_strategy()
        
        elif choice == "0":
            break
        
        else:
            print("无效选择，请重新输入")
    
    analyzer.close()


if __name__ == "__main__":
    main()