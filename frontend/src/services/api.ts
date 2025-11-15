import axios from 'axios';

const API_BASE_URL = (window as any).REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  context_length: number;
  pricing?: {
    input: number;
    output: number;
  };
}

export interface AIStatus {
  provider: string;
  status: string;
  default_model: string;
  available_models: string[];
}

export interface AIUsageStats {
  period: {
    year: number;
    month: number;
    month_year: string;
  };
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_requests: number;
  unique_models: number;
  model_breakdown: Array<{
    model: string;
    tokens: number;
    requests: number;
  }>;
}

export interface AvitoChatSettings {
  id: number;
  chat_id: string;
  customer_id?: number;
  ai_enabled: boolean;
  ai_model?: string;
  ai_temperature: number;
  notifications_enabled: boolean;
  message_count: number;
  last_message_at?: string;
  last_ai_response_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AutomationProcess {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  is_active: boolean;
  stages_count: number;
}

export interface SystemSettings {
  status: string;
  service?: string;
}

class ApiService {
  // AI Settings
  async getAIModels() {
    const response = await api.get<AIModel[]>('/models');
    return response.data;
  }

  async getAIStatus() {
    const response = await api.get<AIStatus>('/status');
    return response.data;
  }

  async getAIUsage() {
    const response = await api.get<AIUsageStats>('/usage/monthly');
    return response.data;
  }

  async updateAISettings(settings: {
    default_model?: string;
    temperature?: number;
    max_tokens?: number;
    api_key?: string;
  }) {
    const response = await api.put('/settings/ai', settings);
    return response.data;
  }

  // AI Chat functions
  async analyzeIntent(message: string) {
    const response = await api.post('/analyze-intent', { message });
    return response.data;
  }

  async generateResponse(message: string, context?: any) {
    const response = await api.post('/generate-response', { message, context });
    return response.data;
  }

  async chat(message: string, conversation_id?: string) {
    const response = await api.post('/chat', { message, conversation_id });
    return response.data;
  }

  async getUsageHistory() {
    const response = await api.get('/usage/history');
    return response.data;
  }

  // Avito Settings
  async getAvitoChats() {
    const response = await api.get('/avito/messenger/v1/accounts/1/chats');
    return response.data;
  }

  async updateAvitoChatSettings(chatId: string, settings: Partial<AvitoChatSettings>) {
    const response = await api.put(`/avito/messenger/v1/accounts/1/chats/${chatId}`, settings);
    return response.data;
  }

  async getAvitoStats() {
    const response = await api.get('/avito/messenger/stats');
    return response.data;
  }

  // Automation Settings
  async getAutomationProcesses() {
    const response = await api.get<AutomationProcess[]>('/automation/processes');
    return response.data;
  }

  async createAutomationProcess(process: Omit<AutomationProcess, 'id'>) {
    const response = await api.post('/automation/processes', process);
    return response.data;
  }

  async updateAutomationProcess(id: number, process: Partial<AutomationProcess>) {
    const response = await api.put(`/automation/processes/${id}`, process);
    return response.data;
  }

  async getAutomationAnalytics() {
    const response = await api.get('/automation/analytics');
    return response.data;
  }

  // System Settings
  async getSystemHealth() {
    const response = await api.get<SystemSettings>('/health');
    return response.data;
  }

  async getSystemSettings() {
    const response = await api.get('/settings/system');
    return response.data;
  }

  async updateSystemSettings(settings: any) {
    const response = await api.put('/settings/system', settings);
    return response.data;
  }

  // Authentication
  async register(credentials: { username: string; password: string; email?: string }) {
    const response = await api.post('/auth/register', credentials);
    return response.data;
  }

  async login(credentials: { email: string; password: string }) {
    const response = await api.post('/auth/login/json', credentials);
    const { access_token } = response.data;
    localStorage.setItem('auth_token', access_token);
    return response.data;
  }

  async logout() {
    localStorage.removeItem('auth_token');
  }

  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  }

  // Customers
  async getCustomers() {
    const response = await api.get('/customers/');
    return response.data;
  }

  async createCustomer(customerData: any) {
    const response = await api.post('/customers/', customerData);
    return response.data;
  }

  async getCustomer(customerId: number) {
    const response = await api.get(`/customers/${customerId}`);
    return response.data;
  }

  async updateCustomer(customerId: number, customerData: any) {
    const response = await api.put(`/customers/${customerId}`, customerData);
    return response.data;
  }

