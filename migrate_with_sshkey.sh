#!/bin/bash

# Docker 镜像迁移脚本 - SSH密钥认证版
# 1. 生成SSH密钥（如果没有）
# 2. 复制公钥到远程服务器
# 3. 使用scp传输镜像

REMOTE_HOST="172.16.252.109"
REMOTE_USER="root"
REMOTE_PASS="stvy~J66eumjdrN"
REMOTE_DIR="/tmp/docker_images"
LOCAL_DIR="/tmp/docker_images"

echo "=== Docker 镜像迁移工具 ==="
echo "远程服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo ""

# 创建本地目录
mkdir -p "$LOCAL_DIR"

# 检查SSH密钥
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "生成SSH密钥..."
    ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa -q
fi

# 使用expect复制公钥
echo "配置SSH密钥认证..."
expect << EOF
set timeout 30

spawn ssh-copy-id -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST}

expect {
    "password:" {
        send "$REMOTE_PASS\r"
        exp_continue
    }
    "Number of key(s) added:" {
        puts "SSH密钥配置成功"
    }
    "already exists" {
        puts "SSH密钥已配置"
    }
    eof {
        puts "SSH密钥配置完成"
    }
}
EOF

echo ""
echo "SSH密钥配置完成！现在开始迁移镜像..."
echo ""

# 镜像列表
IMAGES=(
    "neo4j:latest"
    "postgres:15-alpine"
    "redis:6-alpine"
    "timescale/timescaledb:latest-pg15"
    "milvusdb/milvus:v2.5.10"
)

for image in "${IMAGES[@]}"; do
    echo "迁移镜像: $image"
    image_name=$(echo $image | tr '/:' '_')
    tar_file="${image_name}.tar"
    
    # 在远程保存镜像
    echo "  - 保存镜像..."
    ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR} && docker save -o ${REMOTE_DIR}/${tar_file} $image"
    
    if [ $? -eq 0 ]; then
        # 传输到本地
        echo "  - 传输镜像..."
        scp -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${tar_file} ${LOCAL_DIR}/
        
        if [ $? -eq 0 ]; then
            # 加载镜像
            echo "  - 加载镜像..."
            docker load -i "${LOCAL_DIR}/${tar_file}"
            rm -f "${LOCAL_DIR}/${tar_file}"
            echo -e "  \033[32m✓ 成功: $image\033[0m"
        else
            echo -e "  \033[31m✗ 传输失败\033[0m"
        fi
    else
        echo -e "  \033[31m✗ 保存失败\033[0m"
    fi
    echo ""
done

# 清理远程文件
echo "清理临时文件..."
ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "rm -rf ${REMOTE_DIR}"

echo ""
echo "=== 迁移完成 ==="
echo ""
echo "本地镜像列表:"
docker images | grep -E "(neo4j|postgres|redis|timescale|milvus|REPOSITORY)"