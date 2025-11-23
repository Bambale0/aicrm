/* eslint-disable no-restricted-globals */

import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Button from '../components/ui/Button';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ChartBarIcon,
  WrenchScrewdriverIcon
} from '@heroicons/react/24/outline';

interface Campaign {
  id: number;
  name: string;
  description: string;
  organization_id: number;
  is_active: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

interface CampaignAISettings {
  id: number;
  campaign_id: number;
  default_model: string;
  provider: string;
  temperature: number;
  max_tokens: number;
  auto_reply_enabled: boolean;
  custom_prompt: string;
  target_audience: string;
  brand_voice: string;
  daily_token_limit: number;
  monthly_token_limit: number;
}

function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Campaign | null>(null);
  const [aiSettingsEditing, setAiSettingsEditing] = useState<CampaignAISettings | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    organization_id: 1
  });

  const [aiSettingsForm, setAiSettingsForm] = useState({
    default_model: 'deepseek-chat',
    provider: 'openrouter',
    temperature: 0.7,
    max_tokens: 4000,
    auto_reply_enabled: false,
    custom_prompt: '',
    target_audience: '',
    brand_voice: '',
    daily_token_limit: 10000,
    monthly_token_limit: 100000
  });

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      const response = await apiService.getCampaigns({ per_page: 50 });
      setCampaigns(response.campaigns || []);
    } catch (error) {
      console.error('Failed to load campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) return;

    setCreating(true);
    try {
      await apiService.createCampaign({
        ...formData,
        status: 'draft',
        is_active: true
      });
      await loadCampaigns();
      setFormData({ name: '', description: '', organization_id: 1 });
      setCreating(false);
    } catch (error) {
      console.error('Failed to create campaign:', error);
      setCreating(false);
    }
  };

  const handleUpdate = async () => {
    if (!editing || !formData.name.trim()) return;

    try {
      await apiService.updateCampaign(editing.id, {
        name: formData.name,
        description: formData.description,
        organization_id: formData.organization_id
      });
      await loadCampaigns();
      setEditing(null);
      setFormData({ name: '', description: '', organization_id: 1 });
    } catch (error) {
      console.error('Failed to update campaign:', error);
    }
  };

  const handleDelete = async (campaignId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту кампанию?')) return;

    try {
      await apiService.deleteCampaign(campaignId);
      await loadCampaigns();
    } catch (error) {
      console.error('Failed to delete campaign:', error);
    }
  };

  const handleEditAI = async (campaignId: number) => {
    try {
      const response = await apiService.getCampaignAISettings(campaignId);
      setAiSettingsEditing(response);
      setAiSettingsForm({
        default_model: response.default_model || 'deepseek-chat',
        provider: response.provider || 'openrouter',
        temperature: response.temperature || 0.7,
        max_tokens: response.max_tokens || 4000,
        auto_reply_enabled: response.auto_reply_enabled || false,
        custom_prompt: response.custom_prompt || '',
        target_audience: response.target_audience || '',
        brand_voice: response.brand_voice || '',
        daily_token_limit: response.daily_token_limit || 10000,
        monthly_token_limit: response.monthly_token_limit || 100000
      });
    } catch (error) {
      console.error('Failed to load AI settings:', error);
    }
  };

  const handleSaveAI = async () => {
    if (!aiSettingsEditing) return;

    try {
      await apiService.updateCampaignAISettings(aiSettingsEditing.campaign_id, aiSettingsForm);
      setAiSettingsEditing(null);
      await loadCampaigns();
    } catch (error) {
      console.error('Failed to save AI settings:', error);
    }
  };

  const startEdit = (campaign: Campaign) => {
    setEditing(campaign);
    setFormData({
      name: campaign.name,
      description: campaign.description,
      organization_id: campaign.organization_id
    });
  };

  const cancelEdit = () => {
    setEditing(null);
    setFormData({ name: '', description: '', organization_id: 1 });
  };

  const cancelAiEdit = () => {
    setAiSettingsEditing(null);
    setAiSettingsForm({
      default_model: 'deepseek-chat',
      provider: 'openrouter',
      temperature: 0.7,
      max_tokens: 4000,
      auto_reply_enabled: false,
      custom_prompt: '',
      target_audience: '',
      brand_voice: '',
      daily_token_limit: 10000,
      monthly_token_limit: 100000
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-van-gogh-ultramarine"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-van-gogh-starry-night-blue">Кампании</h1>
          <p className="text-van-gogh-chrome-green mt-2 text-sm sm:text-base">Управление маркетинговыми кампаниями</p>
        </div>
        <Button
          onClick={() => setCreating(true)}
          variant="primary"
          className="flex items-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Создать кампанию
        </Button>
      </div>

      {/* Create Form */}
      {(creating || editing) && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-van-gogh-starry-night-blue">
              {editing ? 'Редактировать кампанию' : 'Создать новую кампанию'}
            </h2>
            <button
              onClick={editing ? cancelEdit : () => setCreating(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Название кампании
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                placeholder="Введите название кампании..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Описание
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                rows={3}
                placeholder="Введите описание кампании..."
              />
            </div>

            <div className="flex justify-end space-x-3">
              <Button
                onClick={editing ? handleUpdate : handleCreate}
                variant="primary"
                loading={editing ? false : creating}
              >
                {editing ? 'Сохранить изменения' : 'Создать кампанию'}
              </Button>
              <Button
                onClick={editing ? cancelEdit : () => setCreating(false)}
                variant="secondary"
              >
                Отмена
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* AI Settings Form */}
      {aiSettingsEditing && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-van-gogh-starry-night-blue">
              Настройки AI для кампании
            </h2>
            <button
              onClick={cancelAiEdit}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Модель AI
              </label>
              <select
                value={aiSettingsForm.default_model}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, default_model: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
              >
                <option value="deepseek-chat">DeepSeek Chat</option>
                <option value="kimi-k2">Kimi K2</option>
                <option value="gpt-4">GPT-4</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Провайдер
              </label>
              <select
                value={aiSettingsForm.provider}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, provider: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
              >
                <option value="openrouter">OpenRouter</option>
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Температура (0.1-2.0)
              </label>
              <input
                type="number"
                min="0.1"
                max="2.0"
                step="0.1"
                value={aiSettingsForm.temperature}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, temperature: parseFloat(e.target.value) })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Максимум токенов
              </label>
              <input
                type="number"
                value={aiSettingsForm.max_tokens}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, max_tokens: parseInt(e.target.value) })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Автоответы
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={aiSettingsForm.auto_reply_enabled}
                  onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, auto_reply_enabled: e.target.checked })}
                  className="mr-2"
                />
                Включить автоответы на сообщения кампании
              </label>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Целевая аудитория
              </label>
              <input
                type="text"
                value={aiSettingsForm.target_audience}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, target_audience: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                placeholder="Опишите целевую аудиторию..."
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Стиль общения (brand voice)
              </label>
              <input
                type="text"
                value={aiSettingsForm.brand_voice}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, brand_voice: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                placeholder="Например: дружелюбный, профессиональный, энергичный..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Дневной лимит токенов
              </label>
              <input
                type="number"
                value={aiSettingsForm.daily_token_limit}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, daily_token_limit: parseInt(e.target.value) })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Месячный лимит токенов
              </label>
              <input
                type="number"
                value={aiSettingsForm.monthly_token_limit}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, monthly_token_limit: parseInt(e.target.value) })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-van-gogh-chrome-green mb-1">
                Промпт кампании
              </label>
              <textarea
                value={aiSettingsForm.custom_prompt}
                onChange={(e) => setAiSettingsForm({ ...aiSettingsForm, custom_prompt: e.target.value })}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-van-gogh-ultramarine focus:border-transparent"
                rows={4}
                placeholder="Дополнительный промпт для этой кампании..."
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 mt-6">
            <Button onClick={handleSaveAI} variant="primary">
              Сохранить AI настройки
            </Button>
            <Button onClick={cancelAiEdit} variant="secondary">
              Отмена
            </Button>
          </div>
        </div>
      )}

      {/* Campaigns List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {campaigns.map((campaign) => (
          <div key={campaign.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-semibold text-van-gogh-starry-night-blue mb-1">
                  {campaign.name}
                </h3>
                <p className="text-sm text-van-gogh-chrome-green line-clamp-2">
                  {campaign.description}
                </p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleEditAI(campaign.id)}
                  className="p-2 text-van-gogh-ultramarine hover:bg-van-gogh-ultramarine/10 rounded-lg"
                  title="AI настройки"
                >
                  <WrenchScrewdriverIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => startEdit(campaign)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                  title="Редактировать"
                >
                  <PencilIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(campaign.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  title="Удалить"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className={`px-2 py-1 rounded-full text-xs ${
                campaign.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : campaign.status === 'paused'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {campaign.status === 'active' ? 'Активна' :
                 campaign.status === 'paused' ? 'На паузе' : 'Черновик'}
              </span>
              <span className="text-gray-500">
                {new Date(campaign.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {campaigns.length === 0 && !loading && (
        <div className="text-center py-12">
          <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-van-gogh-chrome-green">Нет кампаний</h3>
          <p className="mt-1 text-sm text-gray-500">
            Создайте свою первую маркетинговую кампанию.
          </p>
          <div className="mt-6">
            <Button onClick={() => setCreating(true)} variant="primary">
              <PlusIcon className="w-5 h-5 mr-2" />
              Создать кампанию
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Campaigns;
