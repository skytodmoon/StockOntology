<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #409eff">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.companies || 0 }}</div>
            <div class="stat-label">上市公司</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.industries || 0 }}</div>
            <div class="stat-label">行业分类</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.investors || 0 }}</div>
            <div class="stat-label">机构投资者</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.events || 0 }}</div>
            <div class="stat-label">市场事件</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索股票代码或名称..."
        size="large"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button @click="handleSearch">搜索</el-button>
        </template>
      </el-input>
    </el-card>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>行业分布</span>
          </template>
          <div ref="industryChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>市场概览</span>
          </template>
          <div class="market-overview">
            <div v-for="item in marketData" :key="item.name" class="market-item">
              <span class="market-name">{{ item.name }}</span>
              <span :class="['market-value', item.change >= 0 ? 'up' : 'down']">
                {{ item.value }}
                <span class="change">({{ item.change >= 0 ? '+' : '' }}{{ item.change }}%)</span>
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最新事件 -->
    <el-card class="events-card">
      <template #header>
        <div class="card-header">
          <span>最新市场事件</span>
          <el-button type="primary" link>查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentEvents" style="width: 100%">
        <el-table-column prop="eventDate" label="日期" width="120" />
        <el-table-column prop="title" label="事件标题" />
        <el-table-column prop="eventType" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEventTypeTag(row.eventType)">
              {{ row.eventType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="impactLevel" label="影响" width="100">
          <template #default="{ row }">
            <el-tag :type="getImpactTag(row.impactLevel)">
              {{ row.impactLevel }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { graphApi, eventApi } from '@/api'
import * as echarts from 'echarts'

const router = useRouter()
const searchKeyword = ref('')
const stats = ref<any>({})
const marketData = ref<any[]>([])
const recentEvents = ref<any[]>([])
const industryChart = ref<HTMLElement>()

onMounted(async () => {
  await loadStats()
  await loadRecentEvents()
  initChart()
})

const loadStats = async () => {
  try {
    const res: any = await graphApi.getStats()
    if (res.success) {
      const data = res.data
      stats.value = {
        companies: data.node_counts?.Company || 0,
        industries: data.node_counts?.Industry || 0,
        investors: data.node_counts?.Investor || 0,
        events: data.node_counts?.MarketEvent || 0,
      }
    }
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

const loadRecentEvents = async () => {
  try {
    const res: any = await eventApi.getRecent(7)
    if (res.success) {
      recentEvents.value = res.data || []
    }
  } catch (e) {
    console.error('Failed to load events:', e)
  }
}

const initChart = () => {
  if (!industryChart.value) return

  const chart = echarts.init(industryChart.value)
  const option = {
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '行业分布',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 1048, name: '信息技术' },
          { value: 735, name: '金融' },
          { value: 580, name: '消费' },
          { value: 484, name: '医药' },
          { value: 300, name: '新能源' },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }
  chart.setOption(option)

  window.addEventListener('resize', () => chart.resize())
}

const handleSearch = () => {
  if (searchKeyword.value) {
    router.push(`/company/${searchKeyword.value}`)
  }
}

const getEventTypeTag = (type: string) => {
  const map: Record<string, string> = {
    PolicyEvent: 'warning',
    CompanyEvent: '',
    MacroEvent: 'danger',
  }
  return map[type] || 'info'
}

const getImpactTag = (level: string) => {
  const map: Record<string, string> = {
    High: 'danger',
    Medium: 'warning',
    Low: 'info',
  }
  return map[level] || 'info'
}
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.search-card {
  margin-bottom: 20px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
}

.market-overview {
  padding: 10px 0;
}

.market-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.market-item:last-child {
  border-bottom: none;
}

.market-name {
  font-size: 14px;
  color: #606266;
}

.market-value {
  font-weight: bold;
}

.market-value.up {
  color: #f56c6c;
}

.market-value.down {
  color: #67c23a;
}

.change {
  font-size: 12px;
  margin-left: 8px;
}

.events-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
