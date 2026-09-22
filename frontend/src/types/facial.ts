export interface Persona {
  id: string;
  nombre: string;
  email: string;
  activo: boolean;
  created_at: string;
  updated_at?: string;
}

export interface RecognitionResult {
  persona_id: string;
  nombre: string;
  email?: string;
  similitud: number;
  distancia: number;
  umbral: number;
  coincide: boolean;
  probabilidad_calibrada?: number;
  calidad_imagen?: number;
  iluminacion?: number;
  detail?: string;
}

export interface RecognitionResponse {
  success: boolean;
  coincide: boolean;
  resultado: RecognitionResult | null;
  detail?: string;
}

export interface HistorialEntry {
  id: string;
  persona_id: string | null;
  similitud: number;
  distancia: number;
  umbral: number;
  coincide: boolean;
  probabilidad_calibrada: number | null;
  resultado_real?: boolean | null;
  clasificacion?: string | null;
  created_at: string;
  personas?: { nombre: string };
}

export interface PredictionInput {
  similitud: number;
  distancia: number;
  calidad_imagen: number;
  iluminacion: number;
}

export interface PredictionResponse {
  success: boolean;
  probabilidad_calibrada: number;
}

export interface ModelStatus {
  name: string;
  loaded: boolean;
  type: string;
}

export interface Stats {
  total_reconocimientos: number;
  coincidencias_positivas: number;
  tasa_exito: number;
}
