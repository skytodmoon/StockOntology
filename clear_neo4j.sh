#!/bin/bash

# 清理Neo4j数据库中的旧数据和约束

echo "正在清理Neo4j数据库..."

# 删除旧的约束和索引
ssh root@172.16.252.109 << 'EOF'
    # 进入neo4j的cypher shell
    cypher-shell -u neo4j -p 12345678 "DROP CONSTRAINT company_code IF EXISTS;"
    cypher-shell -u neo4j -p 12345678 "DROP CONSTRAINT industry_code IF EXISTS;"
    cypher-shell -u neo4j -p 12345678 "DROP CONSTRAINT stock_code IF EXISTS;"
    cypher-shell -u neo4j -p 12345678 "DROP CONSTRAINT investor_id IF EXISTS;"
    cypher-shell -u neo4j -p 12345678 "DROP CONSTRAINT event_id IF EXISTS;"
    
    # 删除所有数据
    cypher-shell -u neo4j -p 12345678 "MATCH (n) DETACH DELETE n;"
    
    echo "数据库已清理完成"
EOF

echo "清理完成"
