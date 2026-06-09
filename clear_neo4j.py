#!/usr/bin/env python3
"""
清理Neo4j数据库中的所有数据
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_neo4j_client

def clear_database():
    """清空数据库"""
    client = get_neo4j_client()
    
    print("正在清理数据库...")
    
    # 删除所有节点和关系
    with client.get_session() as session:
        # 删除所有数据
        session.run("MATCH (n) DETACH DELETE n")
        print("✓ 所有数据已删除")
        
        # 删除所有约束
        try:
            session.run("DROP CONSTRAINT company_code IF EXISTS")
            print("✓ 删除约束 company_code")
        except:
            pass
            
        try:
            session.run("DROP CONSTRAINT industry_code IF EXISTS")
            print("✓ 删除约束 industry_code")
        except:
            pass
            
        try:
            session.run("DROP CONSTRAINT stock_code IF EXISTS")
            print("✓ 删除约束 stock_code")
        except:
            pass
            
        try:
            session.run("DROP CONSTRAINT investor_id IF EXISTS")
            print("✓ 删除约束 investor_id")
        except:
            pass
            
        try:
            session.run("DROP CONSTRAINT event_id IF EXISTS")
            print("✓ 删除约束 event_id")
        except:
            pass
    
    client.close()
    print("\n✅ 数据库清理完成")

if __name__ == "__main__":
    clear_database()
