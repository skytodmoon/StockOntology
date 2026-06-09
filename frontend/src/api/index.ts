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

export default api
