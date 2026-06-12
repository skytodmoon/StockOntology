<template>
  <div class="causal-chain-view">
    <div class="chain-header">
      <el-icon><Connection /></el-icon>
      <span class="title">因果传导链</span>
      <el-tag v-if="chain" :type="confidenceTagType" size="small">
        置信度: {{ (chain.overall_confidence * 100).toFixed(0) }}%
      </el-tag>
    </div>

    <div v-if="!chain" class="empty-state">
      <el-empty description="暂无因果链数据" :image-size="80" />
    </div>

    <div v-else class="chain-content">
      <!-- 源事件 -->
      <div class="chain-event">
        <div class="event-badge">
          <el-tag :type="eventTypeTag" effect="dark" size="small">
            {{ chain.event?.type || '事件' }}
          </el-tag>
        </div>
        <div class="event-info">
          <div class="event-name">{{ chain.event?.name || '未知事件' }}</div>
          <div class="event-id">ID: {{ chain.event?.id }}</div>
        </div>
      </div>

      <!-- 传导步骤 -->
      <div class="chain-steps">
        <div
          v-for="(step, index) in chain.steps"
          :key="step.step_id"
          class="step-item"
          :class="{ 'step-positive': step.impact_direction === 'positive', 'step-negative': step.impact_direction === 'negative' }"
        >
          <!-- 连接线 -->
          <div class="step-connector">
            <div class="connector-line"></div>
            <div class="connector-arrow">
              <el-icon><ArrowDown /></el-icon>
            </div>
          </div>

          <!-- 步骤内容 -->
          <div class="step-card">
            <div class="step-header">
              <el-tag size="small" type="info">{{ step.rule_applied }}</el-tag>
              <span class="step-confidence">
                {{ (step.confidence * 100).toFixed(0) }}%
              </span>
            </div>

            <div class="step-flow">
              <div class="node source-node">
                <span class="node-type">{{ step.source_node?.type || '' }}</span>
                <span class="node-name">{{ step.source_node?.name || '' }}</span>
              </div>

              <div class="flow-arrow">
                <span class="arrow-icon">
                  {{ step.impact_direction === 'positive' ? '📈' : step.impact_direction === 'negative' ? '📉' : '➡️' }}
                </span>
                <span class="relationship">{{ step.relationship }}</span>
              </div>

              <div class="node target-node">
                <span class="node-type">{{ step.target_node?.type || '' }}</span>
                <span class="node-name">{{ step.target_node?.name || '' }}</span>
              </div>
            </div>

            <div v-if="step.evidence" class="step-evidence">
              <el-icon><Document /></el-icon>
              {{ step.evidence }}
            </div>
          </div>
        </div>
      </div>

      <!-- 结论 -->
      <div class="chain-conclusion">
        <el-divider content-position="left">结论</el-divider>
        <div class="conclusion-text">{{ chain.conclusion }}</div>
        <div class="conclusion-stats">
          <el-statistic title="受影响公司" :value="chain.total_affected_companies" />
          <el-statistic title="推理步骤" :value="chain.steps?.length || 0" />
          <el-statistic title="综合置信度" :value="((chain.overall_confidence || 0) * 100).toFixed(0) + '%'" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface ChainStep {
  step_id: string
  rule_applied: string
  source_node?: { type: string; name: string }
  target_node?: { type: string; name: string }
  relationship: string
  evidence: string
  confidence: number
  impact_direction: string
}

interface CausalChain {
  chain_id: string
  event?: { id: string; name: string; type: string }
  steps: ChainStep[]
  conclusion: string
  overall_confidence: number
  total_affected_companies: number
}

const props = defineProps<{
  chain: CausalChain | null
}>()

const confidenceTagType = computed(() => {
  const c = props.chain?.overall_confidence || 0
  if (c >= 0.7) return 'success'
  if (c >= 0.4) return 'warning'
  return 'danger'
})

const eventTypeTag = computed(() => {
  const type = props.chain?.event?.type
  if (type === 'PolicyEvent') return 'warning'
  if (type === 'MacroEvent') return 'danger'
  return ''
})
</script>

<style scoped>
.causal-chain-view {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.chain-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chain-event {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.event-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.event-id {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.chain-steps {
  padding-left: 24px;
}

.step-item {
  position: relative;
}

.step-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 40px;
}

.connector-line {
  width: 2px;
  flex: 1;
  background: #dcdfe6;
}

.connector-arrow {
  color: #909399;
  font-size: 14px;
}

.step-card {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
  transition: all 0.3s;
}

.step-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.step-positive .step-card {
  border-left: 3px solid #67c23a;
}

.step-negative .step-card {
  border-left: 3px solid #f56c6c;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.step-confidence {
  font-size: 13px;
  color: #909399;
}

.step-flow {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.node {
  display: flex;
  flex-direction: column;
  padding: 8px 12px;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e4e7ed;
  min-width: 120px;
}

.source-node {
  border-color: #409eff;
}

.target-node {
  border-color: #67c23a;
}

.node-type {
  font-size: 11px;
  color: #909399;
}

.node-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.flow-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.arrow-icon {
  font-size: 20px;
}

.relationship {
  font-size: 11px;
  color: #909399;
}

.step-evidence {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.chain-conclusion {
  margin-top: 16px;
}

.conclusion-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
}

.conclusion-stats {
  display: flex;
  gap: 32px;
}

.empty-state {
  padding: 40px 0;
}
</style>