  async deleteCustomer(customerId: number) {
    const response = await api.delete(`/customers/${customerId}`);
    return response.data;
  }

  async getCustomerStats(customerId: number) {
    const response = await api.get(`/customers/${customerId}/stats`);
    return response.data;
  }

  async searchCustomers(query: string) {
    const response = await api.get(`/customers/search/?q=${encodeURIComponent(query)}`);
    return response.data;
  }

  // Orders
  async getOrders() {
    const response = await api.get('/orders/');
    return response.data;
  }

  async createOrder(orderData: any) {
    const response = await api.post('/orders/', orderData);
    return response.data;
  }

  async getOrder(orderId: number) {
    const response = await api.get(`/orders/${orderId}`);
    return response.data;
  }

  async updateOrder(orderId: number, orderData: any) {
    const response = await api.put(`/orders/${orderId}`, orderData);
    return response.data;
  }

  async deleteOrder(orderId: number) {
    const response = await api.delete(`/orders/${orderId}`);
    return response.data;
  }

  async getOrderProductionProgress(orderId: number) {
    const response = await api.get(`/orders/${orderId}/production-progress`);
    return response.data;
  }

  async startProductionStep(orderId: number, stepId: number) {
    const response = await api.post(`/orders/${orderId}/production-steps/${stepId}/start`);
    return response.data;
  }

  async completeProductionStep(orderId: number, stepId: number) {
    const response = await api.post(`/orders/${orderId}/production-steps/${stepId}/complete`);
    return response.data;
  }

  async getOverdueProduction() {
    const response = await api.get('/orders/production/overdue');
    return response.data;
  }

  // Tasks
  async getTasks() {
    const response = await api.get('/tasks/');
    return response.data;
  }

  async createTask(taskData: any) {
    const response = await api.post('/tasks/', taskData);
    return response.data;
  }

  async getTask(taskId: number) {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  }

  async updateTask(taskId: number, taskData: any) {
    const response = await api.put(`/tasks/${taskId}`, taskData);
    return response.data;
  }

  async deleteTask(taskId: number) {
    const response = await api.delete(`/tasks/${taskId}`);
    return response.data;
  }

  async completeTask(taskId: number) {
    const response = await api.post(`/tasks/${taskId}/complete`);
    return response.data;
  }

  // Email
  async sendEmail(data: { to: string; subject: string; body: string; template?: string }) {
    const response = await api.post('/email/send', data);
    return response.data;
  }

  async sendTemplateEmail(data: { to: string; template: string; variables: Record<string, any> }) {
    const response = await api.post('/email/send-template', data);
    return response.data;
  }

  async testEmail(data: { to: string }) {
    const response = await api.post('/email/test', data);
    return response.data;
  }

  async getEmailTemplates() {
    const response = await api.get('/email/templates');
    return response.data;
  }

  async getEmailStatus(messageId: string) {
    const response = await api.get(`/email/status?message_id=${messageId}`);
    return response.data;
  }

  async getEmailServiceStatus() {
    const response = await api.get('/email/service-status');
    return response.data;
  }

  // Telegram
  async initializeTelegram() {
    const response = await api.post('/telegram/initialize');
    return response.data;
  }

  async stopTelegram() {
    const response = await api.post('/telegram/stop');
    return response.data;
  }

  async sendTelegramMessage(chatId: string, message: string) {
    const response = await api.post('/telegram/send-message', { chat_id: chatId, message });
    return response.data;
  }

  async getTelegramStats() {
    const response = await api.get('/telegram/stats');
    return response.data;
  }

  async getTelegramChats() {
    const response = await api.get('/telegram/chats');
    return response.data;
  }

  async getTelegramChat(chatId: string) {
    const response = await api.get(`/telegram/chat/${chatId}`);
    return response.data;
  }

  async linkTelegramChatToCustomer(chatId: string, customerId: number) {
    const response = await api.post(`/telegram/chat/${chatId}/link-customer`, { customer_id: customerId });
    return response.data;
  }

  async unlinkTelegramChatFromCustomer(chatId: string) {
    const response = await api.post(`/telegram/chat/${chatId}/unlink-customer`);
    return response.data;
  }

  async getTelegramCommunications() {
    const response = await api.get('/telegram/communications');
    return response.data;
  }

  async setTelegramWebhook(url: string) {
    const response = await api.post('/telegram/set-webhook', { url });
    return response.data;
  }

