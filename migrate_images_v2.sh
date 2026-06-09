#!/bin/bash

# Docker 镜像迁移脚本 - 方法2
# 1. 在远程保存镜像
# 2. 使用scp传输
# 3. 在本地加载

REMOTE_HOST="172.16.252.109"
REMOTE_USER="root"
REMOTE_PASS="stvy~J66eumjdrN"
REMOTE_DIR="/tmp/docker_images"
LOCAL_DIR="/tmp/docker_images"

echo "=== Docker 镜像迁移工具 ==="
echo "远程服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo ""

# 创建expect脚本来执行远程命令
expect << EOF
set timeout 600

spawn ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST}

expect {
    "password:" {
        send "$REMOTE_PASS\r"
    }
}

expect "~$ "
send "mkdir -p $REMOTE_DIR\r"

expect "~$ "
send "exit\r"
expect eof
EOF

echo ""
echo "正在保存并传输镜像..."
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
    echo "处理镜像: $image"
    image_name=$(echo $image | tr '/:' '_')
    tar_file="${image_name}.tar"
    
    # 创建expect脚本来执行远程命令
    expect << EOF2
set timeout 600

spawn ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "docker save -o ${REMOTE_DIR}/${tar_file} $image"

expect {
    "password:" {
        send "$REMOTE_PASS\r"
    }
}

expect eof
EOF2
    
    if [ $? -eq 0 ]; then
        echo "下载镜像: $image"
        # 使用expect下载
        expect << EOF3
set timeout 600

spawn scp -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${tar_file} ${LOCAL_DIR}/

expect {
    "password:" {
        send "$REMOTE_PASS\r"
    }
}

expect eof
EOF3
        
        if [ $? -eq 0 ]; then
            echo "加载镜像: $image"
            docker load -i "${LOCAL_DIR}/${tar_file}"
            #rm -f "${LOCAL_DIR}/${tar_file}"
            echo -e "\033[32m✓ 完成: $image\033[0m"
        else
            echo -e "\033[31m✗ 下载失败: $image\033[0m"
        fi
    else
        echo -e "\033[31m✗ 保存失败: $image\033[0m"
    fi
    echo ""
done

echo "=== 清理远程文件 ==="
expect << EOF4
set timeout 60

spawn ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "rm -rf ${REMOTE_DIR}"

expect {
    "password:" {
        send "$REMOTE_PASS\r"
    }
}

expect eof
EOF4

echo ""
echo "=== 迁移完成 ==="
docker images | grep -E "(neo4j|postgres|redis|timescale|milvus)"