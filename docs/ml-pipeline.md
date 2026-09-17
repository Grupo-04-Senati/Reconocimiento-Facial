# ML Pipeline

## Modelos Utilizados

### 1. Face Detection & Embedding: InsightFace (ArcFace)
- **Modelo**: buffalo_l
- **Framework**: ONNX Runtime
- **Dimensiones**: 512
- **Detección**: RetinaFace
- **Preprocesamiento**: Normalización, alineación de rostros

### 2. Probability Calibration: scikit-learn
- **Algoritmo**: RandomForestClassifier
- **Calibración**: Isotonic Regression
- **Features**: similitud, distancia, calidad_imagen, iluminacion

## Pipeline de Entrenamiento

```
1. Recopilar datos (ml_training_records)
2. Extraer features: [similitud, calidad, iluminacion, distancia]
3. Label: resultado_real (True/False)
4. Train/Test split (80/20)
5. Entrenar RandomForest
6. Calibrar con Isotonic Regression
7. Evaluar métricas (accuracy, F1, ROC-AUC)
8. Guardar modelo (.joblib)
```

## Métricas de Evaluación

| Métrica | Objetivo |
|---------|----------|
| Accuracy | > 0.90 |
| Precision | > 0.85 |
| Recall | > 0.85 |
| F1-Score | > 0.85 |
| ROC-AUC | > 0.90 |

## Evaluación de Calidad de Imagen

- **Laplacian Variance**: Mide nitidez del rostro
- **Illumination**: Brillo promedio normalizado
- **Face Area Ratio**: Proporción del rostro en la imagen
