<template>
  <div class="kline-chart">
    <div class="chart-header">
      <span class="title">{{ stockName }} ({{ stockCode }})</span>
      <div class="controls">
        <el-radio-group v-model="period" size="small" @change="onPeriodChange">
          <el-radio-button label="daily">日K</el-radio-button>
          <el-radio-button label="weekly">周K</el-radio-button>
        </el-radio-group>
        <el-checkbox v-model="showMA5" label="MA5" size="small" />
        <el-checkbox v-model="showMA10" label="MA10" size="small" />
        <el-checkbox v-model="showMA20" label="MA20" size="small" />
      </div>
    </div>
    <div ref="chartRef" class="chart-container" :style="{ height: height + 'px' }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

interface PriceData {
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

const props = defineProps<{
  stockCode: string
  stockName?: string
  data: PriceData[]
  predictions?: Array<{ day: number; predicted_price: number; confidence_interval?: { lower: number; upper: number } }>
  height?: number
}>()

const chartRef = ref<HTMLElement>()
const period = ref('daily')
const showMA5 = ref(true)
const showMA10 = ref(true)
const showMA20 = ref(true)
let chart: echarts.ECharts | null = null

const onPeriodChange = () => {
  renderChart()
}

const calculateMA = (data: number[], day: number): (number | null)[] => {
  const result: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < day - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < day; j++) {
        sum += data[i - j]
      }
      result.push(parseFloat((sum / day).toFixed(2)))
    }
  }
  return result
}

const renderChart = () => {
  if (!chartRef.value || !props.data || props.data.length === 0) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const dates = props.data.map(d => d.trade_date)
  const ohlc = props.data.map(d => [d.open, d.close, d.low, d.high])
  const volumes = props.data.map(d => d.volume)
  const closes = props.data.map(d => d.close)

  const ma5 = calculateMA(closes, 5)
  const ma10 = calculateMA(closes, 10)
  const ma20 = calculateMA(closes, 20)

  // 预测数据
  const predictionDates: string[] = []
  const predictionPrices: (number | null)[] = []
  const predictionUpper: (number | null)[] = []
  const predictionLower: (number | null)[] = []

  if (props.predictions && props.predictions.length > 0) {
    const lastDate = dates[dates.length - 1]
    props.predictions.forEach((pred, i) => {
      const d = new Date(lastDate)
      d.setDate(d.getDate() + i + 1)
      const dateStr = d.toISOString().split('T')[0]
      predictionDates.push(dateStr)
      predictionPrices.push(pred.predicted_price)
      if (pred.confidence_interval) {
        predictionUpper.push(pred.confidence_interval.upper)
        predictionLower.push(pred.confidence_interval.lower)
      }
    })
  }

  const allDates = [...dates, ...predictionDates]

  const series: any[] = [
    {
      name: 'K线',
      type: 'candlestick',
      data: ohlc,
      itemStyle: {
        color: '#ef5350',
        color0: '#26a69a',
        borderColor: '#ef5350',
        borderColor0: '#26a69a',
      },
    },
    {
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: volumes,
      itemStyle: {
        color: (params: any) => {
          const idx = params.dataIndex
          return closes[idx] >= (closes[idx - 1] || closes[idx]) ? '#ef5350' : '#26a69a'
        },
      },
    },
  ]

  if (showMA5.value) {
    series.push({
      name: 'MA5',
      type: 'line',
      data: ma5,
      smooth: true,
      lineStyle: { width: 1 },
      symbol: 'none',
    })
  }

  if (showMA10.value) {
    series.push({
      name: 'MA10',
      type: 'line',
      data: ma10,
      smooth: true,
      lineStyle: { width: 1 },
      symbol: 'none',
    })
  }

  if (showMA20.value) {
    series.push({
      name: 'MA20',
      type: 'line',
      data: ma20,
      smooth: true,
      lineStyle: { width: 1 },
      symbol: 'none',
    })
  }

  // 预测线
  if (predictionPrices.length > 0) {
    const paddedPredictions = new Array(dates.length - 1).fill(null).concat([closes[closes.length - 1]]).concat(predictionPrices)
    series.push({
      name: '预测',
      type: 'line',
      data: paddedPredictions,
      lineStyle: { width: 2, type: 'dashed', color: '#409eff' },
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#409eff' },
    })

    if (predictionUpper.length > 0 && predictionLower.length > 0) {
      const upperData = new Array(dates.length - 1).fill(null).concat([closes[closes.length - 1]]).concat(predictionUpper)
      const lowerData = new Array(dates.length - 1).fill(null).concat([closes[closes.length - 1]]).concat(predictionLower)
      series.push({
        name: '置信上界',
        type: 'line',
        data: upperData,
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'confidence',
        areaStyle: { opacity: 0 },
      })
      series.push({
        name: '置信下界',
        type: 'line',
        data: lowerData,
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'confidence',
        areaStyle: { color: '#409eff', opacity: 0.15 },
      })
    }
  }

  const option = {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', '预测'],
      top: 0,
    },
    grid: [
      { left: '10%', right: '8%', top: '12%', height: '55%' },
      { left: '10%', right: '8%', top: '73%', height: '18%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: allDates,
        gridIndex: 0,
        axisLabel: { show: false },
        axisTick: { show: false },
      },
      {
        type: 'category',
        data: allDates,
        gridIndex: 1,
        axisLabel: { fontSize: 10 },
      },
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        scale: true,
        splitLine: { lineStyle: { type: 'dashed' } },
      },
      {
        type: 'value',
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: Math.max(0, 100 - (60 / allDates.length) * 100),
        end: 100,
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: 5,
        height: 20,
      },
    ],
    series,
  }

  chart.setOption(option, true)
}

onMounted(() => {
  nextTick(() => {
    renderChart()
  })
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})

watch(() => props.data, () => {
  nextTick(() => renderChart())
}, { deep: true })

watch(() => props.predictions, () => {
  nextTick(() => renderChart())
}, { deep: true })
</script>

<style scoped>
.kline-chart {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-container {
  width: 100%;
}
</style>
