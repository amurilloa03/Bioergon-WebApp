# Constructor de Formularios - Documentación

## 📋 Descripción General

El Constructor de Formularios es una aplicación React moderna que permite crear formularios dinámicos con múltiples tipos de preguntas de forma visual e intuitiva.

## 🎯 Características Principales

### Tipos de Preguntas Soportadas

1. **📝 Respuesta Corta** - Campos de texto simple de una línea
2. **📄 Respuesta Larga** - Áreas de texto multilínea
3. **◉ Opción Múltiple** - Una sola opción seleccionable (radio buttons)
4. **☑ Casillas (Multi)** - Múltiples opciones seleccionables (checkboxes)
5. **▼ Desplegable** - Lista desplegable de opciones
6. **⭐ Calificación** - Escala de calificación de 1 a 5 estrellas
7. **📅 Fecha** - Selector de fecha

### Funcionalidades

- ✅ Crear preguntas de diferentes tipos
- ✅ Editar el título y descripción del formulario
- ✅ Reordenar preguntas (mover arriba/abajo)
- ✅ Duplicar preguntas
- ✅ Marcar preguntas como obligatorias
- ✅ Gestionar opciones para preguntas de opción múltiple
- ✅ Vista previa interactiva del formulario
- ✅ Exportar formulario como JSON
- ✅ Limpiar formulario completo

## 🚀 Cómo Usar

### Crear un Formulario

1. **Ingresar Título**: En el campo superior, ingresa el título del formulario
2. **Agregar Descripción (Opcional)**: Añade una descripción para dar más contexto
3. **Añadir Preguntas**: Haz clic en uno de los botones en el panel derecho para añadir una pregunta del tipo deseado

### Editar Preguntas

1. **Seleccionar Pregunta**: Haz clic en una tarjeta de pregunta para seleccionarla
2. **Editar Propiedades**: En el panel derecho aparecerá un formulario para editar:
   - Texto de la pregunta
   - Marcar como obligatoria
   - Opciones (si aplica)

### Gestionar Opciones

Para preguntas de opción múltiple, casillas o desplegables:
- Edita cada opción en el campo de texto
- Añade nuevas opciones con el botón "+ Añadir Opción"
- Elimina opciones con el botón "✕" (no puedes eliminar todas)

### Reordenar Preguntas

- Usa los botones **↑** y **↓** en cada tarjeta para mover preguntas
- El botón ↑ está deshabilitado en la primera pregunta
- El botón ↓ está deshabilitado en la última pregunta

### Vista Previa

1. Haz clic en el botón **"Vista Previa"** en la cabecera
2. Visualiza cómo se verá el formulario completado
3. Interactúa con todos los elementos
4. Haz clic en **"Editar"** para volver al modo de edición

### Exportar Formulario

1. Haz clic en **"Descargar JSON"**
2. Se descargará un archivo JSON con toda la estructura del formulario
3. Este archivo puede ser importado en futuras sesiones

### Estructura del JSON Exportado

```json
{
  "title": "Título del Formulario",
  "description": "Descripción del formulario",
  "questions": [
    {
      "id": 1234567890,
      "type": "short-text",
      "question": "¿Cuál es tu nombre?",
      "required": true,
      "options": []
    },
    {
      "id": 1234567891,
      "type": "multiple-choice",
      "question": "¿Cuál es tu edad?",
      "required": true,
      "options": ["18-25", "26-35", "36-45", "46+"]
    }
  ],
  "createdAt": "2025-11-18T10:30:00.000Z"
}
```

## 🎨 Interfaz

### Panel Izquierdo - Editor Principal
- Título y descripción del formulario
- Lista de preguntas creadas
- Cada pregunta muestra número, tipo y vista previa

### Panel Derecho - Herramientas
- Botones para añadir nuevos tipos de preguntas
- Panel de edición de la pregunta seleccionada

### Cabecera
- Botón "Vista Previa" para ver cómo se vería el formulario
- Botón "Descargar JSON" para exportar
- Botón "Limpiar" para resetear todo

## 📱 Responsividad

La aplicación se adapta a diferentes tamaños de pantalla:
- **Desktop**: Layout de dos columnas (editor + panel de herramientas)
- **Tablet**: Layout comprimido con panel de herramientas colapsable
- **Mobile**: Panel de herramientas solo en vista de edición detallada

## 💾 Datos

- Los formularios se guardan en memoria durante la sesión
- Para persistencia, exporta el JSON a un archivo
- Los datos NO se guardan automáticamente al cerrar la aplicación

## 🔒 Validaciones

- Se requiere al menos el título del formulario
- Las preguntas sin texto se marcan como "Sin pregunta aún"
- Para preguntas de opción múltiple se requiere al menos 1 opción
- Las fechas se validan en la vista previa

## ⚙️ Configuración Técnica

- **Framework**: React 19
- **Estilos**: CSS3 con gradientes y transiciones
- **Sin dependencias externas**: Formulario completamente funcional sin librerías adicionales

## 🐛 Troubleshooting

**P: No veo las preguntas que agregué**
R: Asegúrate de haber clickeado en uno de los botones de tipo de pregunta en el panel derecho.

**P: No puedo eliminar todas las opciones**
R: Es correcto, las preguntas de opción múltiple necesitan al menos una opción.

**P: ¿Dónde se guardan mis formularios?**
R: Se guardan en la memoria del navegador durante la sesión. Usa "Descargar JSON" para guardar permanentemente.

**P: ¿Puedo importar un formulario anterior?**
R: Actualmente no hay función de importación. Deberás recrear el formulario o modificar manualmente el JSON.

---

**Versión**: 1.0.0
**Última Actualización**: 18 de Noviembre de 2025
