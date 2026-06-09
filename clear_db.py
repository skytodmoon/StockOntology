#!/usr/bin/env python3
"""
清理Neo4j数据库脚本
"""

import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def clear_database():
    """清空数据库"""
    print(f"🔌 连接到 Neo4j: {NEO4J_URI}")
    
    client = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with client.session() as session:
            print("🗑️ 删除所有节点和关系...")
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ 数据已删除")
            
            print("🗑️ 删除所有约束...")
            constraints = ["company_code", "industry_code", "investor_id", "event_id"]
            for constraint in constraints:
                try:
                    session.run(f"DROP CONSTRAINT {constraint} IF EXISTS")
                    print(f"✓ 删除约束: {constraint}")
                except:
                    pass
        
        print("\n✅ 数据库清理完成")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    clear_database()
