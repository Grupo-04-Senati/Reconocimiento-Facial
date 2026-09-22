export type Role = 'admin' | 'operador' | 'analista';

export interface User {
  id: string;
  name: string;
  email: string;
  password: string;
  role: Role;
  active: boolean;
  createdAt: string;
}

export interface Session {
  userId: string;
  name: string;
  email: string;
  role: Role;
  token?: string;
}

export interface FaceRecord {
  id: string;
  name: string;
  email: string;
  photo: string;
  registeredAt: string;
}

export interface MLDataPoint {
  id: string;
  similarity: number;
  lighting: number;
  quality: number;
  distance: number;
  result: boolean;
}

export interface RecognitionRecord {
  id: string;
  matchedName: string;
  matchedPhoto: string;
  similarity: number;
  capturedPhoto: string;
  timestamp: string;
  lighting: number;
  quality: number;
  distance: number;
  predicted: boolean;
  confidence: number;
}

export interface MLMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  falsePositiveRate: number;
  falseNegativeRate: number;
  confusionMatrix: { tp: number; tn: number; fp: number; fn: number };
  model: string;
  trainedAt: string;
  samples: number;
}

export interface Settings {
  schoolName: string;
  schoolYear: string;
  semester: string;
  alertThreshold: number;
  notifications: boolean;
}

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Administrador',
  operador: 'Operador',
  analista: 'Analista ML',
};
