<template>
  <div class="prediction">
    <!-- 股票选择 -->
    <el-card class="control-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-select v-model="selectedStock" placeholder="选择股票" filterable>
            <el-option label="贵州茅台" value="600519" />
            <el-option label="招商银行" value="600036" />
            <el-option label="宁德时代" value="300750" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-input-number v-model="predictDays" :min="1" :max="30" />
          <span class="label">预测天数</span>
        </el-col>
        <el-col :span="4">
          <el-select v-model="predictPeriod" placeholder="趋势周期">
            <el-option label="周" value="week" />
            <el-option label="月" value="month" />
            <el-option label="季" value="quarter" />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-button type="primary" @click="predictPrice" :loading="loading">
            价格预测
          </el-button>
          <el-button @click="predictTrend" :loading="loading">
            趋势分析
          </el-button>
          <el-button @click="calculateRisk" :loading="loading">
            风险评估
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 预测结果 -->
    <el-row :gutter="20" class="result-row">
      <!-- 价格预测图表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>价格预测</span>
          </template>
          <div ref="priceChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 趋势和风险 -->
      <el-col :span="8">
        <!-- 趋势分析 -->
        <el-card class="trend-card">
          <template #header>
            <span>趋势分析</span>
          </template>
          <div v-if="trendResult" class="trend-result">
            <div class="trend-indicator">
              <el-icon :class="trendResult.trend">
                <component :is="getTrendIcon(trendResult.trend)" />
              </el-icon>
              <span :class="['trend-text', trendResult.trend]">
                {{ getTrendText(trendResult.trend) }}
              </span>
            </div>
            <el-progress
              :percentage="Math.round(trendResult.confidence * 100)"
              :color="getTrendColor(trendResult.trend)"
            />
            <div class="trend-indicators">
              <div v-for="(value, key) in trendResult.indicators" :key="key" class="indicator-item">
                <span class="indicator-name">{{ key }}:</span>
                <span class="indicator-value">{{ value }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="请选择股票进行分析" />
        </el-card>

        <!-- 风险评估 -->
        <el-card class="risk-card">
          <template #header>
            <span>风险评估</span>
          </template>
          <div v-if="riskResult" class="risk-result">
            <el-progress
              type="dashboard"
              :percentage="riskResult.risk_score"
              :color="getRiskColor(riskResult.risk_score)"
            />
            <div class="risk-label">
              <el-tag :type="getRiskType(riskResult.risk_level)">
                {{ getRiskText(riskResult.risk_level) }}
              </el-tag>
            </div>
            <div class="risk-factors">
              <span>风险因素:</span>
              <ul>
                <li v-for="factor in riskResult.factors" :key="factor">{{ factor }}</li>
              </ul>
            </div>
          </div>
          <el-empty v-else description="请选择股票进行分析" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { predictionApi } from '@/api'
import * as echarts from 'echarts'

const selectedStock = ref('')
const predictDays = ref(5)
const predictPeriod = ref('week')
const loading = ref(false)
const trendResult = ref<any>(null)
const riskResult = ref<any>(null)
const priceChart = ref<HTMLElement>()

let chart: echarts.ECharts | null = null

onMounted(() => {
  initChart()
})

const initChart = () => {
  if (!priceChart.value) return
  chart = echarts.init(priceChart.value)
  window.addEventListener('resize', () => chart?.resize())
}

const predictPrice = async () => {
  if (!selectedStock.value) return

  loading.value = true
  try {
    const res: any = await predictionApi.predictPrice(selectedStock.value, predictDays.value)
    if (res.success) {
      renderPredictionChart(res.data)
    }
  } catch (e) {
    console.error('Prediction failed:', e)
  } finally {
    loading.value = false
  }
}

const renderPredictionChart = (data: any) => {
  if (!chart) return

  const predictions = data.predictions || []
  const days = predictions.map((p: any) => `Day ${p.day}`)
  const prices = predictions.map((p: any) => p.predicted_price)
  const upper = predictions.map((p: any) => p.confidence_interval?.upper || 0)
  const lower = predictions.map((p: any) => p.confidence_interval?.lower || 0)

  const option = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['预测价格', '置信区间'],
    },
    xAxis: {
      type: 'category',
      data: days,
    },
    yAxis: {
      type: 'value',
      name: '价格',
    },
    series: [
      {
        name: '预测价格',
        type: 'line',
        data: prices,
        itemStyle: { color: '#409eff' },
      },
      {
        name: '置信上界',
        type: 'line',
        data: upper,
        lineStyle: { opacity: 0 },
        areaStyle: { color: '#409eff', opacity: 0.1 },
        stack: 'confidence',
      },
      {
        name: '置信下界',
        type: 'line',
        data: lower,
        lineStyle: { opacity: 0 },
        areaStyle: { color: '#fff' },
        stack: 'confidence',
      },
    ],
  }

  chart.setOption(option, true)
}

const predictTrend = async () => {
  if (!selectedStock.value) return

  loading.value = true
  try {
    const res: any = await predictionApi.predictTrend(selectedStock.value, predictPeriod.value)
    if (res.success) {
      trendResult.value = res.data
    }
  } catch (e) {
    console.error('Trend prediction failed:', e)
  } finally {
    loading.value = false
  }
}

const calculateRisk = async () => {
  if (!selectedStock.value) return

  loading.value = true
  try {
    const res: any = await predictionApi.calculateRisk(selectedStock.value)
    if (res.success) {
      riskResult.value = res.data
    }
  } catch (e) {
    console.error('Risk calculation failed:', e)
  } finally {
    loading.value = false
  }
}

const getTrendIcon = (trend: string) => {
  const map: Record<string, string> = {
    bullish: 'Top',
    bearish: 'Bottom',
    neutral: 'Right',
  }
  return map[trend] || 'Right'
}

const getTrendText = (trend: string) => {
  const map: Record<string, string> = {
    bullish: '看涨',
    bearish: '看跌',
    neutral: '中性',
  }
  return map[trend] || '未知'
}

const getTrendColor = (trend: string) => {
  const map: Record<string, string> = {
    bullish: '#67c23a',
    bearish: '#f56c6c',
    neutral: '#e6a23c',
  }
  return map[trend] || '#909399'
}

const getRiskColor = (score: number) => {
  if (score < 30) return '#67c23a'
  if (score < 60) return '#e6a23c'
  return '#f56c6c'
}

const getRiskType = (level: string) => {
  const map: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
  }
  return map[level] || 'info'
}

const getRiskText = (level: string) => {
  const map: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  }
  return map[level] || '未知'
}
</script>

<style scoped>
.prediction {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-card {
  flex-shrink: 0;
}

.label {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.result-row {
  flex: 1;
}

.chart-container {
  height: 400px;
}

.trend-card,
.risk-card {
  margin-bottom: 16px;
}

.trend-result,
.risk-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
}

.trend-indicator .bullish {
  color: #67c23a;
}

.trend-indicator .bearish {
  color: #f56c6c;
}

.trend-indicator .neutral {
  color: #e6a23c;
}

.trend-text {
  font-size: 18px;
  font-weight: bold;
}

.trend-indicators {
  width: 100%;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.indicator-name {
  color: #909399;
}

.indicator-value {
  font-weight: bold;
}

.risk-label {
  margin-top: 8px;
}

.risk-factors {
  width: 100%;
}

.risk-factors ul {
  margin-top: 8px;
  padding-left: 20px;
}

.risk-factors li {
  color: #606266;
  margin-bottom: 4px;
}
</style>
