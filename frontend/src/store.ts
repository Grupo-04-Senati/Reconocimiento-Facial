import type { Session, FaceRecord, RecognitionRecord, MLDataPoint, MLMetrics, Settings, Role } from './types';
import { authLogin, authRegister } from './services/api';

function getStore<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function setStore<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value));
}

// ---------- Users (via Backend API) ----------
const SESSION_KEY = 'bd_session';

export async function loginUser(email: string, password: string): Promise<Session | null> {
  try {
    const result = await authLogin(email, password);
    if (result.success && result.user) {
      const session: Session = {
        userId: result.user.id,
        name: result.user.name,
        email: result.user.email,
        role: result.user.role as Role,
        token: result.token,
      };
      setStore(SESSION_KEY, session);
      return session;
    }
    return null;
  } catch {
    return null;
  }
}

export async function registerUser(name: string, email: string, password: string, role: string = 'operador'): Promise<{ success: boolean; error?: string }> {
  try {
    const result = await authRegister(name, email, password, role);
    return { success: result.success };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Error al registrar';
    return { success: false, error: msg };
  }
}

export function getSession(): Session | null { return getStore<Session | null>(SESSION_KEY, null); }
export function logoutUser() { localStorage.removeItem(SESSION_KEY); }

export function hasPermission(role: Role, permission: string): boolean {
  const perms: Record<Role, string[]> = {
    admin: ['dashboard', 'registro', 'reconocimiento', 'probabilidades', 'historial', 'entrenamiento', 'seguridad'],
    operador: ['dashboard', 'registro', 'reconocimiento', 'historial'],
    analista: ['dashboard', 'probabilidades', 'historial', 'entrenamiento'],
  };
  return perms[role]?.includes(permission) ?? false;
}

// ---------- Face Records (local fallback) ----------
const FACES_KEY = 'bd_faces';
export function getFaces(): FaceRecord[] { return getStore<FaceRecord[]>(FACES_KEY, []); }

export function addFace(data: Omit<FaceRecord, 'id' | 'registeredAt'>): FaceRecord {
  const faces = getFaces();
  const record: FaceRecord = { id: String(Date.now()), ...data, registeredAt: new Date().toISOString() };
  faces.push(record);
  setStore(FACES_KEY, faces);
  return record;
}

export function deleteFace(id: string) {
  setStore(FACES_KEY, getFaces().filter((f) => f.id !== id));
}

// ---------- ML Dataset (local fallback) ----------
const DATASET_KEY = 'bd_ml_dataset';

function generateDataset(n: number): MLDataPoint[] {
  const data: MLDataPoint[] = [];
  for (let i = 0; i < n; i++) {
    const similarity = Math.random() * 100;
    const lighting = Math.random() * 100;
    const quality = Math.random() * 100;
    const distance = Math.random();
    const score = (similarity * 0.4 + quality * 0.3 + lighting * 0.2 - distance * 50);
    const result = score > 45 + (Math.random() * 10 - 5);
    data.push({ id: String(Date.now() + i), similarity, lighting, quality, distance, result });
  }
  return data;
}

export function getDataset(): MLDataPoint[] {
  let data = getStore<MLDataPoint[]>(DATASET_KEY, []);
  if (data.length === 0) {
    data = generateDataset(200);
    setStore(DATASET_KEY, data);
  }
  return data;
}

export function addDatasetPoints(points: Omit<MLDataPoint, 'id'>[]): void {
  const existing = getDataset();
  const newPoints = points.map((p) => ({ ...p, id: String(Date.now()) }));
  setStore(DATASET_KEY, [...existing, ...newPoints]);
}

export function clearDataset() { setStore(DATASET_KEY, []); }

// ---------- ML Training (local fallback) ----------
const METRICS_KEY = 'bd_ml_metrics';

function sigmoid(x: number): number { return 1 / (1 + Math.exp(-x)); }

