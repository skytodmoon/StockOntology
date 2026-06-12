<template>
  <div class="data-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>数据管理中心</h2>
      <p class="subtitle">手动触发数据采集、本体更新、推理刷新等任务</p>
    </div>

    <!-- 系统状态概览 -->
    <el-card class="status-card">
      <template #header>
        <div class="card-header">
          <span>系统状态</span>
          <el-button type="primary" link @click="loadStatus">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="6" v-for="(info, key) in statusData" :key="key">
          <div class="status-item">
            <div class="status-icon" :class="getStatusClass(info.last_run)">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-name">{{ info.name }}</div>
              <div class="status-time">{{ formatTime(info.last_run) }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据采集任务 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>📊 数据采集</span>
          </template>
          <div class="task-list">
            <div class="task-item" v-for="task in collectionTasks" :key="task.key">
              <div class="task-info">
                <div class="task-name">{{ task.name }}</div>
                <div class="task-desc">{{ task.description }}</div>
              </div>
              <el-button
                type="primary"
                size="small"
                :loading="taskLoading[task.key]"
                @click="triggerTask(task.key)"
              >
                <el-icon><VideoPlay /></el-icon>
                执行
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 推理与预测任务 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>🧠 推理与预测</span>
          </template>
          <div class="task-list">
            <div class="task-item" v-for="task in reasoningTasks" :key="task.key">
              <div class="task-info">
                <div class="task-name">{{ task.name }}</div>
                <div class="task-desc">{{ task.description }}</div>
              </div>
              <el-button
                type="success"
                size="small"
                :loading="taskLoading[task.key]"
                @click="triggerTask(task.key)"
              >
                <el-icon><VideoPlay /></el-icon>
                执行
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 一键操作 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>⚡ 一键操作</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="quick-action">
            <el-button type="primary" size="large" @click="runFullPipeline" :loading="fullPipelineLoading">
              <el-icon><RefreshRight /></el-icon>
              全量数据更新
            </el-button>
            <p class="action-desc">采集行情 → 更新本体 → 推理 → 预测</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="quick-action">
            <el-button type="warning" size="large" @click="runNewsPipeline" :loading="newsPipelineLoading">
              <el-icon><Document /></el-icon>
              情报更新
            </el-button>
            <p class="action-desc">采集新闻 → LLM分类 → 事件推理</p>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="quick-action">
            <el-button type="success" size="large" @click="runPredictionScan" :loading="predictionLoading">
              <el-icon><TrendCharts /></el-icon>
              预测扫描
            </el-button>
            <p class="action-desc">扫描全部股票 → 筛选看涨标的</p>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 任务执行日志 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>📋 执行日志</span>
          <el-select v-model="selectedLogTask" size="small" style="width: 200px" @change="loadLogs">
            <el-option label="行情采集" value="collect_market" />
            <el-option label="新闻采集" value="collect_news" />
            <el-option label="事件推理" value="reason_events" />
            <el-option label="预测扫描" value="scan_predictions" />
          </el-select>
        </div>
      </template>
      <el-table :data="taskLogs" style="width: 100%" max-height="300">
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
        </el-table-column>
        <el-table-column prop="task" label="任务" width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">{{ row.duration ? row.duration.toFixed(1) + 's' : '-' }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="taskLogs.length === 0" description="暂无日志" :image-size="60" />
    </el-card>

    <!-- 缓存的看涨股票 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>🔥 今日看涨股票（缓存）</span>
          <el-button type="primary" link @click="loadCachedRising">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>
      <div v-if="cachedRising">
        <div class="cache-info">
          扫描时间: {{ formatTime(cachedRising.scan_time) }} |
          扫描: {{ cachedRising.total_scanned }} 只 |
          看涨: {{ cachedRising.total_rising }} 只
        </div>
        <el-table :data="cachedRising.rising_stocks?.slice(0, 10)" style="width: 100%">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="stock_name" label="股票" width="120" />
          <el-table-column prop="stock_code" label="代码" width="100" />
          <el-table-column prop="leader_tag" label="赛道" width="150" />
          <el-table-column label="现价" width="100">
            <template #default="{ row }">¥{{ row.current_price }}</template>
          </el-table-column>
          <el-table-column label="预测价" width="100">
            <template #default="{ row }">¥{{ row.predicted_price }}</template>
          </el-table-column>
          <el-table-column label="预测涨幅" width="120">
            <template #default="{ row }">
              <span :class="row.predicted_change_pct >= 0 ? 'text-up' : 'text-down'">
                {{ row.predicted_change_pct >= 0 ? '+' : '' }}{{ row.predicted_change_pct }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="100">
            <template #default="{ row }">{{ (row.confidence * 100).toFixed(0) }}%</template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无缓存数据，请先执行预测扫描" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { schedulerApi } from '@/api'

const statusData = ref<any>({})
const taskLogs = ref<any[]>([])
const selectedLogTask = ref('collect_market')
const cachedRising = ref<any>(null)
const taskLoading = ref<Record<string, boolean>>({})
const fullPipelineLoading = ref(false)
const newsPipelineLoading = ref(false)
const predictionLoading = ref(false)

const collectionTasks = [
  { key: 'collect_market', name: '行情数据采集', description: '采集所有公司的每日行情（OHLCV）' },
  { key: 'collect_news', name: '新闻情报采集', description: '采集热点新闻，LLM自动分类事件' },
  { key: 'collect_financial', name: '财务数据采集', description: '采集最新财务报告' },
]

const reasoningTasks = [
  { key: 'reason_events', name: '事件因果推理', description: '自动推理新事件的影响传导链' },
  { key: 'refresh_reasoning', name: '每日推理刷新', description: '重新推理近30天活跃事件' },
  { key: 'scan_predictions', name: '每日预测扫描', description: '扫描全部股票，筛选看涨标的' },
  { key: 'clear_cache', name: '缓存清理', description: '清除过期缓存和因果链' },
]

onMounted(() => {
  loadStatus()
  loadLogs()
  loadCachedRising()
})

const loadStatus = async () => {
  try {
    const res = await schedulerApi.getStatus() as any
    if (res.success) {
      statusData.value = res.data?.tasks || {}
    }
  } catch (e) {
    console.error('Load status failed:', e)
  }
}

const loadLogs = async () => {
  try {
    const res = await schedulerApi.getTaskLogs(selectedLogTask.value, 20) as any
    if (res.success) {
      taskLogs.value = res.data?.logs || []
    }
  } catch (e) {
    console.error('Load logs failed:', e)
  }
}

const loadCachedRising = async () => {
  try {
    const res = await schedulerApi.getCachedRisingStocks() as any
    if (res.success && res.data) {
      cachedRising.value = res.data
    }
  } catch (e) {
    console.error('Load cached rising failed:', e)
  }
}

const triggerTask = async (taskKey: string) => {
  taskLoading.value[taskKey] = true
  try {
    const res = await schedulerApi.triggerTask(taskKey) as any
    if (res.success) {
      ElMessage.success(`任务已提交: ${res.data?.task_name || taskKey}`)
      // 延迟刷新状态
      setTimeout(() => {
        loadStatus()
        loadLogs()
      }, 3000)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '任务触发失败')
  } finally {
    taskLoading.value[taskKey] = false
  }
}

const runFullPipeline = async () => {
  fullPipelineLoading.value = true
  try {
    // 按顺序触发
    await schedulerApi.triggerTask('collect_market')
    ElMessage.info('行情采集已启动，完成后将自动触发本体更新和推理...')
    setTimeout(() => {
      loadStatus()
      fullPipelineLoading.value = false
    }, 5000)
  } catch (e: any) {
    ElMessage.error(e?.message || '全量更新失败')
    fullPipelineLoading.value = false
  }
}

const runNewsPipeline = async () => {
  newsPipelineLoading.value = true
  try {
    await schedulerApi.triggerTask('collect_news')
    ElMessage.info('新闻采集已启动，完成后将自动触发事件推理...')
    setTimeout(() => {
      loadStatus()
      newsPipelineLoading.value = false
    }, 5000)
  } catch (e: any) {
    ElMessage.error(e?.message || '情报更新失败')
    newsPipelineLoading.value = false
  }
}

const runPredictionScan = async () => {
  predictionLoading.value = true
  try {
    await schedulerApi.triggerTask('scan_predictions')
    ElMessage.info('预测扫描已启动，请稍后刷新查看结果...')
    setTimeout(() => {
      loadCachedRising()
      predictionLoading.value = false
    }, 10000)
  } catch (e: any) {
    ElMessage.error(e?.message || '预测扫描失败')
    predictionLoading.value = false
  }
}

const formatTime = (time: string) => {
  if (!time || time === '从未执行') return '从未执行'
  try {
    const d = new Date(time)
    return d.toLocaleString('zh-CN')
  } catch {
    return time
  }
}

const getStatusClass = (lastRun: string) => {
  if (!lastRun || lastRun === '从未执行') return 'status-gray'
  try {
    const d = new Date(lastRun)
    const now = new Date()
    const diffHours = (now.getTime() - d.getTime()) / (1000 * 60 * 60)
    if (diffHours < 2) return 'status-green'
    if (diffHours < 24) return 'status-yellow'
    return 'status-red'
  } catch {
    return 'status-gray'
  }
}
</script>

<style scoped>
.data-management {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.page-header .subtitle {
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.status-green { background: #f0f9eb; color: #67c23a; }
.status-yellow { background: #fdf6ec; color: #e6a23c; }
.status-red { background: #fef0f0; color: #f56c6c; }
.status-gray { background: #f5f7fa; color: #909399; }

.status-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.status-time {
  font-size: 12px;
  color: #909399;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.task-name {
  font-weight: 600;
  color: #303133;
}

.task-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.quick-action {
  text-align: center;
  padding: 20px;
}

.quick-action .el-button {
  width: 180px;
  height: 60px;
  font-size: 16px;
}

.action-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.cache-info {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.text-up { color: #f56c6c; font-weight: 600; }
.text-down { color: #67c23a; font-weight: 600; }
</style>
