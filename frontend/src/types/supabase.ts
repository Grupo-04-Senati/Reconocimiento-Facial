export interface Database {
  public: {
    Tables: {
      personas: {
        Row: {
          id: string;
          nombre: string;
          email: string;
          activo: boolean;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          nombre: string;
          email: string;
          activo?: boolean;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          nombre?: string;
          email?: string;
          activo?: boolean;
          updated_at?: string;
        };
      };
      face_embeddings: {
        Row: {
          id: string;
          persona_id: string;
          embedding: number[];
          modelo: string;
          image_url: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          persona_id: string;
          embedding: number[];
          modelo?: string;
          image_url?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          persona_id?: string;
          embedding?: number[];
          modelo?: string;
          image_url?: string | null;
        };
      };
      recognition_logs: {
        Row: {
          id: string;
          persona_id: string | null;
          similitud: number;
          distancia: number;
          umbral: number;
          coincide: boolean;
          probabilidad_calibrada: number | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          persona_id?: string | null;
          similitud: number;
          distancia: number;
          umbral: number;
          coincide: boolean;
          probabilidad_calibrada?: number | null;
          created_at?: string;
        };
      };
      ml_training_records: {
        Row: {
          id: string;
          similitud: number;
          calidad_imagen: number;
          iluminacion: number;
          distancia: number;
          resultado_real: boolean;
          created_at: string;
        };
        Insert: {
          id?: string;
          similitud: number;
          calidad_imagen: number;
          iluminacion: number;
          distancia: number;
          resultado_real: boolean;
          created_at?: string;
        };
      };
    };
  };
}
