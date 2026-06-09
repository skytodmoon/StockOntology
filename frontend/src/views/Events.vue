<template>
  <div class="events">
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-select v-model="filters.eventType" placeholder="事件类型" clearable>
            <el-option label="政策事件" value="PolicyEvent" />
            <el-option label="公司事件" value="CompanyEvent" />
            <el-option label="宏观事件" value="MacroEvent" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.impactLevel" placeholder="影响级别" clearable>
            <el-option label="高" value="High" />
            <el-option label="中" value="Medium" />
            <el-option label="低" value="Low" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索关键词..."
            clearable
          />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="loadEvents" :loading="loading">
            搜索
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 事件列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>市场事件 ({{ events.length }})</span>
          <el-button type="primary" size="small" @click="loadEvents">
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="events" style="width: 100%" @row-click="handleRowClick">
        <el-table-column prop="eventDate" label="日期" width="120" sortable />
        <el-table-column prop="title" label="事件标题" min-width="200" />
        <el-table-column prop="eventType" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getEventTypeTag(row.eventType)">
              {{ getEventTypeName(row.eventType) }}
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
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="showEventDetail(row)">
              详情
            </el-button>
            <el-button type="primary" link @click="analyzeEvent(row)">
              分析
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 事件详情抽屉 -->
    <el-drawer v-model="showDrawer" :title="currentEvent?.title" size="500px">
      <div v-if="currentEvent" class="event-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="事件ID">
            {{ currentEvent.eventId }}
          </el-descriptions-item>
          <el-descriptions-item label="事件类型">
            <el-tag :type="getEventTypeTag(currentEvent.eventType)">
              {{ getEventTypeName(currentEvent.eventType) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发生日期">
            {{ currentEvent.eventDate }}
          </el-descriptions-item>
          <el-descriptions-item label="影响级别">
            <el-tag :type="getImpactTag(currentEvent.impactLevel)">
              {{ currentEvent.impactLevel }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="事件来源">
            {{ currentEvent.source || '未知' }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="event-content">
          <h4>事件内容</h4>
          <p>{{ currentEvent.content || '暂无详细内容' }}</p>
        </div>

        <div class="event-tags" v-if="currentEvent.tags?.length">
          <h4>标签</h4>
          <el-tag v-for="tag in currentEvent.tags" :key="tag" class="tag-item">
            {{ tag }}
          </el-tag>
        </div>

        <div class="event-impact" v-if="impactData">
          <h4>影响分析</h4>
          <div v-for="item in impactData.impacts" :key="item.target" class="impact-item">
            <span>{{ item.target?.stockName || item.target?.name }}</span>
            <el-tag :type="item.impactDirection === 'Positive' ? 'success' : 'danger'">
              {{ item.impactDirection }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { eventApi } from '@/api'

const events = ref<any[]>([])
const loading = ref(false)
const showDrawer = ref(false)
const currentEvent = ref<any>(null)
const impactData = ref<any>(null)

const filters = ref({
  eventType: '',
  impactLevel: '',
  keyword: '',
})

onMounted(() => {
  loadEvents()
})

const loadEvents = async () => {
  loading.value = true
  try {
    const params: any = { limit: 100 }
    if (filters.value.eventType) params.event_type = filters.value.eventType
    if (filters.value.impactLevel) params.impact_level = filters.value.impactLevel

    let res: any
    if (filters.value.keyword) {
      res = await eventApi.search(filters.value.keyword)
    } else {
      res = await eventApi.getList(params)
    }

    if (res.success) {
      events.value = res.data || []
    }
  } catch (e) {
    console.error('Failed to load events:', e)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    eventType: '',
    impactLevel: '',
    keyword: '',
  }
  loadEvents()
}

const handleRowClick = (row: any) => {
  showEventDetail(row)
}

const showEventDetail = async (event: any) => {
  currentEvent.value = event
  showDrawer.value = true

  // 加载影响数据
  try {
    const res: any = await eventApi.getImpact(event.eventId)
    if (res.success) {
      impactData.value = res.data
    }
  } catch (e) {
    console.error('Failed to load impact:', e)
  }
}

const analyzeEvent = (event: any) => {
  // TODO: 调用 LLM 分析
  console.log('Analyze event:', event)
}

const getEventTypeTag = (type: string) => {
  const map: Record<string, string> = {
    PolicyEvent: 'warning',
    CompanyEvent: '',
    MacroEvent: 'danger',
    IndustryEvent: 'info',
  }
  return map[type] || 'info'
}

const getEventTypeName = (type: string) => {
  const map: Record<string, string> = {
    PolicyEvent: '政策',
    CompanyEvent: '公司',
    MacroEvent: '宏观',
    IndustryEvent: '行业',
  }
  return map[type] || type
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
.events {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-card,
.list-card {
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-detail {
  padding: 16px;
}

.event-content {
  margin-top: 16px;
}

.event-content h4,
.event-tags h4,
.event-impact h4 {
  margin-bottom: 8px;
  color: #303133;
}

.event-content p {
  color: #606266;
  line-height: 1.6;
}

.event-tags {
  margin-top: 16px;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.event-impact {
  margin-top: 16px;
}

.impact-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}
</style>
