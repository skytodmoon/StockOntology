<template>
  <div class="graph-view">
    <!-- 搜索和控制栏 -->
    <el-card class="control-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索公司..."
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="selectedCompany" placeholder="选择公司" filterable>
            <el-option
              v-for="item in companies"
              :key="item.stockCode"
              :label="`${item.stockName} (${item.stockCode})`"
              :value="item.stockCode"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-slider v-model="depth" :min="1" :max="4" :step="1" show-stops />
          <span class="depth-label">关系深度: {{ depth }}</span>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadGraph" :loading="loading">
            加载图谱
          </el-button>
        </el-col>
        <el-col :span="4">
          <el-button @click="resetGraph">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图谱容器 -->
    <el-card class="graph-card">
      <div ref="graphContainer" class="graph-container"></div>
    </el-card>

    <!-- 节点详情 -->
    <el-drawer v-model="showDrawer" title="节点详情" size="400px">
      <div v-if="selectedNode" class="node-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="类型">
            <el-tag>{{ selectedNode.labels?.[0] || 'Unknown' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item
            v-for="(value, key) in selectedNode"
            :key="key"
            :label="key"
          >
            {{ value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { graphApi } from '@/api'
import * as echarts from 'echarts'

const searchKeyword = ref('')
const selectedCompany = ref('')
const companies = ref<any[]>([])
const depth = ref(2)
const loading = ref(false)
const showDrawer = ref(false)
const selectedNode = ref<any>(null)
const graphContainer = ref<HTMLElement>()

let chart: echarts.ECharts | null = null

onMounted(() => {
  initChart()
  loadCompanies()
})

onUnmounted(() => {
  chart?.dispose()
})

const initChart = () => {
  if (!graphContainer.value) return

  chart = echarts.init(graphContainer.value)

  chart.on('click', (params: any) => {
    if (params.dataType === 'node') {
      selectedNode.value = params.data
      showDrawer.value = true
    }
  })

  window.addEventListener('resize', () => chart?.resize())
}

const loadCompanies = async () => {
  try {
    const res: any = await graphApi.executeQuery(
      'MATCH (c:Company) RETURN c.stockCode as code, c.stockName as name LIMIT 100'
    )
    if (res.success) {
      companies.value = res.data.map((item: any) => ({
        stockCode: item.code,
        stockName: item.name,
      }))
    }
  } catch (e) {
    console.error('Failed to load companies:', e)
  }
}

const loadGraph = async () => {
  if (!selectedCompany.value) return

  loading.value = true
  try {
    const res: any = await graphApi.getCompanyGraph(selectedCompany.value, depth.value)
    if (res.success) {
      renderGraph(res.data)
    }
  } catch (e) {
    console.error('Failed to load graph:', e)
  } finally {
    loading.value = false
  }
}

const renderGraph = (data: any) => {
  if (!chart) return

  const { nodes, edges } = data

  // 节点类型颜色映射
  const colorMap: Record<string, string> = {
    Company: '#409eff',
    Industry: '#67c23a',
    FinancialReport: '#e6a23c',
    MarketEvent: '#f56c6c',
    Investor: '#909399',
  }

  // 处理节点
  const graphNodes = nodes.map((node: any) => ({
    id: node.id,
    name: node.stockName || node.name || node.title || node.id,
    symbolSize: node.labels?.[0] === 'Company' ? 40 : 30,
    category: node.labels?.[0] || 'Unknown',
    itemStyle: {
      color: colorMap[node.labels?.[0]] || '#909399',
    },
    ...node,
  }))

  // 处理边
  const graphEdges = edges.map((edge: any) => ({
    source: edge.source,
    target: edge.target,
    lineStyle: {
      color: '#c0c4cc',
      curveness: 0.3,
    },
  }))

  // 类别
  const categories = Object.keys(colorMap).map((name) => ({
    name,
    itemStyle: { color: colorMap[name] },
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          return `<b>${params.name}</b><br/>类型: ${params.data.labels?.[0] || 'Unknown'}`
        }
        return params.data.type || ''
      },
    },
    legend: {
      data: categories.map((c) => c.name),
      top: 10,
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
          gravity: 0.1,
          edgeLength: 150,
        },
        label: {
          show: true,
          position: 'right',
          fontSize: 12,
        },
        lineStyle: {
          opacity: 0.9,
          width: 2,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 5,
          },
        },
      },
    ],
  }

  chart.setOption(option, true)
}

const handleSearch = async () => {
  if (!searchKeyword.value) return

  try {
    const res: any = await graphApi.searchCompanies(searchKeyword.value)
    if (res.success && res.data.length > 0) {
      selectedCompany.value = res.data[0].stockCode
      loadGraph()
    }
  } catch (e) {
    console.error('Search failed:', e)
  }
}

const resetGraph = () => {
  chart?.clear()
  selectedCompany.value = ''
}
</script>

<style scoped>
.graph-view {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-card {
  flex-shrink: 0;
}

.depth-label {
  font-size: 12px;
  color: #909399;
  text-align: center;
  display: block;
  margin-top: 4px;
}

.graph-card {
  flex: 1;
}

.graph-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}

.graph-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.node-detail {
  padding: 16px;
}
</style>
