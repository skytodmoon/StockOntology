<template>
  <div class="analysis">
    <!-- 聊天界面 -->
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="chat-card">
          <template #header>
            <div class="card-header">
              <span>智能问答</span>
              <el-select v-model="selectedStock" placeholder="选择股票" size="small" filterable>
                <el-option label="贵州茅台" value="600519" />
                <el-option label="招商银行" value="600036" />
                <el-option label="宁德时代" value="300750" />
              </el-select>
            </div>
          </template>

          <!-- 消息列表 -->
          <div class="message-list" ref="messageList">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              :class="['message', msg.role]"
            >
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
            <div v-if="loading" class="message assistant">
              <div class="message-content">
                <div class="message-text">思考中...</div>
              </div>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="input-area">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入您的问题..."
              @keyup.ctrl.enter="sendMessage"
            />
            <el-button type="primary" @click="sendMessage" :loading="loading">
              发送 (Ctrl+Enter)
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 功能面板 -->
      <el-col :span="8">
        <el-card class="feature-card">
          <template #header>
            <span>快速分析</span>
          </template>
          <div class="feature-list">
            <el-button @click="analyzeStock" :disabled="!selectedStock">
              股票分析
            </el-button>
            <el-button @click="generateReport" :disabled="!selectedStock">
              生成报告
            </el-button>
            <el-button @click="analyzeSentiment">
              情感分析
            </el-button>
          </div>
        </el-card>

        <!-- 情感分析结果 -->
        <el-card v-if="sentimentResult" class="sentiment-card">
          <template #header>
            <span>情感分析结果</span>
          </template>
          <div class="sentiment-result">
            <div class="sentiment-label">
              <span>整体情感:</span>
              <el-tag :type="getSentimentType(sentimentResult.sentiment)">
                {{ sentimentResult.sentiment }}
              </el-tag>
            </div>
            <el-progress
              :percentage="Math.round(sentimentResult.score * 100)"
              :color="getSentimentColor(sentimentResult.score)"
            />
            <div class="sentiment-keywords">
              <span>关键词:</span>
              <el-tag
                v-for="kw in sentimentResult.keywords"
                :key="kw"
                size="small"
                class="keyword-tag"
              >
                {{ kw }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { llmApi } from '@/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const selectedStock = ref('')
const inputMessage = ref('')
const messages = ref<Message[]>([])
const loading = ref(false)
const sentimentResult = ref<any>(null)
const messageList = ref<HTMLElement>()

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage: Message = {
    role: 'user',
    content: inputMessage.value,
    time: new Date().toLocaleTimeString(),
  }
  messages.value.push(userMessage)

  const question = inputMessage.value
  inputMessage.value = ''

  await nextTick()
  scrollToBottom()

  loading.value = true
  try {
    const res: any = await llmApi.ragChat(question, selectedStock.value || undefined)
    if (res.success) {
      const assistantMessage: Message = {
        role: 'assistant',
        content: res.data.answer || '抱歉，无法生成回答。',
        time: new Date().toLocaleTimeString(),
      }
      messages.value.push(assistantMessage)
    }
  } catch (e) {
    console.error('Chat failed:', e)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。',
      time: new Date().toLocaleTimeString(),
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const analyzeStock = async () => {
  if (!selectedStock.value) return

  loading.value = true
  try {
    const res: any = await llmApi.analyzeStock(selectedStock.value)
    if (res.success) {
      messages.value.push({
        role: 'assistant',
        content: res.data.analysis || '分析失败',
        time: new Date().toLocaleTimeString(),
      })
    }
  } catch (e) {
    console.error('Analysis failed:', e)
  } finally {
    loading.value = false
  }
}

const generateReport = async () => {
  if (!selectedStock.value) return

  loading.value = true
  try {
    const res: any = await llmApi.generateReport(selectedStock.value)
    if (res.success) {
      messages.value.push({
        role: 'assistant',
        content: res.data.report || '报告生成失败',
        time: new Date().toLocaleTimeString(),
      })
    }
  } catch (e) {
    console.error('Report generation failed:', e)
  } finally {
    loading.value = false
  }
}

const analyzeSentiment = async () => {
  const text = inputMessage.value || '市场整体表现良好，投资者信心增强'

  try {
    const res: any = await llmApi.analyzeSentiment(text)
    if (res.success) {
      sentimentResult.value = res.data
    }
  } catch (e) {
    console.error('Sentiment analysis failed:', e)
  }
}

const scrollToBottom = () => {
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
}

const getSentimentType = (sentiment: string) => {
  const map: Record<string, string> = {
    positive: 'success',
    negative: 'danger',
    neutral: 'info',
  }
  return map[sentiment] || 'info'
}

const getSentimentColor = (score: number) => {
  if (score >= 0.6) return '#67c23a'
  if (score >= 0.4) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.analysis {
  height: calc(100vh - 120px);
}

.chat-card {
  height: 100%;
}

.chat-card :deep(.el-card__body) {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 4px;
}

.input-area {
  padding: 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 12px;
}

.input-area .el-input {
  flex: 1;
}

.feature-card {
  margin-bottom: 16px;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feature-list .el-button {
  width: 100%;
}

.sentiment-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sentiment-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sentiment-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.keyword-tag {
  margin-left: 4px;
}
</style>