export function trainModel(modelType: string): MLMetrics {
  const data = getDataset();
  const trainSize = Math.floor(data.length * 0.8);
  const train = data.slice(0, trainSize);
  const test = data.slice(trainSize);

  let w = [0.1, 0.1, 0.1, -0.1];
  const lr = 0.01;

  for (let epoch = 0; epoch < 100; epoch++) {
    for (const d of train) {
      const features = [d.similarity / 100, d.lighting / 100, d.quality / 100, 1 - d.distance];
      const z = w.reduce((sum, wi, i) => sum + wi * features[i], 0);
      const pred = sigmoid(z);
      const error = (d.result ? 1 : 0) - pred;
      w = w.map((wi, i) => wi + lr * error * features[i]);
    }
  }

  if (modelType === 'random_forest' || modelType === 'gradient_boosting') {
    for (let i = 0; i < w.length; i++) { w[i] += (Math.random() - 0.5) * 0.02; }
  }

  let tp = 0, tn = 0, fp = 0, fn = 0;
  for (const d of test) {
    const features = [d.similarity / 100, d.lighting / 100, d.quality / 100, 1 - d.distance];
    const z = w.reduce((sum, wi, i) => sum + wi * features[i], 0);
    const pred = sigmoid(z) > 0.5;
    if (pred && d.result) tp++;
    else if (!pred && !d.result) tn++;
    else if (pred && !d.result) fp++;
    else fn++;
  }

  const total = tp + tn + fp + fn;
  const accuracy = total > 0 ? ((tp + tn) / total) * 100 : 0;
  const precision = (tp + fp) > 0 ? (tp / (tp + fp)) * 100 : 0;
  const recall = (tp + fn) > 0 ? (tp / (tp + fn)) * 100 : 0;
  const f1 = (precision + recall) > 0 ? (2 * precision * recall) / (precision + recall) : 0;
  const fpr = (fp + tn) > 0 ? (fp / (fp + tn)) * 100 : 0;
  const fnr = (fn + tp) > 0 ? (fn / (fn + tp)) * 100 : 0;

  const metrics: MLMetrics = {
    accuracy: Math.round(accuracy * 10) / 10,
    precision: Math.round(precision * 10) / 10,
    recall: Math.round(recall * 10) / 10,
    f1: Math.round(f1 * 10) / 10,
    falsePositiveRate: Math.round(fpr * 10) / 10,
    falseNegativeRate: Math.round(fnr * 10) / 10,
    confusionMatrix: { tp, tn, fp, fn },
    model: modelType,
    trainedAt: new Date().toISOString(),
    samples: data.length,
  };

  setStore(METRICS_KEY, metrics);
  return metrics;
}

export function getMetrics(): MLMetrics | null { return getStore<MLMetrics | null>(METRICS_KEY, null); }

export function predictWithModel(features: { similarity: number; lighting: number; quality: number; distance: number }): { predicted: boolean; confidence: number } {
  const w = [0.38, 0.22, 0.28, -0.42];
  const input = [features.similarity / 100, features.lighting / 100, features.quality / 100, 1 - features.distance];
  const z = w.reduce((sum, wi, i) => sum + wi * input[i], 0);
  const prob = sigmoid(z);
  return { predicted: prob > 0.5, confidence: Math.round(prob * 1000) / 10 };
}

// ---------- Recognition History (local fallback) ----------
const HISTORY_KEY = 'bd_history';
export function getHistory(): RecognitionRecord[] { return getStore<RecognitionRecord[]>(HISTORY_KEY, []); }

export function addHistory(record: Omit<RecognitionRecord, 'id'>): RecognitionRecord {
  const history = getHistory();
  const entry: RecognitionRecord = { id: String(Date.now()), ...record };
  history.push(entry);
  setStore(HISTORY_KEY, entry);
  return entry;
}

export function clearHistory() { setStore(HISTORY_KEY, []); }

// ---------- Settings ----------
const SETTINGS_KEY = 'bd_settings';
const defaultSettings: Settings = {
  schoolName: 'Badicorp', schoolYear: '2026', semester: '1er Semestre',
  alertThreshold: 75, notifications: true,
};

export function getSettings(): Settings { return getStore<Settings>(SETTINGS_KEY, defaultSettings); }
export function saveSettings(data: Settings) { setStore(SETTINGS_KEY, data); }
