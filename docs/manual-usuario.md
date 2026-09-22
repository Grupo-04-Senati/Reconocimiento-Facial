# Manual de Usuario

## Inicio de Sesión

1. Abrir la aplicación en `http://localhost:5173`
2. Si es la primera vez, crear una cuenta en Supabase Auth
3. Iniciar sesión con email y contraseña

## Registrar un Rostro

1. Navegar a **Registro** (menú superior)
2. Ingrese nombre y correo electrónico
3. Haga click en **Capturar rostro**
4. Alinee su rostro dentro del recuadro
5. Haga click en el botón de captura
6. Verifique la imagen y haga click en **Registrar persona**

## Reconocer un Rostro

1. Navegar a **Reconocimiento** (menú superior)
2. Haga click en **Capturar rostro**
3. El sistema analizará automáticamente la imagen
4. Verá el resultado con:
   - Nombre de la persona identificada
   - Nivel de similitud (0-100%)
   - Probabilidad calibrada
   - Métricas de calidad

## Análisis de Probabilidades

1. Navegar a **Probabilidades** (menú superior)
2. Ajuste los sliders:
   - Similitud: Coincidencia del embedding
   - Distancia: Distancia euclidiana
   - Calidad: Nitidez de la imagen
   - Iluminación: Brillo de la imagen
3. Haga click en **Predecir probabilidad**
4. Vea el resultado calibrado

## Historial

1. Navegar a **Historial** (menú superior)
2. Vea el gráfico de reconocimientos recientes
3. Cambie entre vista de barras y líneas
4. Consulte la tabla de registros detallada
