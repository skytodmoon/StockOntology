<template>
  <div class="explainability-panel">
    <div class="panel-header">
      <el-icon><InfoFilled /></el-icon>
      <span class="title">可解释性分析</span>
    </div>

    <!-- 预测结果 -->
    <div v-if="prediction" class="section">
      <div class="section-title">预测结论</div>
      <div class="prediction-result">
        <div class="trend-indicator" :class="trendClass">
          <span class="trend-icon">{{ trendIcon }}</span>
          <span class="trend-text">{{ trendText }}</span>
        </div>
        <div class="confidence-bar">
          <span class="label">置信度</span>
          <el-progress
            :percentage="Math.round((prediction.confidence || 0) * 100)"
            :color="confidenceColor"
            :stroke-width="10"
          />
        </div>
      </div>
    </div>

    <!-- 本体特征 -->
    <div v-if="ontologyFeatures" class="section">
      <div class="section-title">
        本体特征
        <el-tooltip content="来自知识图谱的结构化特征，传统量化模型无法获取">
          <el-icon><QuestionFilled /></el-icon>
        </el-tooltip>
      </div>
      <div class="features-grid">
        <div class="feature-item">
          <span class="feature-label">事件影响</span>
          <span class="feature-value" :class="{ 'positive': ontologyFeatures.event_impact?.accumulated_score > 0, 'negative': ontologyFeatures.event_impact?.accumulated_score < 0 }">
            {{ (ontologyFeatures.event_impact?.accumulated_score || 0).toFixed(2) }}
          </span>
        </div>
        <div class="feature-item">
          <span class="feature-label">机构持仓</span>
          <span class="feature-value">{{ ontologyFeatures.institutional_sentiment?.investor_count || 0 }} 家</span>
        </div>
        <div class="feature-item">
          <span class="feature-label">竞争排名</span>
          <span class="feature-value">第 {{ ontologyFeatures.competition_pressure?.rank || '?' }} 名</span>
        </div>
        <div class="feature-item">
          <span class="feature-label">供应链风险</span>
          <span class="feature-value" :class="{ 'warning': ontologyFeatures.supply_chain_risk?.risk_score > 0.5 }">
            {{ ((ontologyFeatures.supply_chain_risk?.risk_score || 0) * 100).toFixed(0) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- 矛盾检测 -->
    <div v-if="contradictions && contradictions.length > 0" class="section">
      <div class="section-title">
        <el-icon color="#e6a23c"><WarningFilled /></el-icon>
        矛盾提示
      </div>
      <div class="contradictions">
        <el-alert
          v-for="(c, i) in contradictions"
          :key="i"
          :title="c.message"
          :type="c.severity === 'warning' ? 'warning' : 'info'"
          :closable="false"
          show-icon
          style="margin-bottom: 8px"
        />
      </div>
    </div>

    <!-- 可解释文本 -->
    <div v-if="explanation" class="section">
      <div class="section-title">分析说明</div>
      <div class="explanation-text">{{ explanation }}</div>
    </div>

    <!-- 推理链 -->
    <div v-if="causalChain" class="section">
      <div class="section-title">推理路径</div>
      <CausalChainView :chain="causalChain" />
    </div>

    <!-- 无数据 -->
    <div v-if="!prediction && !ontologyFeatures && !explanation" class="empty-state">
      <el-empty description="暂无可解释性数据" :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import CausalChainView from './CausalChainView.vue'

interface Prediction {
  trend?: string
  confidence?: number
}

interface OntologyFeatures {
  event_impact?: { accumulated_score: number; event_count: number }
  institutional_sentiment?: { investor_count: number; total_ratio: number }
  competition_pressure?: { rank: number; competitor_count: number }
  supply_chain_risk?: { risk_score: number }
}

interface Contradiction {
  type: string
  message: string
  severity: string
}

const props = defineProps<{
  prediction?: Prediction | null
  ontologyFeatures?: OntologyFeatures | null
  contradictions?: Contradiction[]
  explanation?: string
  causalChain?: any
}>()

const trendClass = computed(() => {
  const trend = props.prediction?.trend
  if (trend === 'up') return 'trend-up'
  if (trend === 'down') return 'trend-down'
  return 'trend-neutral'
})

const trendIcon = computed(() => {
  const trend = props.prediction?.trend
  if (trend === 'up') return '📈'
  if (trend === 'down') return '📉'
  return '➡️'
})

const trendText = computed(() => {
  const trend = props.prediction?.trend
  if (trend === 'up') return '看涨'
  if (trend === 'down') return '看跌'
  return '中性'
})

const confidenceColor = computed(() => {
  const c = props.prediction?.confidence || 0
  if (c >= 0.7) return '#67c23a'
  if (c >= 0.4) return '#e6a23c'
  return '#f56c6c'
})
</script>

<style scoped>
.explainability-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.prediction-result {
  display: flex;
  align-items: center;
  gap: 24px;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 600;
}

.trend-up {
  background: #f0f9eb;
  color: #67c23a;
}

.trend-down {
  background: #fef0f0;
  color: #f56c6c;
}

.trend-neutral {
  background: #f5f7fa;
  color: #909399;
}

.confidence-bar {
  flex: 1;
}

.confidence-bar .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  display: block;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 6px;
}

.feature-label {
  font-size: 13px;
  color: #909399;
}

.feature-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.feature-value.positive { color: #67c23a; }
.feature-value.negative { color: #f56c6c; }
.feature-value.warning { color: #e6a23c; }

.explanation-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}

.contradictions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  padding: 20px 0;
}
</style>
