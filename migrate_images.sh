#!/bin/bash

# Docker 镜像迁移脚本 - 简化版
# 使用 expect 自动处理密码并直接通过管道传输

REMOTE_HOST="172.16.252.109"
REMOTE_USER="root"
REMOTE_PASS="stvy~J66eumjdrN"

# 需要迁移的镜像列表
IMAGES=(
    "neo4j:latest"
    "postgres:15-alpine"
    "redis:6-alpine"
    "timescale/timescaledb:latest-pg15"
    "milvusdb/milvus:v2.5.10"
)

echo "=== Docker 镜像迁移工具 ==="
echo "远程服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo ""

# 创建 expect 脚本
cat > /tmp/docker_migrate.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 600
set remote_host [lindex $argv 0]
set remote_user [lindex $argv 1]
set remote_pass [lindex $argv 2]
set image [lindex $argv 3]

spawn ssh -o StrictHostKeyChecking=no ${remote_user}@${remote_host} "docker save $image"
expect {
    "password:" {
        send "$remote_pass\r"
        exp_continue
    }
    eof {
        exit 0
    }
}
EOF

chmod +x /tmp/docker_migrate.exp

for image in "${IMAGES[@]}"; do
    echo "正在迁移: $image"
    echo "----------------------------------------"
    
    # 使用 expect 脚本获取镜像数据并直接加载
    /tmp/docker_migrate.exp "$REMOTE_HOST" "$REMOTE_USER" "$REMOTE_PASS" "$image" | docker load
    
    if [ $? -eq 0 ]; then
        echo -e "\033[32m✓ 成功迁移: $image\033[0m"
    else
        echo -e "\033[31m✗ 迁移失败: $image\033[0m"
    fi
    echo ""
done

# 清理临时文件
rm -f /tmp/docker_migrate.exp

echo "=== 迁移完成 ==="
echo ""
echo "本地已迁移的镜像:"
docker images | grep -E "(neo4j|postgres|redis|timescale|milvus)"