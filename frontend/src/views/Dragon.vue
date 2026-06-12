<template>
  <div class="dragon-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>🐉 龙头战法分析</h1>
      <p class="subtitle">基于知识图谱的龙头股与供应链分析系统</p>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon><Crown /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ analysis.summary?.total_dragons || 0 }}</div>
            <div class="stat-label">龙头股总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon><Shield /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ analysis.summary?.high_moat_count || 0 }}</div>
            <div class="stat-label">高护城河企业</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #409eff">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ analysis.summary?.active_concepts || 0 }}</div>
            <div class="stat-label">活跃概念板块</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ Object.keys(analysis.industry_distribution || {}).length }}</div>
            <div class="stat-label">覆盖行业</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-select
            v-model="selectedIndustry"
            placeholder="选择行业"
            clearable
            @change="handleIndustryChange"
          >
            <el-option label="全部行业" :value="null" />
            <el-option
              v-for="item in industries"
              :key="item.code"
              :label="item.name"
              :value="item.code"
            />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-select
            v-model="minMoat"
            placeholder="最低护城河等级"
            clearable
            @change="handleMoatChange"
          >
            <el-option label="全部" :value="null" />
            <el-option label="等级 5 (极高)" :value="5" />
            <el-option label="等级 4 (高)" :value="4" />
            <el-option label="等级 3 (中)" :value="3" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索股票代码或名称..."
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>
    </el-card>

    <!-- 龙头股列表 -->
    <el-card class="dragon-list-card">
      <template #header>
        <div class="card-header">
          <span>🏆 龙头股列表</span>
          <el-button type="primary" @click="refreshData">刷新数据</el-button>
        </div>
      </template>
      <el-table :data="filteredDragons" style="width: 100%" @row-click="handleRowClick">
        <el-table-column prop="stock_code" label="代码" width="100" />
        <el-table-column prop="stock_name" label="名称" width="120" />
        <el-table-column prop="industry" label="行业" width="120" />
        <el-table-column label="护城河等级" width="150">
          <template #default="{ row }">
            <el-rate
              v-model="row.moat_level"
              disabled
              show-score
              text-color="#ff9900"
              score-template="{value}级"
            />
          </template>
        </el-table-column>
        <el-table-column prop="moat_type" label="护城河类型" width="200" />
        <el-table-column prop="market_cap" label="市值(亿)" width="100" sortable>
          <template #default="{ row }">
            {{ row.market_cap?.toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="roe" label="ROE(%)" width="80" sortable>
          <template #default="{ row }">
            <span :class="row.roe >= 15 ? 'positive' : 'neutral'">
              {{ row.roe }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="showDetail(row)">详情</el-button>
            <el-button type="success" link @click.stop="showSupplyChain(row)">供应链</el-button>
            <el-button type="warning" link @click.stop="showGraph(row)">图谱</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 热门概念板块 -->
    <el-row :gutter="20" class="concept-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🔥 热门概念板块</span>
          </template>
          <el-table :data="analysis.hot_concepts || []" style="width: 100%">
            <el-table-column prop="code" label="代码" width="100" />
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column label="热度" width="150">
              <template #default="{ row }">
                <el-rate
                  v-model="row.hot_level"
                  disabled
                  show-score
                  text-color="#ff9900"
                  score-template="{value}级"
                />
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🛡️ 高护城河企业 TOP10</span>
          </template>
          <el-table :data="analysis.high_moat_companies || []" style="width: 100%">
            <el-table-column prop="stock_code" label="代码" width="100" />
            <el-table-column prop="stock_name" label="名称" width="120" />
            <el-table-column prop="industry" label="行业" width="100" />
            <el-table-column label="护城河" width="120">
              <template #default="{ row }">
                <el-rate
                  v-model="row.moat_level"
                  disabled
                  show-score
                  text-color="#ff9900"
                  score-template="{value}级"
                />
              </template>
            </el-table-column>
            <el-table-column prop="moat_type" label="类型" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 企业详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="企业详情" width="800px">
      <div v-if="selectedCompany" class="company-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="股票代码">{{ selectedCompany.stock_code }}</el-descriptions-item>
          <el-descriptions-item label="股票名称">{{ selectedCompany.stock_name }}</el-descriptions-item>
          <el-descriptions-item label="所属行业">{{ selectedCompany.industry }}</el-descriptions-item>
          <el-descriptions-item label="是否龙头">
            <el-tag :type="selectedCompany.is_leader ? 'success' : 'info'">
              {{ selectedCompany.is_leader ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="护城河等级">
            <el-rate
              v-model="selectedCompany.moat_level"
              disabled
              show-score
              text-color="#ff9900"
              score-template="{value}级"
            />
          </el-descriptions-item>
          <el-descriptions-item label="护城河类型">{{ selectedCompany.moat_type }}</el-descriptions-item>
          <el-descriptions-item label="市值(亿)">{{ selectedCompany.market_cap?.toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="PE">{{ selectedCompany.pe_ratio }}</el-descriptions-item>
          <el-descriptions-item label="ROE(%)">{{ selectedCompany.roe }}</el-descriptions-item>
          <el-descriptions-item label="员工数">{{ selectedCompany.employees?.toLocaleString() }}</el-descriptions-item>
        </el-descriptions>
        <div class="description">
          <h4>公司描述</h4>
          <p>{{ selectedCompany.description }}</p>
        </div>
        <div class="concepts" v-if="selectedCompany.concepts?.length">
          <h4>所属概念</h4>
          <el-tag
            v-for="concept in selectedCompany.concepts"
            :key="concept.code"
            style="margin-right: 8px; margin-bottom: 8px"
          >
            {{ concept.name }}
          </el-tag>
        </div>
      </div>
    </el-dialog>

    <!-- 供应链对话框 -->
    <el-dialog v-model="supplyChainDialogVisible" title="供应链分析" width="1000px">
      <div v-if="supplyChainData">
        <el-tabs v-model="supplyChainDirection">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="上游" name="up" />
          <el-tab-pane label="下游" name="down" />
        </el-tabs>
        <div class="supply-chain-graph" ref="supplyChainGraph"></div>
      </div>
    </el-dialog>

    <!-- 图谱对话框 -->
    <el-dialog v-model="graphDialogVisible" title="企业关联图谱" width="1000px">
      <div v-if="graphData">
        <div class="graph-controls">
          <el-slider v-model="graphDepth" :min="1" :max="4" @change="loadGraphData" />
          <span>图谱深度: {{ graphDepth }}</span>
        </div>
        <div class="company-graph" ref="companyGraph"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { dragonApi } from '@/api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const searchKeyword = ref('')
const selectedIndustry = ref<string | null>(null)
const minMoat = ref<number | null>(null)
const analysis = ref<any>({})
const dragons = ref<any[]>([])
const industries = ref<any[]>([])
const concepts = ref<any[]>([])

// 对话框
const detailDialogVisible = ref(false)
const supplyChainDialogVisible = ref(false)
const graphDialogVisible = ref(false)
const selectedCompany = ref<any>(null)
const supplyChainData = ref<any>(null)
const supplyChainDirection = ref('all')
const graphData = ref<any>(null)
const graphDepth = ref(2)

// 图表引用
const supplyChainGraph = ref<HTMLElement>()
const companyGraph = ref<HTMLElement>()

onMounted(async () => {
  await loadAnalysis()
  await loadDragons()
  await loadConcepts()
})

const loadAnalysis = async () => {
  try {
    const res: any = await dragonApi.getDragonAnalysis()
    if (res.success) {
      analysis.value = res.data
    }
  } catch (e) {
    console.error('Failed to load analysis:', e)
    ElMessage.error('加载分析数据失败')
  }
}

const loadDragons = async () => {
  try {
    const res: any = await dragonApi.getDragonStocks(selectedIndustry.value || undefined)
    if (res.success) {
      dragons.value = res.data || []
    }
  } catch (e) {
    console.error('Failed to load dragons:', e)
    ElMessage.error('加载龙头股数据失败')
  }
}

const loadConcepts = async () => {
  try {
    const res: any = await dragonApi.getAllConcepts()
    if (res.success) {
      concepts.value = res.data || []
    }
  } catch (e) {
    console.error('Failed to load concepts:', e)
  }
}

const filteredDragons = computed(() => {
  let result = dragons.value

  if (minMoat.value !== null) {
    result = result.filter(item => item.moat_level >= minMoat.value!)
  }

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.stock_code.toLowerCase().includes(keyword) ||
      item.stock_name.toLowerCase().includes(keyword)
    )
  }

  return result
})

const handleIndustryChange = async () => {
  await loadDragons()
}

const handleMoatChange = () => {
  // filteredDragons 会自动更新
}

const handleSearch = () => {
  // filteredDragons 会自动更新
}

const refreshData = async () => {
  await Promise.all([loadAnalysis(), loadDragons()])
  ElMessage.success('数据刷新成功')
}

const handleRowClick = (row: any) => {
  showDetail(row)
}

const showDetail = async (company: any) => {
  try {
    const res: any = await dragonApi.getCompanyDetail(company.stock_code)
    if (res.success) {
      selectedCompany.value = res.data
      detailDialogVisible.value = true
    }
  } catch (e) {
    console.error('Failed to load company detail:', e)
    ElMessage.error('加载企业详情失败')
  }
}

const showSupplyChain = async (company: any) => {
  try {
    const res: any = await dragonApi.getSupplyChain(company.stock_code, 'all')
    if (res.success) {
      supplyChainData.value = res.data
      supplyChainDialogVisible.value = true
      await nextTick()
      renderSupplyChainGraph()
    }
  } catch (e) {
    console.error('Failed to load supply chain:', e)
    ElMessage.error('加载供应链数据失败')
  }
}

const showGraph = async (company: any) => {
  try {
    const res: any = await dragonApi.getCompanyGraph(company.stock_code, graphDepth.value)
    if (res.success) {
      graphData.value = res.data
      graphDialogVisible.value = true
      await nextTick()
      renderCompanyGraph()
    }
  } catch (e) {
    console.error('Failed to load graph:', e)
    ElMessage.error('加载图谱数据失败')
  }
}

const loadGraphData = async () => {
  if (selectedCompany.value) {
    const res: any = await dragonApi.getCompanyGraph(
      selectedCompany.value.stock_code,
      graphDepth.value
    )
    if (res.success) {
      graphData.value = res.data
      await nextTick()
      renderCompanyGraph()
    }
  }
}

const renderSupplyChainGraph = () => {
  if (!supplyChainGraph.value || !supplyChainData.value) return

  const chart = echarts.init(supplyChainGraph.value)
  const nodes = supplyChainData.value.nodes.map((node: any) => ({
    id: node.id,
    name: node.data.stockName || node.data.name,
    symbolSize: 60,
    category: node.labels[0],
  }))

  const links = supplyChainData.value.edges.map((edge: any) => ({
    source: edge.source,
    target: edge.target,
    label: { show: true, formatter: edge.type },
  }))

  const option = {
    tooltip: {},
    legend: {
      data: ['Company', 'Industry', 'Concept'],
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: links,
        categories: [{ name: 'Company' }, { name: 'Industry' }, { name: 'Concept' }],
        roam: true,
        label: { show: true, position: 'right' },
        force: { repulsion: 1000, edgeLength: 100 },
      },
    ],
  }

  chart.setOption(option)
}

const renderCompanyGraph = () => {
  if (!companyGraph.value || !graphData.value) return

  const chart = echarts.init(companyGraph.value)
  const nodes = graphData.value.nodes.map((node: any) => ({
    id: node.id,
    name: node.data.stockName || node.data.name || node.data.code,
    symbolSize: 50,
    category: node.labels[0],
  }))

  const links = graphData.value.edges.map((edge: any) => ({
    source: edge.source,
    target: edge.target,
    label: { show: true, formatter: edge.type },
  }))

  const option = {
    tooltip: {},
    legend: {
      data: ['Company', 'Industry', 'Concept', 'MarketEvent'],
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: links,
        categories: [
          { name: 'Company' },
          { name: 'Industry' },
          { name: 'Concept' },
          { name: 'MarketEvent' },
        ],
        roam: true,
        label: { show: true, position: 'right' },
        force: { repulsion: 800, edgeLength: 80 },
      },
    ],
  }

  chart.setOption(option)
}
</script>

<style scoped>
.dragon-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 32px;
  margin-bottom: 8px;
}

.subtitle {
  color: #909399;
  font-size: 16px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
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

.filter-card {
  margin-bottom: 20px;
}

.dragon-list-card {
  margin-bottom: 20px;
}

.concept-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.company-detail {
  padding: 10px 0;
}

.description {
  margin-top: 20px;
}

.description h4 {
  margin-bottom: 10px;
}

.concepts {
  margin-top: 20px;
}

.concepts h4 {
  margin-bottom: 10px;
}

.supply-chain-graph,
.company-graph {
  height: 600px;
  margin-top: 20px;
}

.graph-controls {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.positive {
  color: #f56c6c;
  font-weight: bold;
}

.neutral {
  color: #909399;
}
</style>