  async deleteTelegramWebhook() {
    const response = await api.post('/telegram/delete-webhook');
    return response.data;
  }

  // Avito Items and Management
  async getAvitoItems() {
    const response = await api.get('/avito/items');
    return response.data;
  }

  async getAvitoItem(itemId: number) {
    const response = await api.get(`/avito/items/${itemId}`);
    return response.data;
  }

  async getAvitoItemPerformance(itemId: number) {
    const response = await api.get(`/avito/items/${itemId}/performance`);
    return response.data;
  }

  async getAvitoItemStats() {
    const response = await api.get('/avito/items/stats');
    return response.data;
  }

  async getAvitoAnalytics() {
    const response = await api.get('/avito/analytics');
    return response.data;
  }

  async getAvitoItemVasPrices(itemId: number) {
    const response = await api.get(`/avito/items/${itemId}/vas-prices`);
    return response.data;
  }

  async getAvitoItemVas(itemId: number) {
    const response = await api.get(`/avito/items/${itemId}/vas`);
    return response.data;
  }

  async updateAvitoItemVas(itemId: number, vasData: any) {
    const response = await api.post(`/avito/items/${itemId}/vas`, vasData);
    return response.data;
  }

  async updateAvitoItemPrice(itemId: number, price: number) {
    const response = await api.put(`/avito/items/${itemId}/price`, { price });
    return response.data;
  }

  async optimizeAvitoItemPrice(itemId: number) {
    const response = await api.post(`/avito/items/${itemId}/optimize-price`);
    return response.data;
  }

  async promoteAvitoItem(itemId: number, promotionData: any) {
    const response = await api.post(`/avito/items/${itemId}/promote`, promotionData);
    return response.data;
  }

  async getAvitoCallsStats() {
    const response = await api.get('/avito/calls/stats');
    return response.data;
  }

  // Avito Messenger
  async toggleAvitoChatAi(chatId: string, enabled: boolean) {
    const response = await api.post(`/avito/messenger/chats/${chatId}/toggle-ai`, { enabled });
    return response.data;
  }

  async getAvitoChatMessages(userId: string, chatId: string) {
    const response = await api.get(`/avito/messenger/v1/accounts/${userId}/chats/${chatId}/messages`);
    return response.data;
  }

  // Avito Background Tasks
  async syncAvitoChats() {
    const response = await api.post('/avito/background/sync-chats');
    return response.data;
  }

  async bulkSendAvitoMessages(data: any) {
    const response = await api.post('/avito/background/bulk-send', data);
    return response.data;
  }

  async updateAvitoPerformance() {
    const response = await api.post('/avito/background/update-performance');
    return response.data;
  }

  async cleanupAvito() {
    const response = await api.post('/avito/background/cleanup');
    return response.data;
  }

  async getAvitoBackgroundTasks() {
    const response = await api.get('/avito/background/tasks');
    return response.data;
  }

  async getAvitoBackgroundTask(taskId: string) {
    const response = await api.get(`/avito/background/tasks/${taskId}`);
    return response.data;
  }

  // Automation Events
  async triggerAutomationEvent(entityType: string, eventType: string, entityId: number) {
    const response = await api.post(`/automation/events/${entityType}/${eventType}`, { entity_id: entityId });
    return response.data;
  }

  async moveToAutomationStage(entityType: string, entityId: number, stageId: number) {
    const response = await api.post(`/automation/move-to-stage/${entityType}/${entityId}/${stageId}`);
    return response.data;
  }

  // Automation Stages and Triggers
  async getAutomationStages() {
    const response = await api.get('/automation/stages/');
    return response.data;
  }

  async getAutomationStage(stageId: number) {
    const response = await api.get(`/automation/stages/${stageId}`);
    return response.data;
  }

  async getAutomationTriggers() {
    const response = await api.get('/automation/triggers/');
    return response.data;
  }

  async getAutomationTrigger(triggerId: number) {
    const response = await api.get(`/automation/triggers/${triggerId}`);
    return response.data;
  }

  // Automation Robots
  async getAutomationRobots() {
    const response = await api.get('/automation/robots/');
    return response.data;
  }

  async getAutomationRobot(robotId: number) {
    const response = await api.get(`/automation/robots/${robotId}`);
    return response.data;
  }

  // Automation AI
  async generateAutomationChain(processId: number) {
    const response = await api.post('/automation/ai/generate-chain', { process_id: processId });
    return response.data;
  }

