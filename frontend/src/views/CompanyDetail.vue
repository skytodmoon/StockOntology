<template>
  <div class="company-detail" v-loading="loading">
    <!-- 公司信息卡片 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>{{ company.stockName }} ({{ company.stockCode }})</span>
          <el-tag>{{ company.market }}</el-tag>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="info-item">
            <span class="label">所属行业</span>
            <span class="value">{{ company.industry || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="label">市值</span>
            <span class="value">{{ formatMarketCap(company.marketCap) }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="label">上市日期</span>
            <span class="value">{{ company.listDate || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="info-item">
            <span class="label">总股本</span>
            <span class="value">{{ formatNumber(company.totalShare) }}</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 关系图谱和财务数据 -->
    <el-row :gutter="20" class="content-row">
      <!-- 关系图谱 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>关系图谱</span>
          </template>
          <div ref="graphChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 右侧面板 -->
      <el-col :span="8">
        <!-- 竞争对手 -->
        <el-card class="competitors-card">
          <template #header>
            <span>竞争对手</span>
          </template>
          <div v-if="competitors.length" class="competitor-list">
            <div
              v-for="item in competitors"
              :key="item.stockCode"
              class="competitor-item"
              @click="goToCompany(item.stockCode)"
            >
              <span class="name">{{ item.stockName }}</span>
              <span class="code">{{ item.stockCode }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>

        <!-- 机构投资者 -->
        <el-card class="investors-card">
          <template #header>
            <span>机构投资者</span>
          </template>
          <div v-if="investors.length" class="investor-list">
            <div v-for="item in investors" :key="item.investorId" class="investor-item">
              <span class="name">{{ item.name }}</span>
              <span class="type">{{ item.investorType }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 财务数据 -->
    <el-card class="financial-card">
      <template #header>
        <span>财务数据</span>
      </template>
      <el-table :data="financialReports" style="width: 100%">
        <el-table-column prop="reportDate" label="报告日期" width="120" />
        <el-table-column prop="reportType" label="类型" width="80" />
        <el-table-column prop="revenue" label="营业收入" width="150">
          <template #default="{ row }">
            {{ formatLargeNumber(row.revenue) }}
          </template>
        </el-table-column>
        <el-table-column prop="netProfit" label="净利润" width="150">
          <template #default="{ row }">
            {{ formatLargeNumber(row.netProfit) }}
          </template>
        </el-table-column>
        <el-table-column prop="eps" label="每股收益" width="100" />
        <el-table-column prop="roe" label="ROE" width="100">
          <template #default="{ row }">
            {{ row.roe ? (row.roe * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="peRatio" label="市盈率" width="100" />
        <el-table-column prop="pbRatio" label="市净率" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { graphApi, financialApi } from '@/api'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const company = ref<any>({})
const competitors = ref<any[]>([])
const investors = ref<any[]>([])
const financialReports = ref<any[]>([])
const graphChart = ref<HTMLElement>()

let chart: echarts.ECharts | null = null

onMounted(() => {
  initChart()
  loadCompanyData()
})

watch(() => route.params.code, () => {
  loadCompanyData()
})

const initChart = () => {
  if (!graphChart.value) return
  chart = echarts.init(graphChart.value)
  window.addEventListener('resize', () => chart?.resize())
}

const loadCompanyData = async () => {
  const code = route.params.code as string
  if (!code) return

  loading.value = true
  try {
    // 并行加载数据
    const [companyRes, competitorsRes, investorsRes, reportsRes] = await Promise.all([
      graphApi.getCompanyDetails(code),
      graphApi.getCompanyCompetitors(code),
      graphApi.getCompanyInvestors(code),
      financialApi.getReports(code),
    ])

    if (companyRes.success) {
      company.value = companyRes.data
    }

    if (competitorsRes.success) {
      competitors.value = competitorsRes.data || []
    }

    if (investorsRes.success) {
      investors.value = investorsRes.data || []
    }

    if (reportsRes.success) {
      financialReports.value = reportsRes.data || []
    }

    // 加载图谱
    loadGraph(code)
  } catch (e) {
    console.error('Failed to load company data:', e)
  } finally {
    loading.value = false
  }
}

const loadGraph = async (code: string) => {
  try {
    const res: any = await graphApi.getCompanyGraph(code, 2)
    if (res.success) {
      renderGraph(res.data)
    }
  } catch (e) {
    console.error('Failed to load graph:', e)
  }
}

const renderGraph = (data: any) => {
  if (!chart) return

  const { nodes, edges } = data

  const colorMap: Record<string, string> = {
    Company: '#409eff',
    Industry: '#67c23a',
    Investor: '#e6a23c',
    MarketEvent: '#f56c6c',
  }

  const graphNodes = nodes.map((node: any) => ({
    id: node.id,
    name: node.stockName || node.name || node.title || node.id,
    symbolSize: node.stockCode === company.value.stockCode ? 50 : 30,
    category: node.labels?.[0] || 'Unknown',
    itemStyle: {
      color: colorMap[node.labels?.[0]] || '#909399',
    },
    ...node,
  }))

  const graphEdges = edges.map((edge: any) => ({
    source: edge.source,
    target: edge.target,
  }))

  const categories = Object.keys(colorMap).map((name) => ({
    name,
    itemStyle: { color: colorMap[name] },
  }))

  const option = {
    tooltip: {},
    legend: {
      data: categories.map((c) => c.name),
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: graphNodes,
        links: graphEdges,
        categories: categories,
        roam: true,
        draggable: true,
        force: {
          repulsion: 200,
          edgeLength: 150,
        },
        label: {
          show: true,
          position: 'right',
        },
        emphasis: {
          focus: 'adjacency',
        },
      },
    ],
  }

  chart.setOption(option, true)
}

const goToCompany = (code: string) => {
  router.push(`/company/${code}`)
}

const formatMarketCap = (value: number) => {
  if (!value) return '-'
  if (value >= 1e12) return (value / 1e12).toFixed(2) + '万亿'
  if (value >= 1e8) return (value / 1e8).toFixed(2) + '亿'
  return value.toLocaleString()
}

const formatNumber = (value: number) => {
  if (!value) return '-'
  return value.toLocaleString()
}

const formatLargeNumber = (value: number) => {
  if (!value) return '-'
  if (Math.abs(value) >= 1e8) return (value / 1e8).toFixed(2) + '亿'
  if (Math.abs(value) >= 1e4) return (value / 1e4).toFixed(2) + '万'
  return value.toLocaleString()
}
</script>

<style scoped>
.company-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: #909399;
}

.info-item .value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.content-row {
  margin-top: 16px;
}

.chart-container {
  height: 400px;
}

.competitors-card,
.investors-card {
  margin-bottom: 16px;
}

.competitor-list,
.investor-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.competitor-item,
.investor-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.competitor-item:hover {
  background: #f5f7fa;
}

.competitor-item .name,
.investor-item .name {
  font-weight: 500;
}

.competitor-item .code,
.investor-item .type {
  font-size: 12px;
  color: #909399;
}
</style>
