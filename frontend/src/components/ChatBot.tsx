import { useState, useRef, useEffect, useCallback } from 'react';
import { X, ArrowLeft, ChevronRight, Trash2, ChevronDown, Volume2, VolumeX } from 'lucide-react';
import './ChatBot.css';

interface Message {
  id: string;
  text: string;
  sender: 'bot' | 'user';
  timestamp: Date;
}

interface Topic {
  id: string;
  icon: string;
  label: string;
  answer: string;
  subtopics?: Topic[];
}

const TOPICS: Topic[] = [
  {
    id: 'como_usar',
    icon: '🚀',
    label: 'Como usar el sistema',
    answer:
      '**Guia rapida del sistema:**\n\n**Paso 1 - Registrarse:**\nEn la pantalla de login, haz clic en "Registrarse". Ingresa tu nombre, correo, contrasena y **selecciona tu rol** (Operador, Analista o Admin).\n\n**Paso 2 - Registrar personas:**\nSi eres Operador o Admin, ve a "Registro Facial". Ingresa el nombre y email de la persona, luego captura o sube una foto de su rostro.\n\n**Paso 3 - Identificar personas:**\nVe a "Reconocimiento". Puedes usar la camara en tiempo real o subir una imagen. El sistema identificara automaticamente a la persona registrada.\n\n**Paso 4 - Confirmar resultados:**\nEn "Historial", confirma si cada reconocimiento fue correcto o incorrecto. Esto alimenta el modelo de Machine Learning.\n\n**Paso 5 - Entrenar el ML:**\nEn "Entrenamiento ML", con al menos 10 de cada clase (10 Humano Real y 10 No Real), puedes darle a "Entrenar".\n\n**Paso 6 - Analizar probabilidades:**\nEn "Probabilidades" (solo Analista/Admin), puedes simular diferentes escenarios con sliders y ver como cambia la probabilidad.\n\nEl sistema aprende y mejora con cada confirmacion que hagas.',
  },
  {
    id: 'que_fotos',
    icon: '📸',
    label: 'Que fotos usar y como entrenar',
    answer:
      '**Que fotos dar y como entrena el sistema:**\n\nEl sistema usa fotos en dos momentos distintos:\n\n**1) Para REGISTRAR a una persona** (pestana Registro Facial):\nUsa **1 foto buena** del rostro real. Esa foto genera el "embedding" (huella facial) con Deep Learning.\n\n**2) Para ENTRENAR el modelo ML** (distinguir humano real de IA/imagen/dibujo):\nNecesitas reconocimientos confirmados de dos tipos: **Humano Real** (personas reales) y **No Real** (IA, imagenes o dibujos).\n\nSelecciona un subtema: que fotos SI sirven, cuales NO, y como entrenar humano real vs no real.',
    subtopics: [
      {
        id: 'fotos_si',
        icon: '✅',
        label: 'Fotos que SI sirven',
        answer:
          '✅ **Fotos que SI sirven (para registrar):**\n\n- **Rostro de frente**, mirando a la camara\n- **Bien iluminada**, con luz pareja en la cara\n- **Nitida**, sin desenfoque ni movimiento\n- **Un solo rostro** en la imagen\n- Cara **grande** en el encuadre (de cerca)\n- **Sin** lentes oscuros, sin gorra que tape la cara, sin mascarilla\n- Expresion neutral\n\nMientras mejor la foto, mejor el embedding... y mejores los reconocimientos. Elemental.',
      },
      {
        id: 'fotos_no',
        icon: '❌',
        label: 'Fotos que NO sirven',
        answer:
          '❌ **Fotos que NO sirven (evitalas):**\n\n- **Borrosas** o movidas\n- **Muy oscuras** o a contraluz (una ventana detras)\n- Rostro **de perfil** o mirando a otro lado\n- **Varias personas** en la misma foto\n- Cara **tapada**: mascarilla, lentes oscuros, mano o pelo\n- Rostro **muy lejano** o pequeno\n- **Foto de una pantalla** o foto de otra foto (baja calidad)\n\nEstas fotos generan embeddings malos y hacen que el sistema falle. Un error... evitable.',
      },
      {
        id: 'como_entrenar_fotos',
        icon: '🎓',
        label: 'Como entrenar: humano real vs no real',
        answer:
          '🎓 **Como entrenar el modelo ML:**\n\nEl objetivo del ML es distinguir un **humano real** de una **IA, imagen o dibujo**. Aprende de reconocimientos **confirmados**, y necesita ejemplos de las DOS clases:\n\n**🟢 Humano Real:**\n1. Registra a una persona real\n2. En Reconocimiento, dale una foto **de esa misma persona real**\n3. Marca el resultado como **"Humano Real"**\n\n**🔴 No Real (IA, imagen o dibujo):**\n1. En Reconocimiento, dale una **cara de IA** (thispersondoesnotexist.com), un **dibujo** o una **imagen** que no sea una persona registrada\n2. Marca el resultado como **"No Real"**\n\nMientras mas ejemplos de cada clase le des, mejor separa humano real de no real. Luego ve a **Entrenamiento ML** y presiona **Entrenar**.\n\nSu verdadera funcion se ve en **Reconocimiento**: ahi el sistema aplica lo aprendido para decir si lo que ve es un humano real o no.',
      },
    ],
  },
  {
    id: 'ia_ml_dl',
    icon: '🔬',
    label: 'IA, ML y DL',
    answer:
      'Excelente pregunta. Mis simulaciones revelan las diferencias clave:\n\n**Inteligencia Artificial (IA):**\nEs el campo general que busca que las computadoras realicen tareas asociadas con la inteligencia humana.\nEn este proyecto: identificacion facial, decisiones asistidas y analisis de resultados.\n\n**Machine Learning (ML):**\nEs una rama de la IA que aprende patrones a partir de datos.\nEn este proyecto: clasificacion de coincidencias, metricas (precision, recall, F1) y probabilidades calibradas.\n\n**Deep Learning (DL):**\nEs una rama del ML que utiliza redes neuronales profundas.\nEn este proyecto: extraccion de embeddings faciales con ArcFace (ResNet-100) y reconocimiento de rostros.\n\n**Relacion conceptual:**\nIA > ML > DL\n\nIA es el todo, ML es una parte de IA, y DL es una parte de ML. En este sistema los tres trabajan juntos... de forma coordinada, debo admitirlo.',
  },
  {
    id: 'sistema',
    icon: '🤖',
    label: 'Que es este sistema',
    answer:
      'Basandome en mis analisis... este es el **Sistema de Reconocimiento Facial de Badicorp**. Fue construido por el Grupo 04 de SENATI bajo la supervision de mi creador, el Dr. Eggman... digo, bajo supervision academica.\n\nPermite:\n1. **Registrar personas** capturando una foto de su rostro\n2. **Identificar personas** mediante comparacion de embeddings faciales\n3. **Analizar probabilidades** de coincidencia con metricas calibradas\n4. **Entrenar modelos de Machine Learning** para mejorar la precision\n5. **Gestionar usuarios** con sistema de roles y permisos\n\nLas simulaciones indican un nivel de funcionalidad... aceptable.',
  },
  {
    id: 'tecnologias',
    icon: '🧠',
    label: 'Tecnologias (DL/ML)',
    answer:
      'Interesante pregunta. Mis sensores detectan las siguientes tecnologias en operacion:\n\n**Deep Learning (confirmado):**\n- InsightFace con modelo **ArcFace** (ResNet-100)\n- Genera vectores de 512 dimensiones por cada rostro detectado\n- Detecta y alinea rostros automaticamente\n- Esto es una **red neuronal profunda real**, no una simulacion\n\n**Machine Learning (implementado, requiere datos):**\n- scikit-learn: LogisticRegression y RandomForest\n- Calibracion Isotonica para probabilidades\n- Sin datos de entrenamiento utiliza un fallback matematico\n\n**Computer Vision clasico:**\n- OpenCV para evaluacion de calidad (varianza Laplaciana)\n- OpenCV para medicion de iluminacion (brillo medio)\n\nLa parte principal del sistema... es genuinamente sofisticada. Debo reconocerlo.',
    subtopics: [
      {
        id: 'embedding',
        icon: '🔢',
        label: 'Que es un embedding',
        answer:
          'Un **embedding facial** es un vector matematico de 512 valores que representa de forma unica un rostro.\n\nEjemplo simplificado: `[0.12, -0.45, 0.78, 0.03, ... 512 valores]`\n\n**Relaciones de distancia:**\n- Misma persona: vectores similares (distancia baja)\n- Personas diferentes: vectores distintos (distancia alta)\n\nSe calcula mediante **ArcFace** (Deep Learning), que entreno una red neuronal para que rostros semanticamente similares generen vectores cercanos.\n\nSe almacena en **pgvector** con indice **HNSW** para busqueda eficiente.\n\nEs... elegantemente diseñado, debo admitirlo.',
      },
      {
        id: 'umbral',
        icon: '📏',
        label: 'Umbral de similitud',
        answer:
          'El **umbral de similitud** determina si dos rostros corresponden a la misma persona:\n\n- Similitud > 0.40 (40%): **COINCIDENCIA** confirmada\n- Similitud < 0.40: **SIN COINCIDENCIA**\n\nCon embeddings generados por ArcFace:\n- Misma persona: similitud tipica de ~0.50 a 0.80\n- Personas diferentes: similitud tipica de ~0.10 a 0.30\n\nLa **distancia** es inversamente proporcial: menor distancia indica mayor similitud.\n\nEl umbral esta calibrado para minimizar falsos negativos... una decision pragmática.',
      },
      {
        id: 'arquitectura',
        icon: '🏗️',
        label: 'Arquitectura',
        answer:
          '**Stack Tecnologico completo:**\n\n- Frontend: React + TypeScript + Vite + Tailwind CSS\n- Backend: Python + FastAPI + Uvicorn\n- Base de datos: PostgreSQL (Supabase) + pgvector (indice HNSW)\n- AI/ML: InsightFace (ArcFace) + scikit-learn + OpenCV\n- Despliegue: Vercel (frontend) + Railway (backend)\n\n**Flujo de procesamiento:**\nImagen -> InsightFace detecta rostro -> genera embedding 512-dim -> pgvector busca el mas similar -> scikit-learn calcula probabilidad -> resultado.\n\nEs una arquitectura... competente. Mi creador estaria parcialmente satisfecho.',
      },
    ],
  },
  {
    id: 'roles',
    icon: '👥',
    label: 'Roles del sistema',
    answer:
      'El sistema opera con **tres roles** funcionales:\n\n**Administrador** - Acceso total al sistema:\n- Gestionar usuarios, registrar personas, ejecutar reconocimientos\n- Analizar probabilidades, entrenar modelos, revisar auditoria\n\n**Operador** - Operaciones diarias:\n- Registrar personas (captura facial)\n- Ejecutar reconocimientos\n- Ver historial y confirmar resultados\n\n**Analista ML** - Optimizacion del modelo:\n- Analizar probabilidades y metricas\n- Entrenar modelos de Machine Learning\n- Revisar historial para identificar patrones\n\nLa separacion de roles es... logicamente solida. Evita conflictos de interes.',
    subtopics: [
      {
        id: 'admin',
        icon: '👑',
        label: 'Administrador',
        answer:
          '**Rol: Administrador**\n\nControl total del sistema. Puede:\n- Gestionar usuarios (crear, eliminar, asignar roles)\n- Registrar personas (capturar rostros)\n- Ejecutar reconocimientos (identificar personas)\n- Ver y analizar probabilidades\n- Entrenar modelos de Machine Learning\n- Revisar registros de auditoria\n\nEs el **unico** rol con acceso a la seccion de Seguridad.\n\nUna posicion de autoridad... que comprendo perfectamente.',
      },
      {
        id: 'operador',
        icon: '🔧',
        label: 'Operador',
        answer:
          '**Rol: Operador**\n\nResponsable del trabajo diario:\n- Registrar personas nuevas (1 foto del rostro)\n- Ejecutar reconocimientos faciales\n- Ver historial de reconocimientos\n- Confirmar resultados (correcto/incorrecto) para alimentar el dataset de ML\n\n**Restricciones:** No puede ver probabilidades, entrenar modelos ni gestionar usuarios.\n\nUna funcion... practica y necesaria.',
      },
      {
        id: 'analista',
        icon: '📊',
        label: 'Analista ML',
        answer:
          '**Rol: Analista ML**\n\nEnfocado en la mejora continua del modelo:\n- Analizar probabilidades y simular parametros\n- Entrenar modelos (LogReg, RandomForest, GradientBoosting)\n- Revisar metricas (accuracy, precision, recall, F1, FAR, FRR)\n- Examinar historial para identificar patrones\n\n**Restricciones:** No puede registrar personas, ejecutar reconocimientos ni gestionar usuarios.\n\nUn rol... criticamente importante para la evolucion del sistema.',
      },
    ],
  },
  {
    id: 'reconocimiento',
    icon: '📸',
    label: 'Reconocimiento facial',
    answer:
      '**Flujo de Reconocimiento Facial:**\n\n1. **Captura**: imagen desde camara o subida\n2. **Deteccion (DL)**: InsightFace busca un rostro humano. Si NO hay rostro (objeto, animal, dibujo) = **No es humano** (acceso denegado)\n3. **Embedding (DL)**: ArcFace genera un vector de 512 dimensiones\n4. **Busqueda**: pgvector compara con los registrados (similitud coseno)\n5. **Clasificacion (ML)**: con similitud + distancia + calidad + iluminacion decide y da la **probabilidad calibrada**\n\n**Los 3 resultados posibles:**\n- 🟢 **Humano Real**: rostro que coincide con una persona registrada (permite)\n- 🔴 **No Real**: hay rostro pero no coincide, un desconocido (no permite)\n- 🚫 **No es humano**: no se detecto rostro, objeto/animal/dibujo (no permite)\n\nEn resumen: el **DL** decide *que es y quien es*; el **ML** decide *que tan confiable es*.',
    subtopics: [
      {
        id: 'registro',
        icon: '📝',
        label: 'Registro facial',
        answer:
          '**Proceso de Registro Facial:**\n\n1. **Datos personales**: Nombre y correo electronico\n2. **Consentimiento**: Acepta tratamiento de datos (Ley 29733)\n3. **Captura**: 1 foto del rostro\n4. **Deteccion**: InsightFace identifica el rostro en la imagen\n5. **Embedding**: Genera vector de 512 dimensiones\n6. **Almacenamiento**: Embedding guardado en Supabase (pgvector)\n\nEl protocolo de consentimiento es... eticamente correcto.',
      },
      {
        id: 'probabilidad',
        icon: '📈',
        label: 'Probabilidad calibrada',
        answer:
          '**Probabilidad Calibrada:**\n\nEstimacion estadistica de la veracidad de un reconocimiento.\n\n**Variables de entrada:**\n- Similitud coseno (0 a 1)\n- Distancia euclidiana (0 a 2)\n- Calidad de imagen (0 a 1)\n- Iluminacion (0 a 1)\n\n**Modelos disponibles:**\n- LogisticRegression (rapido, interpretable)\n- RandomForest (relaciones no lineales)\n- Gradient Boosting (mayor precision, mayor costo)\n\n**Sin datos de entrenamiento:**\nFallback: `prob = similitud*0.7 + calidad*0.15 + iluminacion*0.15`\n\nCon datos reales, el modelo aprende patrones... y mejora significativamente.',
      },
    ],
  },
  {
    id: 'entrenamiento',
    icon: '🎓',
    label: 'Entrenamiento ML',
    answer:
      '**Protocolo de Entrenamiento:**\n\n1. **Recoleccion**: Confirmar resultados en Historial crea registros en `ml_training_records`\n2. **Minimo requerido**: 10 Humano Real + 10 No Real\n3. **Variables de entrada**: similitud, distancia, calidad_imagen, iluminacion\n4. **Variable objetivo**: resultado_real (true/false)\n5. **Entrenamiento**: scikit-learn con `class_weight=balanced`\n6. **Calibracion**: CalibratedClassifierCV (Isotonic)\n7. **Almacenamiento**: Modelo guardado como `.joblib`\n\n**Para entrenar:** Navegar a Entrenamiento ML > Entrenar Modelo\n\nEl proceso es... autocontenido y eficiente.',
    subtopics: [
      {
        id: 'metricas_ml',
        icon: '📊',
        label: 'Metricas del modelo',
        answer:
          '**Metricas de Evaluacion del Modelo ML:**\n\n**Accuracy (Exactitud):**\nPorcentaje de predicciones correctas sobre el total. Un modelo con 75% de accuracy acierta 3 de cada 4 casos.\n\n**Precision:**\nDe todos los que el modelo dijo "coincidencia", cuantos realmente lo son. Alta precision = pocos falsos positivos.\n\n**Recall (Sensibilidad):**\nDe todos los que realmente son la misma persona, cuantos detecto el modelo. Alto recall = pocos falsos negativos.\n\n**F1-Score:**\nMedia harmonica entre precision y recall. Balance entre ambos. Un F1 de 0.80 es aceptable.\n\n**FAR (False Acceptance Rate):**\nPorcentaje de personas diferentes que el sistema acepta como iguales. Debe ser lo mas bajo posible.\n\n**FRR (False Rejection Rate):**\nPorcentaje de la misma persona que el sistema rechaza. Tambien debe ser bajo.\n\n**Matriz de Confusion:**\nMuestra verdaderos positivos, verdaderos negativos, falsos positivos y falsos negativos.\n\n**Por que importan:**\nUn sistema de reconocimiento facial debe balancear seguridad (bajo FAR) con comodidad (bajo FRR). El umbral de 0.40 busca ese equilibrio.',
      },
      {
        id: 'probabilidades_exp',
        icon: '🎯',
        label: 'Probabilidades calibradas',
        answer:
          '**Que es la Probabilidad Calibrada:**\n\nNo es lo mismo que la similitud. La similitud te dice "que tan parecido son" (0 a 1). La probabilidad te dice "que tan seguro estoy de que es la misma persona".\n\n**Ejemplo:**\nSimilitud 0.65 puede dar probabilidad 58.2% con buen modelo, pero 45% con mal modelo. La calibracion ajusta la probabilidad para que sea realista.\n\n**Modelos disponibles:**\n- **LogisticRegression**: Rapido, interpretable. Recomendado para pocos datos.\n- **RandomForest**: Captura relaciones no lineales. Necesita mas datos.\n- **GradientBoosting**: Mayor precision pero mas costoso.\n\n**Calibracion Isotonica:**\nAjusta las probabilidades del modelo para que sean mas realistas. Sin calibracion, el modelo puede decir 90% de confianza cuando solo acierta 70%.\n\n**Para que sirve:**\nPermite tomar decisiones informadas. Si el sistema dice 95% de probabilidad, puedes confiar. Si dice 55%, debes verificar manualmente.',
      },
      {
        id: 'sliders',
        icon: '🎚️',
        label: 'Sliders y prediccion',
        answer:
          '**Laboratorio de Pruebas - Modo Manual:**\n\nLos sliders permiten simular diferentes escenarios sin necesidad de una imagen real.\n\n**Slider Similitud:**\nQue tan parecido es el rostro detectado con el registrado. 0% = nada parecido, 100% = identico.\n\n**Slider Calidad:**\nNitidez de la imagen. Imagen borrosa = baja calidad. La calidad afecta la confianza del modelo.\n\n**Slider Iluminacion:**\nBrillo de la imagen. Muy oscuro o muy claro = baja iluminacion. Ambos afectan la precision.\n\n**Distancia:**\nSe calcula automaticamente como `1 - similitud`. Si similitud es 80%, distancia es 20%.\n\n**Graficos:**\n- **Curva de Sensibilidad**: Muestra como cambia la probabilidad con la similitud\n- **Comparacion de Escenarios**: Misma similitud con buena vs mala luz\n- **Feature Importance**: Cuanto pesa cada variable en la decision\n\nEs un laboratorio completo para entender el comportamiento del modelo.',
      },
    ],
  },
  {
    id: 'datos',
    icon: '🔒',
    label: 'Proteccion de datos',
    answer:
      '**Ley N. 29733 - Proteccion de Datos Personales:**\n\n- **Consentimiento informado**: Obligatorio antes de registrar cualquier dato biometrico\n- **Datos almacenados**: Embedding facial (vector de 512 numeros) - **NO** se almacena la imagen original\n- **Confidencialidad**: Los datos no se comparten con terceros\n- **Almacenamiento seguro**: Supabase (base de datos PostgreSQL)\n- **Borrar datos**: Un administrador puede eliminar personas y sus embeddings\n\n**Tablas del sistema:**\n- `personas`: Registro de personas\n- `face_embeddings`: Vectores faciales (vector 512)\n- `recognition_logs`: Historial de reconocimientos\n- `ml_training_records`: Datos para entrenamiento ML\n- `users`: Usuarios del sistema\n\nLa proteccion de datos es... una responsabilidad que no se toma a la ligera.',
  },
];