  async optimizeAutomationChain(processId: number) {
    const response = await api.post(`/automation/ai/optimize-chain/${processId}`);
    return response.data;
  }

  async suggestAutomationImprovements() {
    const response = await api.get('/automation/ai/suggest-improvements');
    return response.data;
  }

  // Automation Analytics
  async getAutomationExecutionsAnalytics() {
    const response = await api.get('/automation/analytics/executions');
    return response.data;
  }

  async getAutomationRobotsAnalytics() {
    const response = await api.get('/automation/analytics/robots');
    return response.data;
  }

  async getAutomationActionsAnalytics() {
    const response = await api.get('/automation/analytics/actions');
    return response.data;
  }

  async getAutomationErrorsAnalytics() {
    const response = await api.get('/automation/analytics/errors');
    return response.data;
  }

  async getAutomationProcessesAnalytics() {
    const response = await api.get('/automation/analytics/processes');
    return response.data;
  }

  async getAutomationHourlyAnalytics() {
    const response = await api.get('/automation/analytics/hourly');
    return response.data;
  }

  // Root endpoint
  // AI Manager - Prompts
  async getPrompts() {
    const response = await api.get('/ai-manager/prompts');
    return response.data;
  }

  async getActivePrompts() {
    const response = await api.get('/ai-manager/prompts/active');
    return response.data;
  }

  async createPrompt(promptData: any) {
    const response = await api.post('/ai-manager/prompts', promptData);
    return response.data;
  }

  async updatePrompt(promptId: number, promptData: any) {
    const response = await api.put(`/ai-manager/prompts/${promptId}`, promptData);
    return response.data;
  }

  async deletePrompt(promptId: number) {
    const response = await api.delete(`/ai-manager/prompts/${promptId}`);
    return response.data;
  }

  async togglePromptStatus(promptId: number) {
    const response = await api.patch(`/ai-manager/prompts/${promptId}/toggle`);
    return response.data;
  }

  // AI Manager - Services
  async getServices() {
    const response = await api.get('/ai-manager/services');
    return response.data;
  }

  async getActiveServices() {
    const response = await api.get('/ai-manager/services/active');
    return response.data;
  }

  async createService(serviceData: any) {
    const response = await api.post('/ai-manager/services', serviceData);
    return response.data;
  }

  async updateService(serviceId: number, serviceData: any) {
    const response = await api.put(`/ai-manager/services/${serviceId}`, serviceData);
    return response.data;
  }

  async deleteService(serviceId: number) {
    const response = await api.delete(`/ai-manager/services/${serviceId}`);
    return response.data;
  }

  async toggleServiceStatus(serviceId: number) {
    const response = await api.patch(`/ai-manager/services/${serviceId}/toggle`);
    return response.data;
  }

  async getServiceCategories() {
    const response = await api.get('/ai-manager/services/categories');
    return response.data;
  }

  // AI Manager - Products
  async getProducts() {
    const response = await api.get('/ai-manager/products');
    return response.data;
  }

  async getActiveProducts() {
    const response = await api.get('/ai-manager/products/active');
    return response.data;
  }

  async getInStockProducts() {
    const response = await api.get('/ai-manager/products/in-stock');
    return response.data;
  }

  async createProduct(productData: any) {
    const response = await api.post('/ai-manager/products', productData);
    return response.data;
  }

  async updateProduct(productId: number, productData: any) {
    const response = await api.put(`/ai-manager/products/${productId}`, productData);
    return response.data;
  }

  async updateProductStock(productId: number, stockQuantity: number) {
    const response = await api.put(`/ai-manager/products/${productId}/stock`, { stock_quantity: stockQuantity });
    return response.data;
  }

  async deleteProduct(productId: number) {
    const response = await api.delete(`/ai-manager/products/${productId}`);
    return response.data;
  }

  async toggleProductStatus(productId: number) {
    const response = await api.patch(`/ai-manager/products/${productId}/toggle`);
    return response.data;
  }

  async getProductCategories() {
    const response = await api.get('/ai-manager/products/categories');
    return response.data;
  }

  async getLowStockProducts(threshold: number = 10) {
    const response = await api.get(`/ai-manager/products/low-stock?threshold=${threshold}`);
    return response.data;
  }

  async getOutOfStockProducts() {
    const response = await api.get('/ai-manager/products/out-of-stock');
    return response.data;
  }

  async getRoot() {
    const response = await api.get('/');
    return response.data;
  }
}

export const apiService = new ApiService();
export default api;
