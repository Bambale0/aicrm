import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  ArrowPathIcon,
  BoltIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  Cog6ToothIcon,
  PencilIcon,
  PlayIcon,
  PlusIcon,
  TrashIcon,
  WrenchScrewdriverIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import api from '../services/api';

type TabKey = 'rules' | 'stages' | 'runs' | 'log';

interface OptionItem {
  value: any;
  label: string;
}

interface FieldSpec {
  path?: string;
  name?: string;
  label: string;
  type: string;
  required?: boolean;
  options?: OptionItem[];
  source?: string;
  supports_template?: boolean;
}

interface EntitySpec {
  value: string;
  label: string;
  description: string;
  fields: FieldSpec[];
}

interface EventSpec {
  value: string;
  label: string;
  description: string;
  entity_types: string[];
  event_fields: FieldSpec[];
}

interface ActionSpec {
  value: string;
  label: string;
  description: string;
  entity_types: string[];
  config_fields: FieldSpec[];
}

interface Catalog {
  entity_types: EntitySpec[];
  events: EventSpec[];
  actions: ActionSpec[];
  condition_operators: OptionItem[];
  workflow_statuses: OptionItem[];
  template_help?: { description: string; examples: string[] };
}

interface Process {
  id: number;
  name: string;
  description?: string;
  entity_type: string;
  is_active: boolean;
  stages_count: number;
  rules_count: number;
  instances_count: number;
}

interface Stage {
  id: number;
  process_id: number;
  name: string;
  description?: string;
  order_index: number;
  is_active: boolean;
}

interface Condition {
  field: string;
  operator: string;
  value: any;
  logical_operator: 'AND' | 'OR';
}

interface RuleAction {
  type: string;
  config: Record<string, any>;
}

interface Rule {
  id: number;
  process_id: number;
  name: string;
  description?: string;
  event_type: string;
  conditions: Condition[];
  actions: RuleAction[];
  priority: number;
  stop_after_match: boolean;
  is_active: boolean;
}

interface WorkflowInstance {
  id: number;
  process_id: number;
  name: string;
  status: string;
  current_stage_id?: number | null;
  current_stage_name?: string | null;
  variables: Record<string, any>;
  external_ref?: string | null;
  updated_at: string;
}

interface Execution {
  id: number;
  rule_id?: number | null;
  instance_id?: number | null;
  correlation_id: string;
  entity_type: string;
  entity_id: number;
  event_type: string;
  action_index?: number | null;
  status: string;
  duration_ms?: number | null;
  error?: string | null;
  created_at: string;
}

const emptyCatalog: Catalog = {
  entity_types: [],
  events: [],
  actions: [],
  condition_operators: [],
  workflow_statuses: [],
};

const emptyRule = {
  name: '',
  description: '',
  event_type: '',
  conditions: [] as Condition[],
  actions: [] as RuleAction[],
  priority: 100,
  stop_after_match: false,
};

