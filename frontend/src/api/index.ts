import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 图谱 API
export const graphApi = {
  getStats: () => api.get('/graph/stats'),
  getMarketOverview: () => api.get('/graph/market-overview'),
  getCompanyInfo: (code: string) => api.get(`/graph/company/${code}`),
  getCompanyDetails: (code: string) => api.get(`/graph/company/${code}/details`),
  getCompanyGraph: (code: string, depth: number = 2) =>
    api.get(`/graph/company/${code}/graph`, { params: { depth } }),
  getCompanyCompetitors: (code: string) => api.get(`/graph/company/${code}/competitors`),
  getCompanyInvestors: (code: string) => api.get(`/graph/company/${code}/investors`),
  searchCompanies: (keyword: string) =>
    api.get('/graph/search/companies', { params: { keyword } }),
  executeQuery: (query: string, params?: any) =>
    api.post('/graph/query', { query, parameters: params }),
}

// 公司 API
export const companyApi = {
  getList: (params?: any) => api.get('/companies', { params }),
  getDetail: (code: string) => api.get(`/companies/${code}`),
  getGraph: (code: string, depth?: number) =>
    api.get(`/companies/${code}/graph`, { params: { depth } }),
  search: (keyword: string) => api.get(`/companies/search/${keyword}`),
}

// 行业 API
export const industryApi = {
  getList: () => api.get('/industries'),
  getHierarchy: () => api.get('/industries/hierarchy'),
  getDetail: (code: string) => api.get(`/industries/${code}`),
  getChain: (code: string) => api.get(`/industries/${code}/chain`),
}

// 事件 API
export const eventApi = {
  getList: (params?: any) => api.get('/events', { params }),
  getRecent: (days?: number) => api.get('/events/recent', { params: { days } }),
  getDetail: (id: string) => api.get(`/events/${id}`),
  getImpact: (id: string) => api.get(`/events/${id}/impact`),
  search: (keyword: string) => api.get(`/events/search/${keyword}`),
}

// 投资者 API
export const investorApi = {
  getList: (params?: any) => api.get('/investors', { params }),
  getDetail: (id: string) => api.get(`/investors/${id}`),
  getHoldings: (id: string) => api.get(`/investors/${id}/holdings`),
}

// 财务 API
export const financialApi = {
  getReports: (code: string, params?: any) =>
    api.get(`/financial/${code}`, { params }),
  getLatest: (code: string) => api.get(`/financial/${code}/latest`),
  getTrends: (code: string, indicators?: string[]) =>
    api.get(`/financial/${code}/trends`, { params: { indicators } }),
}

// LLM API
export const llmApi = {
  chat: (message: string, stockCode?: string) =>
    api.post('/llm/chat', { message, stock_code: stockCode }),
  ragChat: (message: string, stockCode?: string) =>
    api.post('/llm/rag/chat', { message, stock_code: stockCode }),
  analyzeStock: (code: string) => api.post(`/llm/analyze/stock?stock_code=${code}`),
  analyzeSentiment: (text: string) =>
    api.post('/llm/analyze/sentiment', { text }),
  generateReport: (code: string) =>
    api.post(`/llm/generate/report?stock_code=${code}`),
}

// 预测 API
export const predictionApi = {
  predictPrice: (code: string, days?: number) =>
    api.post(`/prediction/price?stock_code=${code}`, null, { params: { days } }),
  predictTrend: (code: string, period?: string) =>
    api.post(`/prediction/trend?stock_code=${code}`, null, { params: { period } }),
  calculateRisk: (code: string) =>
    api.post(`/prediction/risk?stock_code=${code}`),
  findPatterns: (code: string) =>
    api.post(`/prediction/similar-patterns?stock_code=${code}`),
  ontologyEnhanced: (code: string, days?: number) =>
    api.post(`/prediction/ontology-enhanced?stock_code=${code}`, null, { params: { days } }),
  getPriceData: (code: string, limit?: number) =>
    api.get('/prediction/price-data', { params: { stock_code: code, limit } }),
  getRisingStocks: (days?: number, minConfidence?: number, limit?: number) =>
    api.get('/prediction/rising-stars', { params: { days, min_confidence: minConfidence, limit } }),
}

