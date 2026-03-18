# 📋 Forms Creator

Un sistema completo para crear, gestionar y responder formularios dinámicos. Construido con **Flask** (backend) y **React** (frontend), con almacenamiento en **SQLite** y **JSON**.

## ✨ Características

### 🎨 Form Builder
- **9 tipos de preguntas soportadas:**
  - Texto corto
  - Texto largo
  - Opción múltiple
  - Casillas de verificación
  - Lista desplegable
  - Calificación (estrellas)
  - Fecha
  - **Mapa Muscular (Espalda)** 🖐️
  - **Mapa de Mano** ✋

- **Interfaz moderna** con 3 columnas:
  - Panel de tipos de preguntas
  - Vista previa en tiempo real
  - Editor de propiedades

- **Funcionalidades avanzadas:**
  - [x] Agregar/eliminar preguntas
  - [x] Reordenar preguntas (mover arriba/abajo)
  - [x] Marcar preguntas como requeridas
  - [x] Previsualización antes de guardar
  - [x] Descripción y título para cada formulario
  - [x] **Historial de versiones:** Guardado automático y restauración de versiones anteriores
  - [x] **Temas personalizables:** Soporte para múltiples esquemas de colores (Oscuro, Natura, Púrpura, Océano)
  - [x] **Lógica condicional:** Mostrar preguntas basadas en respuestas anteriores

### 📝 Respondedor de Formularios
- Interfaz amigable para usuarios finales
- Validación de campos requeridos
- Se abre en nueva pestaña
- Almacenamiento de respuestas en JSON + Base de datos
- Soporte para **Mapas Corporales Interactivos** (Espalda y Mano)

### 📊 Visualización de Respuestas
- Los **administradores** pueden ver **todas las respuestas** del sistema
- Los **usuarios** ven solo sus propias respuestas
- Visualización de respuestas como formulario **relleno y read-only**
- Incluye fecha, hora y usuario que respondió
- **Exportación de datos:** Descarga de respuestas en formato CSV
- **Integración con Email:** Envío de resúmenes vía Gmail

### 🔐 Control de Acceso
- Sistema de autenticación con contraseñas hasheadas
- Roles: Usuario normal vs Administrador
- Permisos específicos por rol
- Edición de formularios solo por administrador
- Soporte para **Google OAuth** (Inicio de sesión con Google)

## 🛠️ Tecnologías

### Backend
- **Flask** - Framework web Python
- **SQLAlchemy** - ORM para base de datos
- **SQLite** - Base de datos
- **Python 3.13**

### Frontend
- **React 19.2.0** - UI framework
- **Vanilla CSS** - Estilos personalizados
- **Chart.js** - Visualización de datos y estadísticas

### Almacenamiento
- **SQLite** (forms.db) - Datos maestros y respuestas
- **JSON** (formularios/) - Estructura completa de formularios
- **JSON** (respuestas/) - Respuestas de usuarios
- **Versiones JSON** (formularios/versiones/) - Historial de cambios automáticos

## 📁 Estructura del Proyecto

```
Forms_creator/
├── app.py                    # Backend Flask
├── forms.db                  # Base de datos SQLite
├── requirements.txt          # Dependencias Python
├── package.json              # Dependencias Node
│
├── form_builder/             # React App (Frontend)
│   ├── src/
│   │   ├── components/
│   │   │   ├── FormBuilder.js      # Editor de formularios
│   │   │   ├── FormResponder.js    # Respondedor
│   │   │   └── StatsDashboard.js   # Panel de estadísticas
│   │   └── styles/           # Estilos CSS
│   └── build/                # Build compilado
│
├── formularios/              # JSON de formularios
│   ├── *.json               # {nombre_formulario}.json
│   └── versiones/           # Historial de versiones automáticas
│
├── respuestas/              # JSON de respuestas
│   └── *.json               # formulario_{id}_{user}_{timestamp}.json
│
├── static/
│   ├── css/                 # Estilos CSS
│   └── images/              # Imágenes (incluye mapas anatómicos)
│
├── Templates/               # HTML templates Jinja2
└── README.md                # Este archivo
```

## 🚀 Instalación

### Requisitos previos
- Python 3.13+
- Node.js 18+

### Pasos de instalación

1. **Instalar dependencias Python**
```bash
pip install -r requirements.txt
```

2. **Compilar Frontend**
```bash
cd form_builder && npm install && npm run build && cd ..
```

3. **Ejecutar servidor**
```bash
python app.py
```

El servidor estará disponible en `http://127.0.0.1:5000`

## 📖 Uso rápido

### Credenciales predeterminadas
- **Admin:** Pepe / 12345
- **Usuario:** Manolo / 12345

## 🎯 Mejoras futuras
- [ ] Análisis estadísticos visuales con **Mapas de Calor (Heatmaps)**
- [ ] Acceso colaborativo a formularios
- [ ] API pública para integración con terceros
- [ ] Búsqueda avanzada y filtros en respuestas

## 🐛 Conocidas limitaciones
- Las respuestas una vez enviadas no se pueden editar por el usuario
- Máximo 1 respuesta funcional sugerida por usuario por formulario
