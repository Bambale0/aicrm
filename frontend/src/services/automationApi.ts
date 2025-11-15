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

// Types
export interface Process {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Stage {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  process_id: number;
  order_index: number;
  color?: string;
  is_active: boolean;
  created_at: string;
}

export interface Trigger {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  event_type: string;
  conditions?: any;
  target_stage_id: number;
  is_active: boolean;
  created_at: string;
}

export interface Robot {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  stage_id: number;
  is_active: boolean;
  created_at: string;
}

export interface RobotAction {
  id: number;
  robot_id: number;
  action_type: string;
  execution_order: number;
  config?: any;
  conditions?: any;
  delay_seconds: number;
  created_at: string;
}

export interface AutomationChainRequest {
  description: string;
  entity_type: string;
  complexity_level?: string;
}

export interface AutomationChainResponse {
  success: boolean;
  process?: Process;
  stages?: Stage[];
  triggers?: Trigger[];
  robots?: Robot[];
  error?: string;
}

class AutomationApiService {
  // Processes CRUD
  async getProcesses(params?: {
    skip?: number;
    limit?: number;
    entity_type?: string;
  }) {
    const response = await api.get<Process[]>('/automation/processes/', { params });
    return response.data;
  }

  async createProcess(process: Omit<Process, 'id' | 'created_at' | 'updated_at'>) {
    const response = await api.post<Process>('/automation/processes/', process);
    return response.data;
  }

  async getProcess(processId: number) {
    const response = await api.get<Process>(`/automation/processes/${processId}`);
    return response.data;
  }

  async updateProcess(processId: number, process: Partial<Process>) {
    const response = await api.put<Process>(`/automation/processes/${processId}`, process);
    return response.data;
  }

  async deleteProcess(processId: number) {
    const response = await api.delete(`/automation/processes/${processId}`);
    return response.data;
  }

  // Stages CRUD
  async getStages(params?: {
    process_id?: number;
    entity_type?: string;
    skip?: number;
    limit?: number;
  }) {
    const response = await api.get<Stage[]>('/automation/stages/', { params });
    return response.data;
  }

  async createStage(stage: Omit<Stage, 'id' | 'created_at'>) {
    const response = await api.post<Stage>('/automation/stages/', stage);
    return response.data;
  }

  async getStage(stageId: number) {
    const response = await api.get<Stage>(`/automation/stages/${stageId}`);
    return response.data;
  }

  async updateStage(stageId: number, stage: Partial<Stage>) {
    const response = await api.put<Stage>(`/automation/stages/${stageId}`, stage);
    return response.data;
  }

  async deleteStage(stageId: number) {
    const response = await api.delete(`/automation/stages/${stageId}`);
    return response.data;
  }

  // Triggers CRUD
  async getTriggers(params?: {
    entity_type?: string;
    event_type?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) {
    const response = await api.get<Trigger[]>('/automation/triggers/', { params });
    return response.data;
  }

  async createTrigger(trigger: Omit<Trigger, 'id' | 'created_at'>) {
    const response = await api.post<Trigger>('/automation/triggers/', trigger);
    return response.data;
  }

  async getTrigger(triggerId: number) {
    const response = await api.get<Trigger>(`/automation/triggers/${triggerId}`);
    return response.data;
  }

  async updateTrigger(triggerId: number, trigger: Partial<Trigger>) {
    const response = await api.put<Trigger>(`/automation/triggers/${triggerId}`, trigger);
    return response.data;
  }

  async deleteTrigger(triggerId: number) {
    const response = await api.delete(`/automation/triggers/${triggerId}`);
    return response.data;
  }

  // Robots CRUD
  async getRobots(params?: {
    entity_type?: string;
    stage_id?: number;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) {
    const response = await api.get<Robot[]>('/automation/robots/', { params });
    return response.data;
  }

  async createRobot(robot: Omit<Robot, 'id' | 'created_at'>) {
    const response = await api.post<Robot>('/automation/robots/', robot);
    return response.data;
  }

  async getRobot(robotId: number) {
    const response = await api.get<Robot>(`/automation/robots/${robotId}`);
    return response.data;
  }

  async updateRobot(robotId: number, robot: Partial<Robot>) {
    const response = await api.put<Robot>(`/automation/robots/${robotId}`, robot);
    return response.data;
  }

  async deleteRobot(robotId: number) {
    const response = await api.delete(`/automation/robots/${robotId}`);
    return response.data;
  }

  // Events
  async fireAutomationEvent(entityType: string, eventType: string, entityId: number, eventData?: any) {
    const response = await api.post(`/automation/events/${entityType}/${eventType}`, {
      entity_id: entityId,
      ...eventData
    });
    return response.data;
  }

  async moveToStage(entityType: string, entityId: number, stageId: number) {
    const response = await api.post(`/automation/move-to-stage/${entityType}/${entityId}/${stageId}`);
    return response.data;
  }

  // AI Functions
  async generateAutomationChain(request: AutomationChainRequest) {
    const response = await api.post<AutomationChainResponse>('/automation/ai/generate-chain', request);
    return response.data;
  }

  async optimizeAutomationChain(processId: number, optimizationGoal: string) {
    const response = await api.post(`/automation/ai/optimize-chain/${processId}`, null, {
      params: { optimization_goal: optimizationGoal }
    });
    return response.data;
  }

  async suggestImprovements(entityType?: string, analysisPeriodDays?: number) {
    const response = await api.post('/automation/ai/suggest-improvements', null, {
      params: {
        entity_type: entityType,
        analysis_period_days: analysisPeriodDays
      }
    });
    return response.data;
  }

  // Analytics
  async getExecutionStats(params?: {
    start_date?: string;
    end_date?: string;
    entity_type?: string;
  }) {
    const response = await api.get('/automation/analytics/executions', { params });
    return response.data;
  }

  async getRobotPerformance(params?: {
    robot_id?: number;
    start_date?: string;
    end_date?: string;
  }) {
    const response = await api.get('/automation/analytics/robots', { params });
    return response.data;
  }

  async getActionTypeStats(params?: {
    start_date?: string;
    end_date?: string;
  }) {
    const response = await api.get('/automation/analytics/actions', { params });
    return response.data;
  }

  async getErrorAnalysis(params?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) {
    const response = await api.get('/automation/analytics/errors', { params });
    return response.data;
  }

  async getProcessEfficiency(params?: {
    process_id?: number;
    start_date?: string;
    end_date?: string;
  }) {
    const response = await api.get('/automation/analytics/processes', { params });
    return response.data;
  }

  async getHourlyDistribution(params?: {
    start_date?: string;
    end_date?: string;
  }) {
    const response = await api.get('/automation/analytics/hourly', { params });
    return response.data;
  }
}

export const automationApi = new AutomationApiService();
export default automationApi;