export default function AutomationBoard() {
  const [catalog, setCatalog] = useState<Catalog>(emptyCatalog);
  const [summary, setSummary] = useState<any>({});
  const [processes, setProcesses] = useState<Process[]>([]);
  const [selectedProcessId, setSelectedProcessId] = useState<number | null>(null);
  const [stages, setStages] = useState<Stage[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [tab, setTab] = useState<TabKey>('rules');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(true);

  const [processForm, setProcessForm] = useState({ name: '', description: '', entity_type: '' });
  const [stageName, setStageName] = useState('');
  const [ruleForm, setRuleForm] = useState(emptyRule);
  const [editingRuleId, setEditingRuleId] = useState<number | null>(null);
  const [runForm, setRunForm] = useState({ name: '', variables: [{ key: '', value: '' }] });
  const [eventNames, setEventNames] = useState<Record<number, string>>({});
  const [eventPayloads, setEventPayloads] = useState<Record<number, { key: string; value: string }>>({});
  const [variableEdits, setVariableEdits] = useState<Record<number, { key: string; value: string }>>({});
  const [remoteOptions, setRemoteOptions] = useState<Record<string, OptionItem[]>>({});

  const selectedProcess = useMemo(
    () => processes.find((item) => item.id === selectedProcessId) || null,
    [processes, selectedProcessId],
  );

  const entitySpec = useMemo(
    () => catalog.entity_types.find((item) => item.value === selectedProcess?.entity_type) || null,
    [catalog.entity_types, selectedProcess?.entity_type],
  );

  const eventSpecs = useMemo(
    () =>
      catalog.events.filter(
        (item) => selectedProcess && item.entity_types.includes(selectedProcess.entity_type),
      ),
    [catalog.events, selectedProcess],
  );

  const actionSpecs = useMemo(
    () =>
      catalog.actions.filter(
        (item) => selectedProcess && item.entity_types.includes(selectedProcess.entity_type),
      ),
    [catalog.actions, selectedProcess],
  );

  const selectedEvent = eventSpecs.find((item) => item.value === ruleForm.event_type);

  const conditionFields = useMemo(() => {
    const fields = [...(entitySpec?.fields || []), ...(selectedEvent?.event_fields || [])];
    const seen = new Set<string>();
    return fields.filter((field) => {
      const key = field.path || '';
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [entitySpec, selectedEvent]);

  const loadProcessData = async (processId: number | null) => {
    if (!processId) {
      setStages([]);
      setRules([]);
      setInstances([]);
      setExecutions([]);
      return;
    }

    const process = processes.find((item) => item.id === processId);
    const requests: Array<Promise<any>> = [
      api.get('/automation/stages', { params: { process_id: processId } }),
      api.get('/automation/rules', { params: { process_id: processId } }),
      api.get('/automation/executions', { params: { process_id: processId, limit: 100 } }),
    ];

    if (process?.entity_type === 'workflow') {
      requests.push(api.get('/automation/instances', { params: { process_id: processId, limit: 100 } }));
    }

    const responses = await Promise.all(requests);
    setStages(responses[0].data);
    setRules(responses[1].data);
    setExecutions(responses[2].data);
    setInstances(process?.entity_type === 'workflow' ? responses[3]?.data || [] : []);
  };

  const load = async () => {
    setLoading(true);
    setNotice('');
    try {
      const [catalogResponse, summaryResponse, processesResponse] = await Promise.all([
        api.get('/automation/catalog'),
        api.get('/automation/summary'),
        api.get('/automation/processes'),
      ]);

      const nextCatalog = catalogResponse.data as Catalog;
      const nextProcesses = processesResponse.data as Process[];

      setCatalog(nextCatalog);
      setSummary(summaryResponse.data);
      setProcesses(nextProcesses);

      setProcessForm((current) => ({
        ...current,
        entity_type: current.entity_type || nextCatalog.entity_types[0]?.value || '',
      }));

      const nextId =
        selectedProcessId && nextProcesses.some((item) => item.id === selectedProcessId)
          ? selectedProcessId
          : nextProcesses[0]?.id || null;

      setSelectedProcessId(nextId);

      if (nextId) {
        const process = nextProcesses.find((item) => item.id === nextId);
        const [stageResponse, ruleResponse, executionResponse] = await Promise.all([
          api.get('/automation/stages', { params: { process_id: nextId } }),
          api.get('/automation/rules', { params: { process_id: nextId } }),
          api.get('/automation/executions', { params: { process_id: nextId, limit: 100 } }),
        ]);
        setStages(stageResponse.data);
        setRules(ruleResponse.data);
        setExecutions(executionResponse.data);

        if (process?.entity_type === 'workflow') {
          const instanceResponse = await api.get('/automation/instances', {
            params: { process_id: nextId, limit: 100 },
          });
          setInstances(instanceResponse.data);
        } else {
          setInstances([]);
        }
      }
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось загрузить автоматизацию');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!selectedProcess) return;

    const firstEvent = catalog.events.find((item) =>
      item.entity_types.includes(selectedProcess.entity_type),
    );
    const firstAction = catalog.actions.find((item) =>
      item.entity_types.includes(selectedProcess.entity_type),
    );

    setRuleForm({
      ...emptyRule,
      event_type: firstEvent?.value || '',
      actions: firstAction ? [{ type: firstAction.value, config: {} }] : [],
    });
    setEditingRuleId(null);
    setTab('rules');

    loadProcessData(selectedProcess.id).catch(() => undefined);
  }, [selectedProcessId]);

  const refreshSummary = async () => {
    const [summaryResponse, processResponse] = await Promise.all([
      api.get('/automation/summary'),
      api.get('/automation/processes'),
    ]);
    setSummary(summaryResponse.data);
    setProcesses(processResponse.data);
  };

  const createProcess = async (event: FormEvent) => {
    event.preventDefault();
    setNotice('');
    try {
      const response = await api.post('/automation/processes', processForm);
      setProcessForm((current) => ({ ...current, name: '', description: '' }));
      await refreshSummary();
      setSelectedProcessId(response.data.id);
      setNotice('Процесс создан');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось создать процесс');
    }
  };

  const addCondition = () => {
    const firstField = conditionFields[0]?.path || (selectedProcess?.entity_type === 'workflow' ? 'variables.' : 'entity.');
    setRuleForm((current) => ({
      ...current,
      conditions: [
        ...current.conditions,
        {
          field: firstField,
          operator: 'equals',
          value: '',
          logical_operator: 'AND',
        },
      ],
    }));
  };

  const addAction = () => {
    const first = actionSpecs[0];
    if (!first) return;
    setRuleForm((current) => ({
      ...current,
      actions: [...current.actions, { type: first.value, config: {} }],
    }));
  };

  const saveRule = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProcessId) return;

    const payload = {
      process_id: selectedProcessId,
      ...ruleForm,
    };

    try {
      if (editingRuleId) {
        await api.patch('/automation/rules/' + editingRuleId, ruleForm);
        setNotice('Правило обновлено');
      } else {
        await api.post('/automation/rules', payload);
        setNotice('Правило создано');
      }

      const firstAction = actionSpecs[0];
      setRuleForm({
        ...emptyRule,
        event_type: eventSpecs[0]?.value || '',
        actions: firstAction ? [{ type: firstAction.value, config: {} }] : [],
      });
      setEditingRuleId(null);
      await loadProcessData(selectedProcessId);
      await refreshSummary();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось сохранить правило');
    }
  };

  const editRule = (rule: Rule) => {
    setEditingRuleId(rule.id);
    setRuleForm({
      name: rule.name,
      description: rule.description || '',
      event_type: rule.event_type,
      conditions: rule.conditions || [],
      actions: rule.actions || [],
      priority: rule.priority,
      stop_after_match: rule.stop_after_match,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const toggleRule = async (rule: Rule) => {
    await api.patch('/automation/rules/' + rule.id, { is_active: !rule.is_active });
    if (selectedProcessId) await loadProcessData(selectedProcessId);
    await refreshSummary();
  };

  const deleteRule = async (ruleId: number) => {
    if (!window.confirm('Удалить правило?')) return;
    await api.delete('/automation/rules/' + ruleId);
    if (selectedProcessId) await loadProcessData(selectedProcessId);
    await refreshSummary();
  };

  const addStage = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProcessId || !stageName.trim()) return;
    await api.post('/automation/stages', {
      process_id: selectedProcessId,
      name: stageName.trim(),
    });
    setStageName('');
    await loadProcessData(selectedProcessId);
    await refreshSummary();
  };

  const deleteStage = async (stageId: number) => {
    if (!window.confirm('Удалить этап?')) return;
    await api.delete('/automation/stages/' + stageId);
    if (selectedProcessId) await loadProcessData(selectedProcessId);
    await refreshSummary();
  };

  const startRun = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProcessId || !runForm.name.trim()) return;

    const variables = Object.fromEntries(
      runForm.variables
        .filter((item) => item.key.trim())
        .map((item) => [item.key.trim(), parseValue(item.value)]),
    );

    try {
      await api.post('/automation/processes/' + selectedProcessId + '/instances', {
        name: runForm.name.trim(),
        variables,
      });
      setRunForm({ name: '', variables: [{ key: '', value: '' }] });
      setNotice('Процесс запущен');
      await loadProcessData(selectedProcessId);
      await refreshSummary();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось запустить процесс');
    }
  };

  const updateRun = async (instanceId: number, patch: Record<string, any>) => {
    await api.patch('/automation/instances/' + instanceId, patch);
    if (selectedProcessId) await loadProcessData(selectedProcessId);
  };

  const emitEvent = async (instanceId: number) => {
    const eventName = (eventNames[instanceId] || '').trim();
    if (!eventName) {
      setNotice('Введите название события');
      return;
    }
    try {
      const payload = eventPayloads[instanceId] || { key: '', value: '' };
      const data = payload.key.trim()
        ? { [payload.key.trim()]: parseValue(payload.value) }
        : {};
      const response = await api.post('/automation/instances/' + instanceId + '/events', {
        event_name: eventName,
        data,
      });
      setNotice(
        'Событие обработано: правил ' + response.data.matched_rule_ids.length +
        ', действий ' + response.data.action_results.length,
      );
      setEventNames((current) => ({ ...current, [instanceId]: '' }));
      setEventPayloads((current) => ({
        ...current,
        [instanceId]: { key: '', value: '' },
      }));
      if (selectedProcessId) await loadProcessData(selectedProcessId);
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || 'Не удалось отправить событие');
    }
  };

  const updateVariable = async (instanceId: number) => {
    const edit = variableEdits[instanceId] || { key: '', value: '' };
    const key = edit.key.trim();
    if (!key) {
      setNotice('Введите название поля');
      return;
    }
    await updateRun(instanceId, {
      variables: { [key]: parseValue(edit.value) },
    });
    setVariableEdits((current) => ({
      ...current,
      [instanceId]: { key: '', value: '' },
    }));
    setNotice('Данные процесса обновлены');
  };

  const validateAll = async () => {
    const response = await api.get('/automation/validate');
    setNotice(
      response.data.valid
        ? 'Проверка пройдена: все правила корректны'
        : 'Найдены ошибки: ' + response.data.errors.length,
    );
  };

  const deleteProcess = async (processId: number) => {
    if (!window.confirm('Удалить процесс вместе с правилами и запусками?')) return;
    await api.delete('/automation/processes/' + processId);
    setSelectedProcessId(null);
    await load();
  };

  const ensureRemoteOptions = async (source?: string) => {
    if (!source || remoteOptions[source]) return;
    const response = await api.get('/automation/options', { params: { source } });
    setRemoteOptions((current) => ({ ...current, [source]: response.data.data || [] }));
  };

  if (loading) {
    return (
      <div className="flex min-h-[420px] items-center justify-center">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <h1 className="page-title">Автоматизация процессов</h1>
          <p className="page-subtitle">
            Простая схема: <strong>КОГДА</strong> произошло событие → <strong>ЕСЛИ</strong> условия подходят → <strong>ТО</strong> выполнить действия.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={validateAll} className="btn-secondary">
            <CheckCircleIcon className="mr-2 h-4 w-4" />
            Проверить всё
          </button>
          <button onClick={() => load()} className="btn-secondary">
            <ArrowPathIcon className="mr-2 h-4 w-4" />
            Обновить
          </button>
        </div>
      </div>

      {notice && (
        <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          {notice}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Summary icon={Cog6ToothIcon} label="Активные процессы" value={summary.active_processes || 0} hint={'из ' + (summary.processes || 0)} />
        <Summary icon={BoltIcon} label="Активные триггеры" value={summary.active_rules || 0} hint={'из ' + (summary.rules || 0)} />
        <Summary icon={PlayIcon} label="Процессы в работе" value={summary.running_instances || 0} hint="свои процессы" />
        <Summary icon={XCircleIcon} label="Ошибки" value={summary.failed_executions || 0} hint="журнал выполнений" danger />
      </div>

      <div className="grid gap-5 xl:grid-cols-[330px_1fr]">
        <aside className="space-y-4">
          <form onSubmit={createProcess} className="card">
            <h2 className="text-base font-semibold text-slate-900">Новый процесс</h2>
            <p className="mt-1 text-xs text-slate-500">Выберите, что именно нужно автоматизировать.</p>

            <div className="mt-4 space-y-3">
              <input
                className="input-field"
                placeholder="Например: Срочные заявки"
                value={processForm.name}
                onChange={(event) => setProcessForm({ ...processForm, name: event.target.value })}
                required
              />
              <select
                className="input-field"
                value={processForm.entity_type}
                onChange={(event) => setProcessForm({ ...processForm, entity_type: event.target.value })}
                required
              >
                {catalog.entity_types.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
              <textarea
                className="input-field min-h-20"
                placeholder="Что делает этот процесс"
                value={processForm.description}
                onChange={(event) => setProcessForm({ ...processForm, description: event.target.value })}
              />
              <button className="btn-primary w-full" type="submit">
                <PlusIcon className="mr-2 h-4 w-4" />
                Создать процесс
              </button>
            </div>
          </form>

          <div className="card p-3">
            <div className="mb-2 px-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Мои процессы
            </div>
            <div className="space-y-1">
              {processes.length === 0 && (
                <div className="p-5 text-center text-sm text-slate-400">Процессов пока нет</div>
              )}
              {processes.map((process) => (
                <div
                  key={process.id}
                  className={
                    'flex items-center rounded-xl ' +
                    (selectedProcessId === process.id ? 'bg-blue-50' : 'hover:bg-slate-50')
                  }
                >
                  <button
                    className="min-w-0 flex-1 px-3 py-3 text-left"
                    onClick={() => setSelectedProcessId(process.id)}
                  >
                    <div className="truncate text-sm font-semibold text-slate-900">{process.name}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {labelFor(catalog.entity_types, process.entity_type)} · {process.rules_count} сценариев
                    </div>
                  </button>
                  <button
                    className="mr-2 rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                    onClick={() => deleteProcess(process.id)}
                    title="Удалить"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <section className="min-w-0 space-y-4">
          {!selectedProcess ? (
            <div className="card py-16 text-center text-sm text-slate-400">
              Создайте или выберите процесс слева
            </div>
          ) : (
            <>
              <div className="card">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl font-semibold text-slate-900">{selectedProcess.name}</h2>
                      <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                        {labelFor(catalog.entity_types, selectedProcess.entity_type)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-500">
                      {selectedProcess.description || entitySpec?.description}
                    </p>
                  </div>
                  <span className={'rounded-full px-3 py-1 text-xs font-semibold ' + (selectedProcess.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600')}>
                    {selectedProcess.is_active ? 'Активен' : 'Выключен'}
                  </span>
                </div>

                <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
                  <TabButton active={tab === 'rules'} onClick={() => setTab('rules')}>Триггеры и роботы · {rules.length}</TabButton>
                  {selectedProcess.entity_type === 'workflow' && (
                    <>
                      <TabButton active={tab === 'stages'} onClick={() => setTab('stages')}>Этапы · {stages.length}</TabButton>
                      <TabButton active={tab === 'runs'} onClick={() => setTab('runs')}>Запуски · {instances.length}</TabButton>
                    </>
                  )}
                  <TabButton active={tab === 'log'} onClick={() => setTab('log')}>Журнал</TabButton>
                </div>
              </div>

              {tab === 'rules' && (
                <div className="space-y-4">
                  <form onSubmit={saveRule} className="card space-y-5">
                    <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900">
                          {editingRuleId ? 'Редактирование сценария' : 'Новый сценарий'}
                        </h3>
                        <p className="mt-1 text-sm text-slate-500">
                          Как в Битрикс: ТРИГГЕР запускает сценарий, УСЛОВИЯ фильтруют, РОБОТЫ выполняются по порядку.
                        </p>
                      </div>
                      {editingRuleId && (
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => {
                            setEditingRuleId(null);
                            setRuleForm({
                              ...emptyRule,
                              event_type: eventSpecs[0]?.value || '',
                              actions: actionSpecs[0] ? [{ type: actionSpecs[0].value, config: {} }] : [],
                            });
                          }}
                        >
                          Отменить редактирование
                        </button>
                      )}
                    </div>

                    <div className="grid gap-3 md:grid-cols-2">
                      <div>
                        <label className="mb-1 block text-sm font-medium text-slate-700">Название сценария</label>
                        <input
                          className="input-field"
                          placeholder="Например: Аварийные заявки — мастеру"
                          value={ruleForm.name}
                          onChange={(event) => setRuleForm({ ...ruleForm, name: event.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm font-medium text-slate-700">Описание</label>
                        <input
                          className="input-field"
                          placeholder="Необязательно"
                          value={ruleForm.description}
                          onChange={(event) => setRuleForm({ ...ruleForm, description: event.target.value })}
                        />
                      </div>
                    </div>

                    <RuleSection badge="ТРИГГЕР" tone="blue" title="КОГДА должен запуститься сценарий">
                      <select
                        className="input-field"
                        value={ruleForm.event_type}
                        onChange={(event) =>
                          setRuleForm({
                            ...ruleForm,
                            event_type: event.target.value,
                            conditions: [],
                          })
                        }
                        required
                      >
                        {eventSpecs.map((item) => (
                          <option key={item.value} value={item.value}>{item.label}</option>
                        ))}
                      </select>
                      {selectedEvent && (
                        <p className="mt-2 text-xs text-slate-500">{selectedEvent.description}</p>
                      )}
                    </RuleSection>

                    <RuleSection badge="ЕСЛИ" tone="amber" title="Какие условия должны совпасть">
                      <div className="space-y-2">
                        {ruleForm.conditions.length === 0 && (
                          <div className="rounded-xl border border-dashed border-slate-200 p-4 text-sm text-slate-400">
                            Без условий — триггер запускает роботов при каждом таком событии.
                          </div>
                        )}
                        {ruleForm.conditions.map((condition, index) => (
                          <ConditionEditor
                            key={index}
                            condition={condition}
                            index={index}
                            fields={conditionFields}
                            operators={catalog.condition_operators}
                            onChange={(next) => {
                              const items = [...ruleForm.conditions];
                              items[index] = next;
                              setRuleForm({ ...ruleForm, conditions: items });
                            }}
                            onDelete={() => {
                              setRuleForm({
                                ...ruleForm,
                                conditions: ruleForm.conditions.filter((_, itemIndex) => itemIndex !== index),
                              });
                            }}
                          />
                        ))}
                        <button type="button" className="btn-secondary" onClick={addCondition}>
                          <PlusIcon className="mr-2 h-4 w-4" />
                          Добавить условие
                        </button>
                      </div>
                    </RuleSection>

                    <RuleSection badge="РОБОТЫ" tone="emerald" title="ТО — что выполнить по порядку">
                      <div className="space-y-3">
                        {ruleForm.actions.map((action, index) => {
                          const spec = actionSpecs.find((item) => item.value === action.type);
                          return (
                            <div key={index} className="rounded-xl border border-slate-200 bg-white p-4">
                              <div className="flex items-start gap-3">
                                <div className="min-w-0 flex-1 space-y-3">
                                  <select
                                    className="input-field"
                                    value={action.type}
                                    onChange={(event) => {
                                      const items = [...ruleForm.actions];
                                      items[index] = { type: event.target.value, config: {} };
                                      setRuleForm({ ...ruleForm, actions: items });
                                    }}
                                  >
                                    {actionSpecs.map((item) => (
                                      <option key={item.value} value={item.value}>{item.label}</option>
                                    ))}
                                  </select>

                                  {spec?.description && (
                                    <p className="text-xs text-slate-500">{spec.description}</p>
                                  )}

                                  {(spec?.config_fields || []).map((field) => (
                                    <ActionField
                                      key={field.name}
                                      field={field}
                                      value={action.config[field.name || '']}
                                      stages={stages}
                                      remoteOptions={remoteOptions[field.source || ''] || []}
                                      ensureRemoteOptions={ensureRemoteOptions}
                                      onChange={(value) => {
                                        const items = [...ruleForm.actions];
                                        items[index] = {
                                          ...action,
                                          config: {
                                            ...action.config,
                                            [field.name || '']: value,
                                          },
                                        };
                                        setRuleForm({ ...ruleForm, actions: items });
                                      }}
                                    />
                                  ))}
                                </div>

                                {ruleForm.actions.length > 1 && (
                                  <button
                                    type="button"
                                    className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                                    onClick={() =>
                                      setRuleForm({
                                        ...ruleForm,
                                        actions: ruleForm.actions.filter((_, itemIndex) => itemIndex !== index),
                                      })
                                    }
                                  >
                                    <TrashIcon className="h-4 w-4" />
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })}

                        <button type="button" className="btn-secondary" onClick={addAction}>
                          <PlusIcon className="mr-2 h-4 w-4" />
                          Добавить действие
                        </button>
                      </div>
                    </RuleSection>

                    <div className="flex flex-col justify-between gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center">
                      <label className="flex items-center gap-2 text-sm text-slate-600">
                        <input
                          type="checkbox"
                          checked={ruleForm.stop_after_match}
                          onChange={(event) =>
                            setRuleForm({ ...ruleForm, stop_after_match: event.target.checked })
                          }
                        />
                        После этого сценария не запускать следующие совпавшие сценарии
                      </label>

                      <button className="btn-primary" type="submit">
                        <CheckCircleIcon className="mr-2 h-4 w-4" />
                        {editingRuleId ? 'Сохранить изменения' : 'Создать сценарий'}
                      </button>
                    </div>
                  </form>

                  <div className="space-y-3">
                    {rules.length === 0 && (
                      <div className="card border-dashed py-12 text-center text-sm text-slate-400">
                        Сценариев ещё нет. Добавьте триггер и роботов выше — без кода.
                      </div>
                    )}

                    {rules.map((rule) => (
                      <div key={rule.id} className="card">
                        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="font-semibold text-slate-900">{rule.name}</div>
                              <span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + (rule.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500')}>
                                {rule.is_active ? 'Работает' : 'Выключено'}
                              </span>
                            </div>

                            <div className="mt-4 space-y-2 text-sm">
                              <SentenceRow badge="ТРИГГЕР" text={labelFor(eventSpecs, rule.event_type)} />
                              <SentenceRow
                                badge="ЕСЛИ"
                                text={rule.conditions.length ? describeConditions(rule.conditions, conditionFields, catalog.condition_operators) : 'без дополнительных условий'}
                              />
                              <SentenceRow
                                badge="РОБОТЫ"
                                text={rule.actions.map((action) => labelFor(actionSpecs, action.type)).join(' → ')}
                              />
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-2">
                            <button className="btn-secondary px-3 py-2" onClick={() => editRule(rule)}>
                              <PencilIcon className="mr-2 h-4 w-4" />
                              Изменить
                            </button>
                            <button className="btn-secondary px-3 py-2" onClick={() => toggleRule(rule)}>
                              {rule.is_active ? 'Выключить' : 'Включить'}
                            </button>
                            <button className="btn-danger px-3 py-2" onClick={() => deleteRule(rule.id)}>
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {tab === 'stages' && selectedProcess.entity_type === 'workflow' && (
                <div className="space-y-4">
                  <div className="card">
                    <h3 className="font-semibold text-slate-900">Этапы процесса</h3>
                    <p className="mt-1 text-sm text-slate-500">
                      Этапы нужны только собственным процессам. Роботы могут автоматически переводить запуск между ними.
                    </p>
                    <form onSubmit={addStage} className="mt-4 flex flex-col gap-3 sm:flex-row">
                      <input
                        className="input-field"
                        placeholder="Например: На согласовании"
                        value={stageName}
                        onChange={(event) => setStageName(event.target.value)}
                        required
                      />
                      <button className="btn-primary shrink-0" type="submit">
                        <PlusIcon className="mr-2 h-4 w-4" />
                        Добавить этап
                      </button>
                    </form>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {stages.length === 0 && (
                      <div className="card w-full border-dashed py-12 text-center text-sm text-slate-400">
                        Этапов пока нет
                      </div>
                    )}
                    {stages.map((stage, index) => (
                      <React.Fragment key={stage.id}>
                        <div className="card min-w-[220px] flex-1">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="text-xs font-medium text-slate-400">Этап {index + 1}</div>
                              <div className="mt-1 font-semibold text-slate-900">{stage.name}</div>
                            </div>
                            <button
                              className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                              onClick={() => deleteStage(stage.id)}
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                        {index < stages.length - 1 && (
                          <ChevronRightIcon className="hidden h-5 w-5 shrink-0 text-slate-300 xl:block" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {tab === 'runs' && selectedProcess.entity_type === 'workflow' && (
                <div className="space-y-4">
                  <form onSubmit={startRun} className="card">
                    <h3 className="font-semibold text-slate-900">Запустить процесс</h3>
                    <p className="mt-1 text-sm text-slate-500">
                      Один процесс может иметь сколько угодно одновременных запусков.
                    </p>

                    <div className="mt-4 space-y-3">
                      <input
                        className="input-field"
                        placeholder="Название запуска"
                        value={runForm.name}
                        onChange={(event) => setRunForm({ ...runForm, name: event.target.value })}
                        required
                      />

                      <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Начальные данные
                        </div>
                        <div className="space-y-2">
                          {runForm.variables.map((variable, index) => (
                            <div key={index} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                              <input
                                className="input-field"
                                placeholder="Название поля"
                                value={variable.key}
                                onChange={(event) => {
                                  const items = [...runForm.variables];
                                  items[index] = { ...variable, key: event.target.value };
                                  setRunForm({ ...runForm, variables: items });
                                }}
                              />
                              <input
                                className="input-field"
                                placeholder="Значение"
                                value={variable.value}
                                onChange={(event) => {
                                  const items = [...runForm.variables];
                                  items[index] = { ...variable, value: event.target.value };
                                  setRunForm({ ...runForm, variables: items });
                                }}
                              />
                              <button
                                type="button"
                                className="btn-secondary px-3"
                                onClick={() =>
                                  setRunForm({
                                    ...runForm,
                                    variables: runForm.variables.filter((_, itemIndex) => itemIndex !== index),
                                  })
                                }
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </div>
                          ))}
                        </div>
                        <button
                          type="button"
                          className="mt-2 text-sm font-medium text-blue-600"
                          onClick={() =>
                            setRunForm({
                              ...runForm,
                              variables: [...runForm.variables, { key: '', value: '' }],
                            })
                          }
                        >
                          + Добавить поле
                        </button>
                      </div>

                      <button className="btn-primary" type="submit">
                        <PlayIcon className="mr-2 h-4 w-4" />
                        Запустить
                      </button>
                    </div>
                  </form>

                  <div className="space-y-3">
                    {instances.length === 0 && (
                      <div className="card border-dashed py-12 text-center text-sm text-slate-400">
                        Запусков пока нет
                      </div>
                    )}

                    {instances.map((instance) => (
                      <div key={instance.id} className="card">
                        <div className="grid gap-4 xl:grid-cols-[1fr_220px_300px] xl:items-start">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="font-semibold text-slate-900">{instance.name}</div>
                              <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">
                                {labelFor(catalog.workflow_statuses, instance.status)}
                              </span>
                            </div>
                            <div className="mt-2 text-sm text-slate-500">
                              Этап: <strong className="text-slate-700">{instance.current_stage_name || 'не задан'}</strong>
                            </div>
                            {Object.keys(instance.variables || {}).length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-2">
                                {Object.entries(instance.variables).map(([key, value]) => (
                                  <span key={key} className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                                    {key}: {String(value)}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>

                          <div className="space-y-3">
                            <div>
                              <label className="mb-1 block text-xs font-medium text-slate-500">Этап</label>
                              <select
                                className="input-field"
                                value={instance.current_stage_id || ''}
                                onChange={(event) =>
                                  updateRun(instance.id, {
                                    current_stage_id: event.target.value ? Number(event.target.value) : null,
                                  })
                                }
                              >
                                <option value="">Без этапа</option>
                                {stages.map((stage) => (
                                  <option key={stage.id} value={stage.id}>{stage.name}</option>
                                ))}
                              </select>
                            </div>
                            <div>
                              <label className="mb-1 block text-xs font-medium text-slate-500">Статус</label>
                              <select
                                className="input-field"
                                value={instance.status}
                                onChange={(event) => updateRun(instance.id, { status: event.target.value })}
                              >
                                {catalog.workflow_statuses.map((status) => (
                                  <option key={String(status.value)} value={status.value}>{status.label}</option>
                                ))}
                              </select>
                            </div>
                          </div>

                          <div className="space-y-3">
                            <div>
                              <label className="mb-1 block text-xs font-medium text-slate-500">Событие процесса</label>
                              <div className="flex gap-2">
                                <input
                                  className="input-field"
                                  placeholder="Например: согласовано"
                                  value={eventNames[instance.id] || ''}
                                  onChange={(event) =>
                                    setEventNames((current) => ({
                                      ...current,
                                      [instance.id]: event.target.value,
                                    }))
                                  }
                                />
                                <button className="btn-secondary shrink-0" onClick={() => emitEvent(instance.id)}>
                                  Запустить
                                </button>
                              </div>
                              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                                <input
                                  className="input-field"
                                  placeholder="Поле события, необязательно"
                                  value={eventPayloads[instance.id]?.key || ''}
                                  onChange={(event) =>
                                    setEventPayloads((current) => ({
                                      ...current,
                                      [instance.id]: {
                                        key: event.target.value,
                                        value: current[instance.id]?.value || '',
                                      },
                                    }))
                                  }
                                />
                                <input
                                  className="input-field"
                                  placeholder="Значение"
                                  value={eventPayloads[instance.id]?.value || ''}
                                  onChange={(event) =>
                                    setEventPayloads((current) => ({
                                      ...current,
                                      [instance.id]: {
                                        key: current[instance.id]?.key || '',
                                        value: event.target.value,
                                      },
                                    }))
                                  }
                                />
                              </div>
                            </div>

                            <div>
                              <label className="mb-1 block text-xs font-medium text-slate-500">Добавить / изменить данные</label>
                              <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                                <input
                                  className="input-field"
                                  placeholder="Поле"
                                  value={variableEdits[instance.id]?.key || ''}
                                  onChange={(event) =>
                                    setVariableEdits((current) => ({
                                      ...current,
                                      [instance.id]: {
                                        key: event.target.value,
                                        value: current[instance.id]?.value || '',
                                      },
                                    }))
                                  }
                                />
                                <input
                                  className="input-field"
                                  placeholder="Значение"
                                  value={variableEdits[instance.id]?.value || ''}
                                  onChange={(event) =>
                                    setVariableEdits((current) => ({
                                      ...current,
                                      [instance.id]: {
                                        key: current[instance.id]?.key || '',
                                        value: event.target.value,
                                      },
                                    }))
                                  }
                                />
                                <button className="btn-secondary shrink-0" onClick={() => updateVariable(instance.id)}>
                                  Сохранить
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {tab === 'log' && (
                <div className="card overflow-hidden p-0">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 text-sm">
                      <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                        <tr>
                          <th className="px-5 py-3">Время</th>
                          <th className="px-5 py-3">Событие</th>
                          <th className="px-5 py-3">Правило</th>
                          <th className="px-5 py-3">Результат</th>
                          <th className="px-5 py-3">Длительность</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {executions.length === 0 && (
                          <tr>
                            <td colSpan={5} className="px-5 py-12 text-center text-slate-400">
                              Выполнений пока нет
                            </td>
                          </tr>
                        )}
                        {executions.map((item) => (
                          <tr key={item.id}>
                            <td className="px-5 py-4 text-slate-500">
                              {new Date(item.created_at).toLocaleString('ru-RU')}
                            </td>
                            <td className="px-5 py-4 font-medium text-slate-700">
                              {labelFor(eventSpecs, item.event_type)}
                            </td>
                            <td className="px-5 py-4 text-slate-500">
                              {rules.find((rule) => rule.id === item.rule_id)?.name || ('#' + (item.rule_id || '—'))}
                            </td>
                            <td className="px-5 py-4">
                              <span className={'rounded-full px-2.5 py-1 text-xs font-semibold ' + (item.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700')}>
                                {item.status === 'completed' ? 'Выполнено' : 'Ошибка'}
                              </span>
                              {item.error && <div className="mt-1 max-w-md text-xs text-red-600">{item.error}</div>}
                            </td>
                            <td className="px-5 py-4 text-slate-500">{item.duration_ms ?? '—'} ms</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function Summary({ icon: Icon, label, value, hint, danger = false }: any) {
  return (
    <div className="card p-4">
      <div className={'mb-3 flex h-10 w-10 items-center justify-center rounded-xl ' + (danger ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600')}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="mt-1 text-sm text-slate-600">{label}</div>
      <div className="mt-1 text-xs text-slate-400">{hint}</div>
    </div>
  );
}

function TabButton({ active, onClick, children }: any) {
  return (
    <button
      onClick={onClick}
      className={'rounded-xl px-3 py-2 text-sm font-medium transition ' + (active ? 'bg-blue-50 text-blue-700' : 'text-slate-500 hover:bg-slate-50')}
    >
      {children}
    </button>
  );
}

function RuleSection({ badge, tone, title, children }: any) {
  const tones: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-700',
    amber: 'bg-amber-100 text-amber-700',
    emerald: 'bg-emerald-100 text-emerald-700',
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
      <div className="mb-3 flex items-center gap-3">
        <span className={'rounded-lg px-2.5 py-1 text-xs font-bold ' + tones[tone]}>{badge}</span>
        <div className="font-medium text-slate-800">{title}</div>
      </div>
      {children}
    </div>
  );
}

function SentenceRow({ badge, text }: { badge: string; text: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="w-16 shrink-0 rounded-lg bg-slate-100 px-2 py-1 text-center text-[11px] font-bold text-slate-500">
        {badge}
      </span>
      <div className="pt-0.5 text-slate-700">{text}</div>
    </div>
  );
}

function ConditionEditor({
  condition,
  index,
  fields,
  operators,
  onChange,
  onDelete,
}: {
  condition: Condition;
  index: number;
  fields: FieldSpec[];
  operators: OptionItem[];
  onChange: (value: Condition) => void;
  onDelete: () => void;
}) {
  const fieldSpec = fields.find((item) => item.path === condition.field);
  const noValue = ['is_empty', 'not_empty', 'is_true', 'is_false'].includes(condition.operator);

  return (
    <div className="grid gap-2 rounded-xl border border-slate-200 bg-white p-3 lg:grid-cols-[90px_1.4fr_1fr_1fr_auto]">
      <select
        className="input-field"
        disabled={index === 0}
        value={index === 0 ? 'AND' : condition.logical_operator}
        onChange={(event) => onChange({ ...condition, logical_operator: event.target.value as 'AND' | 'OR' })}
      >
        <option value="AND">{index === 0 ? 'ГДЕ' : 'И'}</option>
        <option value="OR">ИЛИ</option>
      </select>

      <div>
        <input
          className="input-field"
          list={'condition-fields-' + index}
          placeholder="Поле или variables.имя"
          value={condition.field}
          onChange={(event) => onChange({ ...condition, field: event.target.value })}
        />
        <datalist id={'condition-fields-' + index}>
          {fields.map((field) => (
            <option key={field.path} value={field.path}>{field.label}</option>
          ))}
        </datalist>
      </div>

      <select
        className="input-field"
        value={condition.operator}
        onChange={(event) => onChange({ ...condition, operator: event.target.value })}
      >
        {operators.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
      </select>

      {noValue ? (
        <div className="flex items-center px-3 text-sm text-slate-400">значение не требуется</div>
      ) : fieldSpec?.type === 'select' ? (
        <select
          className="input-field"
          value={String(condition.value ?? '')}
          onChange={(event) => onChange({ ...condition, value: parseValue(event.target.value) })}
        >
          <option value="">Выберите</option>
          {(fieldSpec.options || []).map((item) => (
            <option key={String(item.value)} value={String(item.value)}>{item.label}</option>
          ))}
        </select>
      ) : (
        <input
          className="input-field"
          placeholder="Значение"
          value={String(condition.value ?? '')}
          onChange={(event) => onChange({ ...condition, value: parseValue(event.target.value) })}
        />
      )}

      <button
        type="button"
        className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
        onClick={onDelete}
      >
        <TrashIcon className="h-4 w-4" />
      </button>
    </div>
  );
}

function ActionField({
  field,
  value,
  stages,
  remoteOptions,
  ensureRemoteOptions,
  onChange,
}: {
  field: FieldSpec;
  value: any;
  stages: Stage[];
  remoteOptions: OptionItem[];
  ensureRemoteOptions: (source?: string) => Promise<void>;
  onChange: (value: any) => void;
}) {
  useEffect(() => {
    if (field.type === 'remote_select') {
      ensureRemoteOptions(field.source).catch(() => undefined);
    }
  }, [field.type, field.source]);

  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-slate-500">{field.label}</label>

      {field.type === 'select' && (
        <select
          className="input-field"
          value={value ?? ''}
          onChange={(event) => onChange(event.target.value)}
          required={field.required}
        >
          <option value="">Выберите</option>
          {(field.options || []).map((item) => (
            <option key={String(item.value)} value={item.value}>{item.label}</option>
          ))}
        </select>
      )}

      {field.type === 'remote_select' && (
        <select
          className="input-field"
          value={value ?? ''}
          onChange={(event) => onChange(event.target.value ? Number(event.target.value) : '')}
          required={field.required}
        >
          <option value="">Выберите</option>
          {remoteOptions.map((item) => (
            <option key={String(item.value)} value={item.value}>{item.label}</option>
          ))}
        </select>
      )}

      {field.type === 'stage_select' && (
        <select
          className="input-field"
          value={value ?? ''}
          onChange={(event) => onChange(event.target.value ? Number(event.target.value) : '')}
          required={field.required}
        >
          <option value="">Выберите этап</option>
          {stages.map((stage) => (
            <option key={stage.id} value={stage.id}>{stage.name}</option>
          ))}
        </select>
      )}

      {field.type === 'boolean' && (
        <label className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-3 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => onChange(event.target.checked)}
          />
          Да
        </label>
      )}

      {field.type === 'textarea' && (
        <textarea
          className="input-field min-h-24"
          value={value ?? ''}
          onChange={(event) => onChange(event.target.value)}
          required={field.required}
        />
      )}

      {field.type === 'text' && (
        <input
          className="input-field"
          value={value ?? ''}
          onChange={(event) => onChange(event.target.value)}
          required={field.required}
        />
      )}

      {field.supports_template && (
        <div className="mt-1 text-[11px] text-slate-400">
          Можно подставлять данные: {'{{ entity.number }}'}, {'{{ event.event_name }}'}, {'{{ variables.name }}'}
        </div>
      )}
    </div>
  );
}

function labelFor(items: Array<{ value: any; label: string }>, value: any) {
  return items.find((item) => item.value === value)?.label || String(value ?? '—');
}

function describeConditions(
  conditions: Condition[],
  fields: FieldSpec[],
  operators: OptionItem[],
) {
  return conditions
    .map((condition, index) => {
      const fieldLabel = fields.find((field) => field.path === condition.field)?.label || condition.field;
      const operatorLabel = labelFor(operators, condition.operator);
      const glue = index === 0 ? '' : condition.logical_operator === 'OR' ? ' ИЛИ ' : ' И ';
      const noValue = ['is_empty', 'not_empty', 'is_true', 'is_false'].includes(condition.operator);
      return glue + fieldLabel + ' ' + operatorLabel + (noValue ? '' : ' ' + String(condition.value));
    })
    .join('');
}

function parseValue(value: string): any {
  const trimmed = value.trim();
  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;
  if (trimmed !== '' && !Number.isNaN(Number(trimmed))) return Number(trimmed);
  if (
    (trimmed.startsWith('[') && trimmed.endsWith(']')) ||
    (trimmed.startsWith('{') && trimmed.endsWith('}'))
  ) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return value;
    }
  }
  return value;
}
