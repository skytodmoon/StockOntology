<template>
  <div class="prediction-page">
    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <el-tab-pane label="个股预测" name="single">
        <el-row :gutter="20">
          <!-- 左侧：预测控制 + 图表 -->
          <el-col :span="16">
            <!-- 股票选择 -->
            <el-card class="control-card">
          <el-form :inline="true">
            <el-form-item label="股票代码">
              <el-input
                v-model="stockCode"
                placeholder="输入股票代码，如 600519"
                style="width: 200px"
                @keyup.enter="loadAllData"
              />
            </el-form-item>
            <el-form-item label="预测天数">
              <el-input-number v-model="days" :min="1" :max="30" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadAllData" :loading="loading">
                <el-icon><TrendCharts /></el-icon>
                本体增强预测
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- K 线图 -->
        <el-card v-if="priceData.length > 0" style="margin-top: 16px">
          <KLineChart
            :stockCode="stockCode"
            :stockName="stockName"
            :data="priceData"
            :predictions="predictions"
            :height="450"
          />
        </el-card>

        <!-- 趋势分析 -->
        <el-card v-if="trendData" style="margin-top: 16px">
          <template #header>
            <span>趋势分析</span>
          </template>
          <div class="trend-card">
            <div class="trend-indicator" :class="trendClass">
              <span class="icon">{{ trendIcon }}</span>
              <span class="text">{{ trendText }}</span>
            </div>
            <div class="trend-details">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="MA5">{{ trendData.indicators?.ma5 }}</el-descriptions-item>
                <el-descriptions-item label="MA10">{{ trendData.indicators?.ma10 }}</el-descriptions-item>
                <el-descriptions-item label="RSI">{{ trendData.indicators?.rsi }}</el-descriptions-item>
                <el-descriptions-item label="置信度">
                  {{ ((trendData.confidence || 0) * 100).toFixed(0) }}%
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>

        <!-- 风险评估 -->
        <el-card v-if="riskData" style="margin-top: 16px">
          <template #header>
            <span>风险评估</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="8" style="text-align: center">
              <el-progress
                type="dashboard"
                :percentage="riskData.risk_score || 0"
                :color="riskColor"
                :width="120"
              />
              <div class="risk-label">{{ riskLevelText }}</div>
            </el-col>
            <el-col :span="16">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="年化波动率">
                  {{ ((riskData.volatility || 0) * 100).toFixed(2) }}%
                </el-descriptions-item>
                <el-descriptions-item label="最大回撤">
                  {{ ((riskData.max_drawdown || 0) * 100).toFixed(2) }}%
                </el-descriptions-item>
              </el-descriptions>
              <div v-if="riskData.factors?.length > 0" style="margin-top: 12px">
                <span style="font-size: 13px; color: #909399">风险因素：</span>
                <el-tag v-for="f in riskData.factors" :key="f" type="warning" size="small" style="margin: 2px">
                  {{ f }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 右侧：可解释性面板 -->
      <el-col :span="8">
        <ExplainabilityPanel
          :prediction="ontologyResult"
          :ontologyFeatures="ontologyResult?.ontology_features"
          :contradictions="ontologyResult?.contradictions"
          :explanation="ontologyResult?.explanation"
          :causalChain="causalChain"
        />
      </el-col>
    </el-row>
      </el-tab-pane>

      <!-- 上涨趋势预测 Tab -->
      <el-tab-pane label="上涨趋势预测" name="rising">
        <RisingStocks @select="onRisingStockSelect" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { predictionApi, reasoningApi } from '@/api'
import KLineChart from '@/components/KLineChart.vue'
import ExplainabilityPanel from '@/components/ExplainabilityPanel.vue'
import RisingStocks from '@/components/RisingStocks.vue'

const activeTab = ref('single')
const stockCode = ref('600519')
const stockName = ref('')
const days = ref(5)
const loading = ref(false)

const priceData = ref<any[]>([])
const predictions = ref<any[]>([])
const trendData = ref<any>(null)
const riskData = ref<any>(null)
const ontologyResult = ref<any>(null)
const causalChain = ref<any>(null)

const trendClass = computed(() => {
  const trend = trendData.value?.trend
  if (trend === 'bullish' || trend === 'up') return 'trend-up'
  if (trend === 'bearish' || trend === 'down') return 'trend-down'
  return 'trend-neutral'
})

const trendIcon = computed(() => {
  const trend = trendData.value?.trend
  if (trend === 'bullish' || trend === 'up') return '📈'
  if (trend === 'bearish' || trend === 'down') return '📉'
  return '➡️'
})

const trendText = computed(() => {
  const trend = trendData.value?.trend
  if (trend === 'bullish' || trend === 'up') return '看涨'
  if (trend === 'bearish' || trend === 'down') return '看跌'
  return '中性'
})

const riskColor = computed(() => {
  const score = riskData.value?.risk_score || 0
  if (score < 30) return '#67c23a'
  if (score < 60) return '#e6a23c'
  return '#f56c6c'
})

const riskLevelText = computed(() => {
  const level = riskData.value?.risk_level
  if (level === 'low') return '低风险'
  if (level === 'medium') return '中风险'
  return '高风险'
})

const loadAllData = async () => {
  if (!stockCode.value) {
    ElMessage.warning('请输入股票代码')
    return
  }

  loading.value = true
  try {
    // 并行加载所有数据
    const [priceDataRes, priceRes, trendRes, riskRes, ontoRes] = await Promise.all([
      predictionApi.getPriceData(stockCode.value, 120),
      predictionApi.predictPrice(stockCode.value, days.value),
      predictionApi.predictTrend(stockCode.value, 'week'),
      predictionApi.calculateRisk(stockCode.value),
      predictionApi.ontologyEnhanced(stockCode.value, days.value),
    ])

    // K 线图数据
    if ((priceDataRes as any).success) {
      const data = (priceDataRes as any).data
      priceData.value = data?.prices || []
      stockName.value = data?.stock_name || ''
    }

    // 预测结果
    if ((priceRes as any).success) {
      predictions.value = (priceRes as any).data?.predictions || []
    }
    if ((trendRes as any).success) {
      trendData.value = (trendRes as any).data
    }
    if ((riskRes as any).success) {
      riskData.value = (riskRes as any).data
    }
    if ((ontoRes as any).success) {
      ontologyResult.value = (ontoRes as any).data
    }

    // 获取因果链
    try {
      const chainsRes = await reasoningApi.getChains(stockCode.value, 30) as any
      if (chainsRes.success && chainsRes.data?.chains?.length > 0) {
        causalChain.value = chainsRes.data.chains[0]
      }
    } catch (_) {}

    ElMessage.success('预测完成')
  } catch (e: any) {
    ElMessage.error(e?.message || '预测失败')
  } finally {
    loading.value = false
  }
}

// 从上涨趋势列表选择股票
const onRisingStockSelect = (code: string) => {
  stockCode.value = code
  activeTab.value = 'single'
  loadAllData()
}
</script>

<style scoped>
.prediction-page {
  max-width: 1400px;
  margin: 0 auto;
}

.trend-card {
  display: flex;
  align-items: center;
  gap: 24px;
}

.trend-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 24px;
  border-radius: 12px;
  min-width: 100px;
}

.trend-up { background: #f0f9eb; }
.trend-down { background: #fef0f0; }
.trend-neutral { background: #f5f7fa; }

.trend-indicator .icon { font-size: 32px; }
.trend-indicator .text { font-size: 18px; font-weight: 600; margin-top: 8px; }
.trend-up .text { color: #67c23a; }
.trend-down .text { color: #f56c6c; }
.trend-neutral .text { color: #909399; }

.trend-details { flex: 1; }

.risk-label {
  font-size: 16px;
  font-weight: 600;
  margin-top: 8px;
}
</style>
