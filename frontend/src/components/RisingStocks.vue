<template>
  <div class="rising-stocks">
    <div class="panel-header">
      <el-icon><TrendCharts /></el-icon>
      <span class="title">上涨趋势股票预测</span>
      <el-tag type="success" size="small" v-if="!loading && stocks.length > 0">
        共 {{ stocks.length }} 只看涨
      </el-tag>
    </div>

    <!-- 控制栏 -->
    <div class="controls">
      <el-form :inline="true" size="small">
        <el-form-item label="预测天数">
          <el-input-number v-model="predictDays" :min="1" :max="30" @change="loadRisingStocks" />
        </el-form-item>
        <el-form-item label="最低置信度">
          <el-slider v-model="minConfidence" :min="0" :max="1" :step="0.1" :format-tooltip="(v: number) => (v * 100).toFixed(0) + '%'" style="width: 120px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadRisingStocks" :loading="loading">
            <el-icon><Search /></el-icon>
            扫描预测
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计摘要 -->
    <div v-if="scanResult" class="scan-summary">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="summary-item">
            <span class="label">扫描股票</span>
            <span class="value">{{ scanResult.total_scanned }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <span class="label">看涨股票</span>
            <span class="value text-success">{{ scanResult.total_rising }}</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <span class="label">预测天数</span>
            <span class="value">{{ scanResult.prediction_days }}天</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-item">
            <span class="label">最高涨幅</span>
            <span class="value text-danger">+{{ maxChangePct }}%</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 股票列表 -->
    <div v-loading="loading" class="stocks-list">
      <el-table
        v-if="stocks.length > 0"
        :data="stocks"
        stripe
        highlight-current-row
        @row-click="onRowClick"
        style="width: 100%"
      >
        <el-table-column label="排名" width="60" align="center">
          <template #default="{ $index }">
            <div :class="['rank-badge', $index < 3 ? 'rank-top' : '']">{{ $index + 1 }}</div>
          </template>
        </el-table-column>

        <el-table-column label="股票" width="180">
          <template #default="{ row }">
            <div class="stock-info">
              <span class="stock-name">{{ row.stock_name }}</span>
              <span class="stock-code">{{ row.stock_code }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="赛道" width="140">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.leader_tag || row.industry || '-' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="现价" width="100" align="right">
          <template #default="{ row }">
            <span class="price">¥{{ row.current_price }}</span>
          </template>
        </el-table-column>

        <el-table-column label="预测价" width="100" align="right">
          <template #default="{ row }">
            <span class="price predicted">¥{{ row.predicted_price }}</span>
          </template>
        </el-table-column>

        <el-table-column label="预测涨幅" width="120" align="center">
          <template #default="{ row }">
            <div class="change-cell">
              <span class="change-pct" :class="row.predicted_change_pct >= 0 ? 'up' : 'down'">
                {{ row.predicted_change_pct >= 0 ? '+' : '' }}{{ row.predicted_change_pct }}%
              </span>
              <el-progress
                :percentage="Math.min(Math.abs(row.predicted_change_pct), 30)"
                :stroke-width="4"
                :show-text="false"
                :color="row.predicted_change_pct >= 10 ? '#f56c6c' : '#67c23a'"
                style="width: 60px"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column label="置信度" width="100" align="center">
          <template #default="{ row }">
            <el-progress
              type="circle"
              :percentage="Math.round(row.confidence * 100)"
              :width="40"
              :stroke-width="4"
              :color="row.confidence >= 0.7 ? '#67c23a' : row.confidence >= 0.5 ? '#e6a23c' : '#f56c6c'"
            />
          </template>
        </el-table-column>

        <el-table-column label="技术指标" min-width="200">
          <template #default="{ row }">
            <div class="indicators">
              <span v-if="row.indicators?.rsi" class="indicator">
                RSI: <b>{{ row.indicators.rsi }}</b>
              </span>
              <span v-if="row.indicators?.ma5" class="indicator">
                MA5: <b>{{ row.indicators.ma5 }}</b>
              </span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && stocks.length === 0 && scanResult" description="未找到看涨股票" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { predictionApi } from '@/api'

const emit = defineEmits<{
  (e: 'select', stockCode: string): void
}>()

const router = useRouter()
const loading = ref(false)
const predictDays = ref(5)
const minConfidence = ref(0.5)
const stocks = ref<any[]>([])
const scanResult = ref<any>(null)

const maxChangePct = computed(() => {
  if (stocks.value.length === 0) return '0'
  return Math.max(...stocks.value.map(s => s.predicted_change_pct)).toFixed(1)
})

const loadRisingStocks = async () => {
  loading.value = true
  try {
    const res = await predictionApi.getRisingStocks(
      predictDays.value,
      minConfidence.value,
      20
    ) as any

    if (res.success) {
      stocks.value = res.data?.rising_stocks || []
      scanResult.value = res.data
      ElMessage.success(`扫描完成，找到 ${stocks.value.length} 只看涨股票`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '扫描失败')
  } finally {
    loading.value = false
  }
}

const onRowClick = (row: any) => {
  emit('select', row.stock_code)
}
</script>

<style scoped>
.rising-stocks {
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

.controls {
  margin-bottom: 16px;
}

.scan-summary {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.summary-item {
  text-align: center;
}

.summary-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.summary-item .value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }

.rank-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #f5f7fa;
  color: #909399;
  margin: 0 auto;
}

.rank-top {
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
  color: #fff;
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-weight: 600;
  color: #303133;
}

.stock-code {
  font-size: 12px;
  color: #909399;
}

.price {
  font-weight: 600;
  color: #303133;
}

.price.predicted {
  color: #67c23a;
}

.change-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.change-pct {
  font-weight: 700;
  font-size: 14px;
}

.change-pct.up { color: #f56c6c; }
.change-pct.down { color: #67c23a; }

.indicators {
  display: flex;
  gap: 12px;
}

.indicator {
  font-size: 12px;
  color: #606266;
}

.indicator b {
  color: #303133;
}

.stocks-list {
  min-height: 200px;
}
</style>
