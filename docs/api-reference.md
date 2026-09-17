# API Reference

Base URL: `http://localhost:8000`

## Health

### `GET /api/health`
Verifica estado del sistema.

**Response:**
```json
{
  "status": "healthy",
  "service": "Sistema de Reconocimiento Facial",
  "version": "1.0.0",
  "environment": "development"
}
```

## Personas

### `POST /api/personas`
Registra una nueva persona con embedding facial.

**Request:** `multipart/form-data`
- `nombre` (string, required)
- `email` (string, required)
- `imagen` (file, required) - JPG/PNG/WebP, max 5MB

**Response:**
```json
{
  "success": true,
  "persona_id": "uuid",
  "message": "Persona 'Nombre' registrada exitosamente"
}
```

### `GET /api/personas`
Lista todas las personas registradas.

### `GET /api/personas/{id}`
Obtiene detalles de una persona.

### `DELETE /api/personas/{id}`
Elimina una persona y sus embeddings.

## Reconocimiento

### `POST /api/reconocimiento`
Reconoce un rostro en una imagen.

**Request:** `multipart/form-data`
- `imagen` (file, required)

**Response:**
```json
{
  "success": true,
  "resultado": {
    "persona_id": "uuid",
    "nombre": "Nombre",
    "similitud": 0.8934,
    "distancia": 0.1066,
    "umbral": 0.75,
    "coincide": true,
    "probabilidad_calibrada": 0.8721,
    "calidad_imagen": 0.9200,
    "iluminacion": 0.7100
  }
}
```

### `GET /api/reconocimiento/historial`
Obtiene los últimos 100 registros de reconocimiento.

## Probabilidades

### `POST /api/probabilidades/prediccion`
Predice probabilidad calibrada de coincidencia.

**Request Body:**
```json
{
  "similitud": 0.85,
  "distancia": 0.35,
  "calidad_imagen": 0.9,
  "iluminacion": 0.7
}
```

### `POST /api/probabilidades/entrenar`
Registra un registro de entrenamiento ML.

### `GET /api/probabilidades/estadisticas`
Obtiene estadísticas de reconocimiento.

## Models

### `GET /api/models/status`
Estado de los modelos ML cargados.
