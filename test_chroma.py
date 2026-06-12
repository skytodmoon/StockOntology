#!/usr/bin/env python3
"""
ChromaDB 测试脚本

测试 ChromaDB 的连接和基本功能。
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import get_chroma_client, init_chroma_collection


def test_chroma_connection():
    """测试 ChromaDB 连接"""
    print("=" * 60)
    print("ChromaDB 连接测试")
    print("=" * 60)

    try:
        # 获取客户端
        print("\n1️⃣ 连接 ChromaDB...")
        client = get_chroma_client()
        print("✓ ChromaDB 连接成功")

        # 获取统计信息
        print("\n2️⃣ 获取统计信息...")
        stats = client.get_stats()
        print(f"✓ 模式: {stats.get('mode', 'unknown')}")
        print(f"✓ 集合数量: {stats.get('collection_count', 0)}")
        print(f"✓ 持久化目录: {stats.get('persist_directory', 'N/A')}")

        # 创建测试集合
        print("\n3️⃣ 创建测试集合...")
        collection = client.get_collection("test_collection", create_if_not_exists=True)
        print(f"✓ 集合 'test_collection' 创建成功")

        # 添加测试文档
        print("\n4️⃣ 添加测试文档...")
        test_docs = [
            "贵州茅台是中国白酒龙头企业",
            "五粮液是浓香型白酒代表",
            "宁德时代是动力电池领先企业",
        ]
        test_ids = ["doc1", "doc2", "doc3"]
        test_metadata = [
            {"stock_code": "600519", "type": "company"},
            {"stock_code": "000858", "type": "company"},
            {"stock_code": "300750", "type": "company"},
        ]

        success = client.add_documents(
            "test_collection",
            documents=test_docs,
            ids=test_ids,
            metadatas=test_metadata,
        )
        if success:
            print(f"✓ 成功添加 {len(test_docs)} 个文档")

        # 查询文档
        print("\n5️⃣ 查询相似文档...")
        query_text = "白酒行业龙头"
        results = client.query(
            "test_collection",
            query_texts=[query_text],
            n_results=2,
        )
        print(f"✓ 查询: '{query_text}'")
        print(f"✓ 返回 {len(results['ids'][0])} 个结果:")
        for i, (id, doc, dist) in enumerate(
            zip(results["ids"][0], results["documents"][0], results["distances"][0])
        ):
            print(f"   [{i+1}] ID: {id}, 距离: {dist:.4f}")
            print(f"       内容: {doc[:50]}...")

        # 统计文档数量
        print("\n6️⃣ 统计文档数量...")
        count = client.count_documents("test_collection")
        print(f"✓ 文档数量: {count}")

        # 删除测试集合
        print("\n7️⃣ 清理测试数据...")
        client.delete_collection("test_collection")
        print("✓ 测试集合已删除")

        # 创建默认集合
        print("\n8️⃣ 创建默认集合 'stock_docs'...")
        default_collection = init_chroma_collection("stock_docs")
        print(f"✓ 默认集合创建成功")

        print("\n" + "=" * 60)
        print("✅ ChromaDB 测试完成！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_chroma_connection()
    sys.exit(0 if success else 1)