// 推理 API
export const reasoningApi = {
  traceChain: (eventId: string, maxDepth?: number, includeCompetition?: boolean) =>
    api.post('/reasoning/trace-chain', null, {
      params: { event_id: eventId, max_depth: maxDepth, include_competition: includeCompetition }
    }),
  getChains: (code: string, days?: number) =>
    api.get(`/reasoning/chains/${code}`, { params: { days } }),
  validate: (code: string, prediction: string) =>
    api.post('/reasoning/validate', null, { params: { stock_code: code, prediction } }),
  getImpact: (code: string, days?: number) =>
    api.get(`/reasoning/impact/${code}`, { params: { days } }),
  classifyEvent: (text: string) =>
    api.post('/reasoning/classify-event', null, { params: { event_text: text } }),
}

// 调度器 API
export const schedulerApi = {
  getStatus: () => api.get('/scheduler/status'),
  getTasks: () => api.get('/scheduler/tasks'),
  triggerTask: (taskKey: string) => api.post(`/scheduler/trigger/${taskKey}`),
  getTaskLogs: (taskKey: string, limit?: number) =>
    api.get(`/scheduler/logs/${taskKey}`, { params: { limit } }),
  getCachedRisingStocks: () => api.get('/scheduler/cache/daily-rising'),
}

// 采集器 API
export const collectorApi = {
  getStatus: () => api.get('/collectors/status'),
  collectMarketData: (codes?: string[]) =>
    api.post('/collectors/market/collect', { stock_codes: codes }),
  collectStockList: () => api.post('/collectors/market/stock-list'),
  collectNews: (keyword?: string, code?: string) =>
    api.post('/collectors/news/collect', { keyword, stock_code: code }),
}

// 龙头战法 API
export const dragonApi = {
  // 获取龙头股列表
  getDragonStocks: (industryCode?: string) =>
    api.get('/dragon/stocks', { params: { industry_code: industryCode } }),

  // 获取高护城河企业
  getHighMoatCompanies: (minMoat?: number) =>
    api.get('/dragon/stocks/high-moat', { params: { min_moat: minMoat } }),

  // 获取企业完整信息
  getCompanyDetail: (stockCode: string) =>
    api.get(`/dragon/company/${stockCode}`),

  // 获取供应链关系
  getSupplyChain: (stockCode: string, direction?: 'up' | 'down' | 'all') =>
    api.get(`/dragon/company/${stockCode}/supply-chain`, { params: { direction } }),

  // 获取企业关联图谱
  getCompanyGraph: (stockCode: string, depth?: number) =>
    api.get(`/dragon/company/${stockCode}/graph`, { params: { depth } }),

  // 获取股票日K线数据
  getDailyData: (stockCode: string, startDate?: string, endDate?: string, limit?: number) =>
    api.get(`/dragon/market/${stockCode}/daily`, {
      params: { start_date: startDate, end_date: endDate, limit }
    }),

  // 获取最近N天股票数据
  getRecentData: (stockCode: string, days?: number) =>
    api.get(`/dragon/market/${stockCode}/recent`, { params: { days } }),

  // 获取价格统计
  getPriceStatistics: (stockCode: string, startDate: string, endDate: string) =>
    api.get(`/dragon/market/${stockCode}/statistics`, {
      params: { start_date: startDate, end_date: endDate }
    }),

  // 获取移动平均线
  getMovingAverage: (stockCode: string, window?: number, startDate?: string, endDate?: string) =>
    api.get(`/dragon/market/${stockCode}/ma`, {
      params: { window, start_date: startDate, end_date: endDate }
    }),

  // 获取所有概念板块
  getAllConcepts: () => api.get('/dragon/concepts'),

  // 获取概念成分股
  getConceptStocks: (conceptCode: string) =>
    api.get(`/dragon/concept/${conceptCode}/stocks`),

  // 获取股票所属概念
  getStockConcepts: (stockCode: string) =>
    api.get(`/dragon/company/${stockCode}/concepts`),

  // 获取市场事件
  getAllEvents: (limit?: number) =>
    api.get('/dragon/events', { params: { limit } }),

  // 获取事件影响的股票
  getEventImpacts: (eventId: string) =>
    api.get(`/dragon/event/${eventId}/impacts`),

  // 获取影响股票的事件
  getStockEvents: (stockCode: string) =>
    api.get(`/dragon/company/${stockCode}/events`),

  // 获取龙头战法综合分析
  getDragonAnalysis: () => api.get('/dragon/analysis'),
}

export default api
