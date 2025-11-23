import axios from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? ''  // Use relative URLs in production (nginx will proxy to backend)
  : window.location.protocol + '//' + window.location.hostname + ':8000';

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
    const response = await api.get('/ai/models');
    const modelsData = response.data;
    // Convert dictionary to array if needed
    if (modelsData.models && typeof modelsData.models === 'object') {
      return Object.values(modelsData.models);
    }
    return Array.isArray(modelsData) ? modelsData : [];
  }

  async getAIStatus() {
    const response = await api.get<AIStatus>('/ai/status');
    return response.data;
  }

  async getAIUsage() {
    const response = await api.get<AIUsageStats>('/ai/usage/monthly');
    return response.data;
  }

  async getAIMonthlyUsage() {
    return this.getAIUsage();
  }

  async getAIUsageHistory(days: number = 30) {
    const response = await api.get('/ai/usage/history', { params: { days } });
    return response.data;
  }

  async updateAISettings(settings: any) {
    const response = await api.put('/ai/settings/ai', settings);
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
  async getAvitoSettings() {
    const response = await api.get('/avito/settings');
    return response.data;
  }

  async updateAvitoSettings(settings: any) {
    const response = await api.put('/avito/settings', settings);
    return response.data;
  }

  async testAvitoConnection() {
    const response = await api.post('/avito/settings/test-connection');
    return response.data;
  }

  async testAvitoWebhook() {
    const response = await api.post('/avito/settings/test-webhook');
    return response.data;
  }

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

  async completeProductionStep(orderId: number, stepId: number, data?: { actual_hours?: number; notes?: string }) {
    const response = await api.post(`/orders/${orderId}/production-steps/${stepId}/complete`, data);
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

  async getEmailStatus(messageId: string) {
    const response = await api.get(`/email/status?message_id=${messageId}`);
    return response.data;
  }

  async getEmailServiceStatus() {
    const response = await api.get('/email/status');
    return response.data;
  }

  async testIMAPConnection(settings: any) {
    const response = await api.post('/email/test-imap', settings);
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

  async createAutomationStage(stageData: any) {
    const response = await api.post('/automation/stages/', stageData);
    return response.data;
  }

  async updateAutomationStage(stageId: number, stageData: any) {
    const response = await api.put(`/automation/stages/${stageId}`, stageData);
    return response.data;
  }

  async deleteAutomationStage(stageId: number) {
    const response = await api.delete(`/automation/stages/${stageId}`);
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

  async createAutomationTrigger(triggerData: any) {
    const response = await api.post('/automation/triggers/', triggerData);
    return response.data;
  }

  async updateAutomationTrigger(triggerId: number, triggerData: any) {
    const response = await api.put(`/automation/triggers/${triggerId}`, triggerData);
    return response.data;
  }

  async deleteAutomationTrigger(triggerId: number) {
    const response = await api.delete(`/automation/triggers/${triggerId}`);
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

  // Users
  async getUsers() {
    const response = await api.get('/users/');
    return response.data;
  }

  async createUser(userData: any) {
    const response = await api.post('/users/', userData);
    return response.data;
  }

  async getUser(userId: number) {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: number, userData: any) {
    const response = await api.patch(`/users/${userId}`, userData);
    return response.data;
  }

  async deleteUser(userId: number) {
    const response = await api.delete(`/users/${userId}`);
    return response.data;
  }

  // Communications
  async getCommunications(params?: {
    skip?: number;
    limit?: number;
    channel?: string;
    customer_id?: number;
    order_id?: number;
    direction?: string;
    sentiment?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value.toString());
        }
      });
    }
    const response = await api.get(`/communications/?${queryParams.toString()}`);
    return response.data;
  }

  async getCommunication(communicationId: number) {
    const response = await api.get(`/communications/${communicationId}`);
    return response.data;
  }

  async createCommunication(communicationData: any) {
    const response = await api.post('/communications/', communicationData);
    return response.data;
  }

  async updateCommunication(communicationId: number, communicationData: any) {
    const response = await api.put(`/communications/${communicationId}`, communicationData);
    return response.data;
  }

  async deleteCommunication(communicationId: number) {
    const response = await api.delete(`/communications/${communicationId}`);
    return response.data;
  }

  async searchCommunications(searchData: any) {
    const response = await api.post('/communications/search', searchData);
    return response.data;
  }

  async getCommunicationStats(params?: {
    channel?: string;
    customer_id?: number;
    date_from?: string;
    date_to?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value.toString());
        }
      });
    }
    const response = await api.get(`/communications/stats/summary?${queryParams.toString()}`);
    return response.data;
  }

  // Email Management
  async getEmailMessages(folder: string = 'INBOX', limit: number = 50, offset: number = 0) {
    const response = await api.get(`/email/messages?folder=${folder}&limit=${limit}&offset=${offset}`);
    return response.data;
  }

  async markEmailsAsRead(data: { message_ids: string[]; folder: string }) {
    const response = await api.post('/email/mark-read', data);
    return response.data;
  }

  async deleteEmails(data: { message_ids: string[]; folder: string }) {
    const response = await api.post('/email/delete', data);
    return response.data;
  }

  async getEmailTemplates() {
    const response = await api.get('/email/templates');
    return response.data;
  }

  async getEmailSettings() {
    const response = await api.get('/email/settings');
    return response.data;
  }

  async saveEmailSettings(settings: any) {
    const response = await api.post('/email/settings', settings);
    return response.data;
  }

  async testSMTPConnection(settings: any) {
    const response = await api.post('/email/test-smtp', settings);
    return response.data;
  }

  async getEmailStats() {
    const response = await api.get('/email/stats');
    return response.data;
  }
}

export const apiService = new ApiService();
export default api;
