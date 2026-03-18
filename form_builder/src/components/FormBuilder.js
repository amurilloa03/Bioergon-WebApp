import React, { useState, useEffect } from "react";
import "../styles/FormBuilder.css";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

function FormBuilder() {


    const [formTitle, setFormTitle] = useState("Mi Formulario");
    const [formDescription, setFormDescription] = useState("");
    const [questions, setQuestions] = useState([]);
    const [selectedQuestionId, setSelectedQuestionId] = useState(null);
    const [formId, setFormId] = useState(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState("");
    const [isPreview, setIsPreview] = useState(false);
    const [theme, setTheme] = useState("default");
    const [versions, setVersions] = useState([]);
    const [showVersions, setShowVersions] = useState(false);


    const themes = [
        { id: 'default', label: 'Estándar', color: '#667eea', bg: '#f0f2f5' },
        { id: 'dark', label: 'Oscuro Moderno', color: '#BB86FC', bg: '#121212' },
        { id: 'nature', label: 'Verde Natura', color: '#2d6a4f', bg: '#f1f8e9' },
        { id: 'purple', label: 'Púrpura Real', color: '#8e44ad', bg: '#f3e5f5' },
        { id: 'ocean', label: 'Azul Océano', color: '#0077b6', bg: '#e0f7fa' },
        { id: 'sunset', label: 'Atardecer Coral', color: '#FF5A5F', bg: '#FFF8F6' },
        { id: 'cherry', label: 'Cerezo Pastel', color: '#FF9EBB', bg: '#FFF0F5' },
        { id: 'earth', label: 'Moka Tierra', color: '#8D6E63', bg: '#EFEBE9' },
        { id: 'midnight', label: 'Azul Medianoche', color: '#4FC3F7', bg: '#0F172A' },
        { id: 'sunny', label: 'Amarillo Solar', color: '#F59E0B', bg: '#FFFBEB' }
    ];


    // ==========================================
    // 1. AQUÍ ESTÁ EL PRIMER CAMBIO (Línea 21)
    // Hemos añadido la última línea del Mapa Muscular
    // ==========================================
    const questionTypes = [
        { type: 'short-text', label: 'Texto corto', emoji: '📝' },
        { type: 'long-text', label: 'Texto largo', emoji: '📄' },
        { type: 'multiple-choice', label: 'Opción múltiple', emoji: '⭕' },
        { type: 'checkbox', label: 'Casillas', emoji: '✅' },
        { type: 'dropdown', label: 'Dropdown', emoji: '⬇️' },
        { type: 'rating', label: 'Calificación', emoji: '⭐' },
        { type: 'date', label: 'Fecha', emoji: '📅' },
        { type: 'muscle-map', label: 'Mapa Muscular', emoji: '🖐️' },
        { type: 'hand-map', label: 'Mapa de Mano', emoji: '✋' } // <--- ¡NUEVO!
    ];

    // Cargar formulario existente si tiene ID
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const id = params.get('form_id');
        if (id) {
            setFormId(id);
            loadFormData(id);
        }
    }, []);

    const loadFormData = async (id) => {
        try {
            const response = await fetch(`/api/formularios/${id}`);
            if (response.ok) {
                const data = await response.json();
                setFormTitle(data.title || "Mi Formulario");
                setFormDescription(data.description || "");
                setTheme(data.theme || "default");
                const questionsWithIds = (data.questions || []).map((q, idx) => ({

                    ...q,
                    id: q.id || Date.now() + idx
                }));
                setQuestions(questionsWithIds);
            }
        } catch (error) {
            console.error("Error cargando formulario:", error);
        }
    };

    const addQuestion = (type) => {
        const newQuestion = {
            id: Date.now(),
            type,
            text: "",
            required: false,
            options: (type === "multiple-choice" || type === "checkbox" || type === "dropdown") ? ["Opción 1", "Opción 2"] : [],
            image: null
        };
        setQuestions([...questions, newQuestion]);
        setSelectedQuestionId(newQuestion.id);
    };

    const updateQuestion = (id, updatedData) => {
        setQuestions(questions.map(q => q.id === id ? { ...q, ...updatedData } : q));
    };

    const deleteQuestion = (id) => {
        setQuestions(questions.filter(q => q.id !== id));
        if (selectedQuestionId === id) {
            setSelectedQuestionId(null);
        }
    };

    const onDragStart = () => {
        document.body.classList.add('is-dragging');
    };

    const onDragEnd = (result) => {
        document.body.classList.remove('is-dragging');
        if (!result.destination) return;
        const newQuestions = Array.from(questions);
        const [reorderedItem] = newQuestions.splice(result.source.index, 1);
        newQuestions.splice(result.destination.index, 0, reorderedItem);
        setQuestions(newQuestions);
    };

    const selectedQuestion = questions.find(q => q.id === selectedQuestionId);

    const renderQuestionInput = (question) => {
        switch (question.type) {
            case 'short-text':
                return <input type="text" className="preview-input" placeholder="Tu respuesta" />;
            case 'long-text':
                return <textarea className="preview-input" placeholder="Tu respuesta" rows="4" />;
            case 'multiple-choice':
                return (
                    <div className="preview-options">
                        {question.options.map((opt, idx) => (
                            <label key={idx} className="preview-option">
                                <input type="radio" name={`q-${question.id}`} value={opt} />
                                <span>{opt}</span>
                            </label>
                        ))}
                    </div>
                );
            case 'checkbox':
                return (
                    <div className="preview-options">
                        {question.options.map((opt, idx) => (
                            <label key={idx} className="preview-option">
                                <input type="checkbox" value={opt} />
                                <span>{opt}</span>
                            </label>
                        ))}
                    </div>
                );
            case 'dropdown':
                return (
                    <select className="preview-input" defaultValue="">
                        <option value="" disabled>Selecciona una opción</option>
                        {question.options.map((opt, idx) => (
                            <option key={idx} value={opt}>{opt}</option>
                        ))}
                    </select>
                );
            case 'rating':
                return (
                    <div className="preview-rating">
                        {[1, 2, 3, 4, 5].map(star => (
                            <button key={star} className="star-btn" type="button">⭐</button>
                        ))}
                    </div>
                );
            case 'date':
                return <input type="date" className="preview-input" />;

            // ==========================================
            // 2. AQUÍ ESTÁ EL SEGUNDO CAMBIO (Línea 145)
            // Esto le dice al programa cómo dibujar el mapa en el editor
            // ==========================================
            case 'muscle-map':
                return (
                    <div className="preview-muscle-map" style={{
                        border: '2px dashed #667eea',
                        padding: '20px',
                        textAlign: 'center',
                        background: 'rgba(102, 126, 234, 0.05)',
                        borderRadius: '8px',
                        color: '#667eea'
                    }}>
                        <div style={{ fontSize: '24px', marginBottom: '10px' }}>🖐️</div>
                        <strong>Mapa Corporal Interactivo</strong>
                        <p style={{ fontSize: '12px', margin: '5px 0 0' }}>
                            Vista previa del diagrama anatómico.
                        </p>
                    </div>
                );
            case 'hand-map':
                return (
                    <div className="preview-muscle-map" style={{
                        border: '2px dashed #ff6b6b',
                        padding: '20px',
                        textAlign: 'center',
                        background: 'rgba(255, 107, 107, 0.05)',
                        borderRadius: '8px',
                        color: '#ff6b6b'
                    }}>
                        <div style={{ fontSize: '24px', marginBottom: '10px' }}>✋</div>
                        <strong>Mapa de Mano Interactivo</strong>
                        <p style={{ fontSize: '12px', margin: '5px 0 0' }}>
                            Vista previa del diagrama de la mano.
                        </p>
                    </div>
                );
            default:
                return null;
        }
    };

    const getCsrfToken = () => {
        const name = 'csrf_token=';
        const decodedCookie = decodeURIComponent(document.cookie);
        const ca = decodedCookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        return '';
    };

    const saveForm = async () => {
        setIsSaving(true);
        setSaveMessage("");
        try {
            const method = formId ? 'PUT' : 'POST';
            const url = formId ? `/api/formularios/${formId}` : '/api/formularios';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    title: formTitle,
                    description: formDescription,
                    theme: theme,
                    questions: questions
                })

            });

            if (response.ok) {
                const data = await response.json();
                if (!formId) {
                    setFormId(data.form_id);
                    window.history.replaceState({}, '', `/form-builder?form_id=${data.form_id}`);
                }
                setSaveMessage("✓ Formulario guardado correctamente");
                setTimeout(() => setSaveMessage(""), 3000);
            } else {
                setSaveMessage("✗ Error al guardar el formulario");
            }
        } catch (error) {
            console.error("Error guardando formulario:", error);
            setSaveMessage("✗ Error al guardar el formulario");
        } finally {
            setIsSaving(false);
        }
    };

    const loadVersions = async () => {
        if (!formId) return;
        try {
            const response = await fetch(`/api/formularios/${formId}/versiones`);
            if (response.ok) {
                const data = await response.json();
                setVersions(data);
                setShowVersions(true);
            }
        } catch (error) {
            console.error("Error cargando versiones:", error);
        }
    };

    const restoreVersion = async (filename) => {
        if (!window.confirm("¿Estás seguro de que quieres restaurar esta versión? Se guardará una copia del estado actual antes de restaurar.")) return;

        try {
            const response = await fetch(`/api/formularios/${formId}/restaurar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ filename })
            });

            if (response.ok) {
                setShowVersions(false);
                loadFormData(formId); // Recargar datos
                setSaveMessage("✓ Versión restaurada");
                setTimeout(() => setSaveMessage(""), 3000);
            } else {
                alert("Error al restaurar versión");
            }
        } catch (error) {
            console.error("Error restaurando versión:", error);
            alert("Error de conexión");
        }
    };

    const clearHistory = async () => {
        if (!window.confirm("¿Estás seguro de que quieres borrar todo el historial? Esta acción no se puede deshacer.")) return;

        try {
            const response = await fetch(`/api/formularios/${formId}/versiones`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() }
            });

            if (response.ok) {
                setVersions([]);
                setShowVersions(false);
                setSaveMessage("✓ Historial borrado");
                setTimeout(() => setSaveMessage(""), 3000);
            } else {
                alert("Error al borrar historial");
            }
        } catch (error) {
            console.error("Error borrando historial:", error);
            alert("Error de conexión");
        }
    };

    const handleImageUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch('/api/upload-image', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                updateQuestion(selectedQuestionId, { image: data.url });
            } else {
                const errorData = await response.json();
                alert(`Error al subir la imagen: ${errorData.error || 'Error desconocido'}`);
            }
        } catch (error) {
            console.error("Error subiendo imagen:", error);
            alert("Error de conexión al subir la imagen");
        }
    };

    return (
        <div className={`form-builder-wrapper theme-${theme}`}>

            {/* Header */}
            <header className="fb-header">
                <div className="fb-header-content">
                    <h1>📋 Constructor de Formularios</h1>
                    <div className="fb-header-buttons">
                        <button className="fb-btn-save-header fb-btn-back" onClick={() => window.location.href = '/formularios'}>
                            🏠 Volver
                        </button>
                        <button className="fb-btn-save-header fb-btn-preview" onClick={() => setIsPreview(!isPreview)}>
                            {isPreview ? "✏️ Editar" : "👁️ Previsualizar"}
                        </button>
                        {formId && !isPreview && (
                            <button className="fb-btn-save-header fb-btn-history" onClick={loadVersions} title="Historial de versiones">
                                🕒 Historial
                            </button>
                        )}
                        <button className="fb-btn-save-header" onClick={saveForm} disabled={isSaving || isPreview}>
                            {isSaving ? "Guardando..." : "💾 Guardar"}
                        </button>

                    </div>
                    {saveMessage && <div className="fb-save-message">{saveMessage}</div>}
                </div>
            </header>

            {/* Main Content */}
            <main className="fb-main">
                {isPreview ? (
                    // MODO PREVISUALIZACIÓN
                    <div className="fb-preview-container">
                        <div className={`preview-card theme-${theme}`}>

                            <h2 className="preview-title">{formTitle}</h2>
                            {formDescription && <p className="preview-description">{formDescription}</p>}

                            {questions.length === 0 ? (
                                <p className="preview-empty">No hay preguntas en este formulario</p>
                            ) : (
                                <form className="preview-form">
                                    {questions.map((question, index) => (
                                        <div key={question.id} className="preview-question">
                                            <label className="preview-question-label">
                                                <span className="preview-q-number">{index + 1}.</span>
                                                <span className="preview-q-text">{question.text || `Pregunta ${index + 1}`}</span>
                                                {question.required && <span className="preview-required">*</span>}
                                            </label>
                                            <div className="preview-input-wrapper">
                                                {question.image && (
                                                    <div className="preview-question-image" style={{ marginBottom: '15px', textAlign: 'center' }}>
                                                        <img src={question.image} alt="Pregunta" style={{ maxWidth: '100%', maxHeight: '400px', borderRadius: '8px' }} />
                                                    </div>
                                                )}
                                                {renderQuestionInput(question)}
                                            </div>
                                        </div>
                                    ))}
                                    <button type="submit" className="preview-submit-btn">Enviar Respuestas</button>
                                </form>
                            )}
                        </div>
                    </div>
                ) : (
                    // MODO EDICIÓN
                    <div className="fb-container">
                        {/* Sidebar izquierdo - Tipos de preguntas */}
                        <aside className="fb-sidebar-left">
                            <h3>Tipos de Preguntas</h3>
                            <div className="fb-question-types">
                                {questionTypes.map(qt => (
                                    <button
                                        key={qt.type}
                                        className="fb-type-btn"
                                        onClick={() => addQuestion(qt.type)}
                                        title={qt.label}
                                    >
                                        <span className="fb-type-emoji">{qt.emoji}</span>
                                        <span className="fb-type-label">{qt.label}</span>
                                    </button>
                                ))}
                            </div>

                            <div className="fb-themes-section">
                                <h3>🎨 Temas</h3>
                                <div className="fb-themes-grid">
                                    {themes.map(t => (
                                        <button
                                            key={t.id}
                                            className={`fb-theme-btn ${theme === t.id ? 'active' : ''}`}
                                            onClick={() => setTheme(t.id)}
                                            style={{ '--theme-color': t.color, '--theme-bg': t.bg }}
                                        >
                                            <div className="fb-theme-preview">
                                                <div className="fb-theme-swatch" style={{ background: t.color }}></div>
                                            </div>
                                            <span>{t.label}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </aside>


                        {/* Centro - Preview de preguntas */}
                        <div className="fb-center">
                            <div className="fb-form-header">
                                <input
                                    type="text"
                                    value={formTitle}
                                    onChange={(e) => setFormTitle(e.target.value)}
                                    className="fb-title-input"
                                    placeholder="Título del formulario"
                                />
                                <textarea
                                    value={formDescription}
                                    onChange={(e) => setFormDescription(e.target.value)}
                                    className="fb-description-input"
                                    placeholder="Descripción (opcional)"
                                    rows="2"
                                />
                            </div>

                            {questions.length === 0 ? (
                                <div className="fb-empty-state">
                                    <p>📋 Añade preguntas para empezar a crear tu formulario</p>
                                </div>
                            ) : (
                                <DragDropContext onDragStart={onDragStart} onDragEnd={onDragEnd}>
                                    <Droppable droppableId="questions-list">
                                        {(provided) => (
                                            <div
                                                className="fb-questions-container"
                                                {...provided.droppableProps}
                                                ref={provided.innerRef}
                                            >
                                                {questions.map((question, index) => (
                                                    <Draggable
                                                        key={question.id.toString()}
                                                        draggableId={question.id.toString()}
                                                        index={index}
                                                    >
                                                        {(provided, snapshot) => (
                                                            <div
                                                                ref={provided.innerRef}
                                                                {...provided.draggableProps}
                                                                className={`fb-question-item ${selectedQuestionId === question.id ? 'selected' : ''} ${snapshot.isDragging ? 'dragging' : ''}`}
                                                                onClick={() => setSelectedQuestionId(question.id)}
                                                            >
                                                                <div className="fb-question-header">
                                                                    <div className="fb-question-header-left">
                                                                        <div className="fb-drag-handle" {...provided.dragHandleProps} title="Arrastrar para reordenar">
                                                                            ⣿
                                                                        </div>
                                                                        <span className="fb-question-number">{index + 1}</span>
                                                                        <span className="fb-question-type">{question.type}</span>
                                                                        {question.required && <span className="fb-required">*</span>}
                                                                    </div>
                                                                </div>
                                                                <p className="fb-question-text">{question.text || `(sin texto)`}</p>
                                                                {question.options && question.options.length > 0 && (
                                                                    <p className="fb-question-options">
                                                                        {question.options.slice(0, 2).join(' • ')}
                                                                        {question.options.length > 2 && ` +${question.options.length - 2}`}
                                                                    </p>
                                                                )}

                                                                {question.type === 'muscle-map' && (
                                                                    <div style={{ fontSize: '12px', color: '#888', fontStyle: 'italic', marginTop: '5px' }}>
                                                                        [Mapa Corporal Interactivo]
                                                                    </div>
                                                                )}
                                                                {question.type === 'hand-map' && (
                                                                    <div style={{ fontSize: '12px', color: '#888', fontStyle: 'italic', marginTop: '5px' }}>
                                                                        [Mapa de Mano Interactivo]
                                                                    </div>
                                                                )}

                                                                <div className="fb-question-actions">
                                                                    <button
                                                                        className="fb-delete-btn"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            deleteQuestion(question.id);
                                                                        }}
                                                                        title="Eliminar pregunta"
                                                                    >
                                                                        🗑️ Eliminar
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </Draggable>
                                                ))}
                                                {provided.placeholder}
                                            </div>
                                        )}
                                    </Droppable>
                                </DragDropContext>
                            )}
                        </div>

                        {/* Sidebar derecho - Editor de pregunta seleccionada */}
                        <aside className="fb-sidebar-right">
                            {selectedQuestion ? (
                                <div className="fb-question-editor">
                                    <h3>✏️ Editar Pregunta</h3>
                                    <input
                                        type="text"
                                        value={selectedQuestion.text}
                                        onChange={(e) => updateQuestion(selectedQuestion.id, { text: e.target.value })}
                                        className="fb-input"
                                        placeholder="Texto de la pregunta"
                                    />

                                    <label className="fb-checkbox">
                                        <input
                                            type="checkbox"
                                            checked={selectedQuestion.required}
                                            onChange={(e) => updateQuestion(selectedQuestion.id, { required: e.target.checked })}
                                        />
                                        Pregunta requerida
                                    </label>

                                    {/* --- EDITOR DE IMAGEN --- */}
                                    <div className="fb-image-editor" style={{ marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '10px' }}>
                                        <h4>🖼️ Imagen de la Pregunta</h4>
                                        {selectedQuestion.image ? (
                                            <div className="fb-image-preview-container" style={{ position: 'relative', marginBottom: '10px', marginTop: '5px' }}>
                                                <img src={selectedQuestion.image} alt="Preview" style={{ maxWidth: '100%', borderRadius: '4px', border: '1px solid #ddd' }} />
                                                <button
                                                    className="fb-remove-image-btn"
                                                    onClick={() => updateQuestion(selectedQuestion.id, { image: null })}
                                                    style={{ position: 'absolute', top: '5px', right: '5px', background: 'rgba(255,0,0,0.8)', color: 'white', border: 'none', borderRadius: '50%', width: '24px', height: '24px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}
                                                    title="Eliminar imagen"
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="fb-upload-container" style={{ marginTop: '5px' }}>
                                                <input
                                                    type="file"
                                                    id={`img-upload-${selectedQuestion.id}`}
                                                    accept="image/*"
                                                    onChange={handleImageUpload}
                                                    style={{ display: 'none' }}
                                                />
                                                <label
                                                    htmlFor={`img-upload-${selectedQuestion.id}`}
                                                    className="fb-add-option-btn"
                                                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', background: '#f8f9fa', border: '2px dashed #ccc', padding: '10px', borderRadius: '4px' }}
                                                >
                                                    📁 Seleccionar Imagen
                                                </label>
                                            </div>
                                        )}
                                    </div>

                                    {(selectedQuestion.type === "multiple-choice" || selectedQuestion.type === "checkbox" || selectedQuestion.type === "dropdown") && (
                                        <div className="fb-options-editor">
                                            <h4>Opciones</h4>
                                            {selectedQuestion.options.map((opt, idx) => (
                                                <div key={idx} className="fb-option-input-row">
                                                    <input
                                                        type="text"
                                                        value={opt}
                                                        onChange={(e) => {
                                                            const newOpts = [...selectedQuestion.options];
                                                            newOpts[idx] = e.target.value;
                                                            updateQuestion(selectedQuestion.id, { options: newOpts });
                                                        }}
                                                        className="fb-input"
                                                    />
                                                    <button
                                                        onClick={() => {
                                                            const newOpts = selectedQuestion.options.filter((_, i) => i !== idx);
                                                            updateQuestion(selectedQuestion.id, { options: newOpts });
                                                        }}
                                                        className="fb-remove-btn"
                                                    >
                                                        ✕
                                                    </button>
                                                </div>
                                            ))}
                                            <button
                                                onClick={() => updateQuestion(selectedQuestion.id, { options: [...selectedQuestion.options, "Nueva opción"] })}
                                                className="fb-add-option-btn"
                                            >
                                                + Añadir opción
                                            </button>
                                        </div>
                                    )}
                                    {/* --- LÓGICA CONDICIONAL --- */}
                                    <div className="fb-conditional-logic" style={{ marginTop: '20px', borderTop: '1px solid #ccc', paddingTop: '10px' }}>
                                        <h4>👁️ Lógica de Visibilidad</h4>
                                        <p style={{ fontSize: '12px', color: '#666', marginBottom: '10px' }}>
                                            Mostrar esta pregunta solo si una pregunta anterior tiene una respuesta específica.
                                        </p>
                                        <label className="fb-label">Depende de (Pregunta anterior):</label>
                                        <select
                                            className="fb-input"
                                            value={selectedQuestion.dependsOn || ""}
                                            onChange={(e) => {
                                                updateQuestion(selectedQuestion.id, { dependsOn: e.target.value, dependsValue: "" });
                                            }}
                                            style={{ marginBottom: '10px' }}
                                        >
                                            <option value="">(Ninguna - Siempre visible)</option>
                                            {questions
                                                .slice(0, questions.findIndex(q => q.id === selectedQuestion.id))
                                                .filter(q => ['multiple-choice', 'checkbox', 'dropdown'].includes(q.type))
                                                .map(q => (
                                                    <option key={q.id} value={q.id}>
                                                        {q.text || `Pregunta ${questions.findIndex(allQ => allQ.id === q.id) + 1}`}
                                                    </option>
                                                ))}
                                        </select>

                                        {selectedQuestion.dependsOn && (
                                            <div>
                                                <label className="fb-label">Mostrar cuando la respuesta sea:</label>
                                                <select
                                                    className="fb-input"
                                                    value={selectedQuestion.dependsValue || ""}
                                                    onChange={(e) => updateQuestion(selectedQuestion.id, { dependsValue: e.target.value })}
                                                >
                                                    <option value="">-- Selecciona una opción --</option>
                                                    {(questions.find(q => q.id.toString() === selectedQuestion.dependsOn?.toString())?.options || []).map((opt, idx) => (
                                                        <option key={idx} value={opt}>{opt}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="fb-no-selection">
                                    <p>👈 Selecciona una pregunta para editarla</p>
                                </div>
                            )}
                        </aside>
                    </div>
                )}
            </main>

            {/* Panel de Versiones */}
            {showVersions && (
                <div className="fb-versions-modal">
                    <div className="fb-versions-content">
                        <div className="fb-versions-header">
                            <h3>📜 Historial de Versiones</h3>
                            <button onClick={() => setShowVersions(false)} className="fb-close-modal">✕</button>
                        </div>
                        <div className="fb-versions-list">
                            {versions.length === 0 ? (
                                <p style={{ textAlign: 'center', padding: '20px', color: '#666' }}>No hay versiones anteriores guardadas todavía.</p>
                            ) : (
                                versions.map((v, idx) => (
                                    <div key={idx} className="fb-version-item">
                                        <div className="fb-version-info">
                                            <span className="fb-version-date">{v.fecha}</span>
                                            <span className="fb-version-size">{(v.size / 1024).toFixed(1)} KB</span>
                                        </div>
                                        <button className="fb-btn-restore" onClick={() => restoreVersion(v.filename)}>
                                            Restaurar
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                        <div className="fb-versions-footer">
                            <p>Se crea una versión nueva automáticamente cada vez que guardas.</p>
                            <button className="fb-btn-clear-history" onClick={clearHistory}>
                                🗑️ Limpiar historial completo
                            </button>
                        </div>

                    </div>
                </div>
            )}

            {/* Footer */}

            <footer className="fb-footer">
                <p>&copy; {new Date().getFullYear()} Constructor de Formularios</p>
            </footer>
        </div>
    );
}

export default FormBuilder;
