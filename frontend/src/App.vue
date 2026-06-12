<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-left">
        <h1 class="logo">StockOntology</h1>
        <span class="subtitle">股票分析预测系统</span>
      </div>
      <div class="header-right">
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          :router="true"
          class="header-menu"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/graph">知识图谱</el-menu-item>
          <el-menu-item index="/analysis">智能分析</el-menu-item>
          <el-menu-item index="/prediction">预测模型</el-menu-item>
          <el-menu-item index="/events">事件监控</el-menu-item>
          <el-menu-item index="/data">数据管理</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.app-container {
  min-height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  background: linear-gradient(45deg, #00d2ff, #3a7bd5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 14px;
  color: #a0aec0;
}

.header-menu {
  background: transparent;
  border: none;
}

.header-menu .el-menu-item {
  color: #a0aec0 !important;
  border-bottom: none !important;
}

.header-menu .el-menu-item:hover,
.header-menu .el-menu-item.is-active {
  color: #00d2ff !important;
  background: rgba(0, 210, 255, 0.1) !important;
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