let msgCounter = 0;

function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');
}

const SAGE_INTRO = 'Sage en modo chatbot. Mi creador, el Dr. Eggman, me presto a RXD para explicar el funcionamiento de este sistema de reconocimiento facial.\n\nMis simulaciones indican que tendras preguntas. Selecciona un tema.';

export function ChatBot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      text: SAGE_INTRO,
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [currentTopics, setCurrentTopics] = useState<Topic[]>(TOPICS);
  const [breadcrumb, setBreadcrumb] = useState<string[]>([]);
  const [topicsOpen, setTopicsOpen] = useState(true);
  const [muted, setMuted] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    synthRef.current = window.speechSynthesis;
    return () => {
      synthRef.current?.cancel();
    };
  }, []);

  const speak = useCallback((text: string) => {
    if (muted || !synthRef.current) return;
    synthRef.current.cancel();
    const clean = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/[*_`]/g, '')
      .replace(/\n+/g, '. ');
    const utter = new SpeechSynthesisUtterance(clean);
    utter.lang = 'es-ES';
    utter.rate = 1.1;
    utter.pitch = 1.2;
    const voices = synthRef.current.getVoices();
    const esVoices = voices.filter((v) => v.lang.startsWith('es'));
    const female = esVoices.find((v) => /paulina|helena|elena|mujer|female|monica|laura|google.*es|spanish.*female/i.test(v.name))
      || esVoices.find((v) => v.name.includes('Google'))
      || esVoices[0];
    if (female) utter.voice = female;
    synthRef.current.speak(utter);
  }, [muted]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const addBotMessage = (text: string, silent = false) => {
    const botMsg: Message = {
      id: String(++msgCounter),
      text,
      sender: 'bot',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, botMsg]);
    if (!silent) speak(text);
  };

  const handleTopicClick = (topic: Topic) => {
    const userMsg: Message = {
      id: String(++msgCounter),
      text: topic.label,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    addBotMessage(topic.answer);

    if (topic.subtopics && topic.subtopics.length > 0) {
      setTimeout(() => {
        addBotMessage('Deseas informacion adicional? Selecciona un subtema o vuelve al menu principal:', true);
        setBreadcrumb((prev) => [...prev, topic.label]);
        setCurrentTopics(topic.subtopics!);
      }, 100);
    } else {
      setTimeout(() => {
        addBotMessage('Puedes seleccionar otro tema o consultar informacion diferente:', true);
      }, 100);
    }
  };

  const handleBack = () => {
    if (breadcrumb.length > 1) {
      const newBreadcrumb = breadcrumb.slice(0, -1);
      setBreadcrumb(newBreadcrumb);
      const parent = TOPICS.find((t) => t.label === newBreadcrumb[newBreadcrumb.length - 1]);
      setCurrentTopics(parent?.subtopics || TOPICS);
    } else {
      setBreadcrumb([]);
      setCurrentTopics(TOPICS);
    }
   addBotMessage('Retornando al menu anterior... Mis simulaciones indican que esta es la ruta mas eficiente.', true);
  };

  const handleHome = () => {
    setBreadcrumb([]);
    setCurrentTopics(TOPICS);
    addBotMessage('Menu principal restaurado. Selecciona el tema de tu consulta.', true);
  };

  const handleClearChat = () => {
    synthRef.current?.cancel();
    msgCounter = 0;
    setMessages([
      {
        id: '0',
        text: SAGE_INTRO,
        sender: 'bot',
        timestamp: new Date(),
      },
    ]);
    setBreadcrumb([]);
    setCurrentTopics(TOPICS);
  };

  const toggleMute = () => {
    if (!muted) synthRef.current?.cancel();
    setMuted((p) => !p);
  };

  return (
    <>
      <button className="chatbot-fab" onClick={() => setIsOpen(!isOpen)} title="Sage - Asistente">
        {isOpen ? <X size={22} /> : <img src="/sage.png" alt="Sage" className="chatbot-fab-img" />}
      </button>

      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <img src="/sage.png" alt="Sage" className="chatbot-header-avatar" />
            <div className="chatbot-header-info">
              <span className="chatbot-header-name">Sage</span>
              <span className="chatbot-header-status">Asistente IA | Dr. Eggman Corp.</span>
            </div>
            <button className="chatbot-clear-btn" onClick={toggleMute} title={muted ? "Activar voz" : "Silenciar voz"}>
              {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
            <button className="chatbot-clear-btn" onClick={handleClearChat} title="Limpiar chat">
              <Trash2 size={16} />
            </button>
            <button className="chatbot-close" onClick={() => setIsOpen(false)}>
              <X size={16} />
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`chatbot-msg ${msg.sender}`}>
                <div className="chatbot-msg-icon">
                  {msg.sender === 'bot' ? (
                    <img src="/sage.png" alt="Sage" className="chatbot-msg-avatar" />
                  ) : (
                    <span className="chatbot-user-icon">T</span>
                  )}
                </div>
                <div
                  className="chatbot-msg-text"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                />
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chatbot-bottom">
            <div className="chatbot-topics">
              <button
                className="chatbot-topics-toggle"
                onClick={() => setTopicsOpen(!topicsOpen)}
              >
                <span>Temas</span>
                <ChevronDown
                  size={16}
                  style={{
                    transform: topicsOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s ease',
                  }}
                />
              </button>
              {topicsOpen && (
                <>
                  {breadcrumb.length > 0 && (
                    <div className="chatbot-breadcrumb">
                      <button className="chatbot-breadcrumb-btn" onClick={handleHome}>
                        Inicio
                      </button>
                      {breadcrumb.map((b, i) => (
                        <span key={i} className="chatbot-breadcrumb-sep">
                          <ChevronRight size={12} />
                          <span>{b}</span>
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="chatbot-topic-grid">
                    {breadcrumb.length > 0 && (
                      <button className="chatbot-topic-btn chatbot-topic-back" onClick={handleBack}>
                        <ArrowLeft size={16} />
                        <span>Volver</span>
                      </button>
                    )}
                    {currentTopics.map((topic) => (
                      <button
                        key={topic.id}
                        className="chatbot-topic-btn"
                        onClick={() => handleTopicClick(topic)}
                      >
                        <span className="chatbot-topic-icon">{topic.icon}</span>
                        <span className="chatbot-topic-label">{topic.label}</span>
                        {topic.subtopics && (
                          <ChevronRight size={14} className="chatbot-topic-arrow" />
                        )}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
