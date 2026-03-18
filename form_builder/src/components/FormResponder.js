import React, { useState, useEffect } from "react";
import "../styles/FormResponder.css";
import SelectorEspalda from './SelectorEspalda.js';
import SelectorMano from './SelectorMano';

function FormResponder() {
    const [formTitle, setFormTitle] = useState("");
    const [formDescription, setFormDescription] = useState("");
    const [questions, setQuestions] = useState([]);
    const [formId, setFormId] = useState(null);
    const [respuestas, setRespuestas] = useState({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitMessage, setSubmitMessage] = useState("");
    const [theme, setTheme] = useState("default");
    const handZoneMap = {
        'pulgar': 'ZONA A',
        'indice': 'ZONA B',
        'corazon': 'ZONA C',
        'anular': 'ZONA D',
        'menique': 'ZONA E',
        'palma': 'ZONA F'
    };


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
                setFormTitle(data.title || "Formulario");
                setFormDescription(data.description || "");
                setQuestions(data.questions || []);
                setTheme(data.theme || "default");
            }

        } catch (error) {
            console.error("Error cargando formulario:", error);
            setSubmitMessage("❌ Error al cargar el formulario");
        }
    };

    const handleInputChange = (questionId, value) => {
        setRespuestas(prev => ({
            ...prev,
            [questionId]: value
        }));
    };

    const handleCheckboxChange = (questionId, optionValue, isChecked) => {
        const current = respuestas[questionId] || [];
        let updated;

        if (isChecked) {
            updated = Array.isArray(current) ? [...current, optionValue] : [optionValue];
        } else {
            updated = Array.isArray(current) ? current.filter(v => v !== optionValue) : [];
        }

        setRespuestas(prev => ({
            ...prev,
            [questionId]: updated
        }));
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

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitMessage("");

        try {
            const response = await fetch(`/api/respuestas/${formId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ respuestas })
            });

            if (response.ok) {
                setSubmitMessage("✓ Respuestas enviadas correctamente");
                setRespuestas({});
                setTimeout(() => {
                    window.location.href = '/formularios';
                }, 2000);
            } else {
                setSubmitMessage("✗ Error al enviar las respuestas");
            }
        } catch (error) {
            console.error("Error enviando respuestas:", error);
            setSubmitMessage("✗ Error al enviar las respuestas");
        } finally {
            setIsSubmitting(false);
        }
    };

    /* const renderQuestionInput = (question) => {
         const qId = question.id;
         const value = respuestas[qId] || '';
 
         switch (question.type) {
             case 'short-text':
                 return (
                     <input
                         type="text"
                         value={value}
                         onChange={(e) => handleInputChange(qId, e.target.value)}
                         className="responder-input"
                         placeholder="Tu respuesta"
                         required={question.required}
                     />
                 );
             case 'long-text':
                 return (
                     <textarea
                         value={value}
                         onChange={(e) => handleInputChange(qId, e.target.value)}
                         className="responder-input"
                         placeholder="Tu respuesta"
                         rows="4"
                         required={question.required}
                     />
                 );
             case 'multiple-choice':
                 return (
                     <div className="responder-options">
                         {question.options.map((opt, idx) => (
                             <label key={idx} className="responder-option">
                                 <input
                                     type="radio"
                                     name={`q - ${ qId } `}
                                     value={opt}
                                     checked={value === opt}
                                     onChange={(e) => handleInputChange(qId, e.target.value)}
                                     required={question.required}
                                 />
                                 <span>{opt}</span>
                             </label>
                         ))}
                     </div>
                 );
             case 'checkbox':
                 return (
                     <div className="responder-options">
                         {question.options.map((opt, idx) => (
                             <label key={idx} className="responder-option">
                                 <input
                                     type="checkbox"
                                     checked={Array.isArray(value) && value.includes(opt)}
                                     onChange={(e) => handleCheckboxChange(qId, opt, e.target.checked)}
                                 />
                                 <span>{opt}</span>
                             </label>
                         ))}
                     </div>
                 );
             case 'dropdown':
                 return (
                     <select
                         value={value}
                         onChange={(e) => handleInputChange(qId, e.target.value)}
                         className="responder-input"
                         required={question.required}
                     >
                         <option value="">Selecciona una opción</option>
                         {question.options.map((opt, idx) => (
                             <option key={idx} value={opt}>{opt}</option>
                         ))}
                     </select>
                 );
             case 'rating':
                 return (
                     <div className="responder-rating">
                         {[1, 2, 3, 4, 5].map(star => (
                             <button
                                 key={star}
                                 type="button"
                                 className={`star - btn ${ value >= star ? 'active' : '' } `}
                                 onClick={() => handleInputChange(qId, star)}
                             >
                                 ⭐
                             </button>
                         ))}
                     </div>
                 );
             case 'date':
                 return (
                     <input
                         type="date"
                         value={value}
                         onChange={(e) => handleInputChange(qId, e.target.value)}
                         className="responder-input"
                         required={question.required}
                     />
                 );
             default:
                 return null;
         }
     };*/
    const renderQuestionInput = (question) => {
        const qId = question.id;
        const value = respuestas[qId] || '';

        switch (question.type) {
            // --- NUEVO CASO AÑADIDO: SELECTOR DE ESPALDA ---
            case 'muscle-map': // Asegúrate que en tu JSON el tipo se llame así
                return (
                    <div className="muscle-map-container" style={{ marginTop: '10px' }}>
                        <SelectorEspalda
                            valorInicial={value}
                            alSeleccionar={(zona) => handleInputChange(qId, zona)}
                        />
                        {/* Pequeño texto de confirmación debajo del mapa */}
                        <div style={{ marginTop: '5px', fontSize: '0.9em', color: '#555' }}>
                            Zona seleccionada: <strong>{value ? value.toUpperCase() : "Ninguna"}</strong>
                        </div>
                    </div>
                );
            // ------------------------------------------------

            case 'short-text':
                return (
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => handleInputChange(qId, e.target.value)}
                        className="responder-input"
                        placeholder="Tu respuesta"
                        required={question.required}
                    />
                );
            case 'long-text':
                return (
                    <textarea
                        value={value}
                        onChange={(e) => handleInputChange(qId, e.target.value)}
                        className="responder-input"
                        placeholder="Tu respuesta"
                        rows="4"
                        required={question.required}
                    />
                );
            case 'multiple-choice':
                return (
                    <div className="responder-options">
                        {question.options.map((opt, idx) => (
                            <label key={idx} className="responder-option">
                                <input
                                    type="radio"
                                    name={`q - ${qId} `}
                                    value={opt}
                                    checked={value === opt}
                                    onChange={(e) => handleInputChange(qId, e.target.value)}
                                    required={question.required}
                                />
                                <span>{opt}</span>
                            </label>
                        ))}
                    </div>
                );
            case 'checkbox':
                return (
                    <div className="responder-options">
                        {question.options.map((opt, idx) => (
                            <label key={idx} className="responder-option">
                                <input
                                    type="checkbox"
                                    checked={Array.isArray(value) && value.includes(opt)}
                                    onChange={(e) => handleCheckboxChange(qId, opt, e.target.checked)}
                                />
                                <span>{opt}</span>
                            </label>
                        ))}
                    </div>
                );
            case 'dropdown':
                return (
                    <select
                        value={value}
                        onChange={(e) => handleInputChange(qId, e.target.value)}
                        className="responder-input"
                        required={question.required}
                    >
                        <option value="" disabled>Selecciona una opción</option>
                        {question.options.map((opt, idx) => (
                            <option key={idx} value={opt}>{opt}</option>
                        ))}
                    </select>
                );
            case 'rating':
                return (
                    <div className="responder-rating">
                        {[1, 2, 3, 4, 5].map(star => (
                            <button
                                key={star}
                                type="button"
                                className={`star - btn ${value >= star ? 'active' : ''} `}
                                onClick={() => handleInputChange(qId, star)}
                            >
                                ⭐
                            </button>
                        ))}
                    </div>
                );
            case 'date':
                return (
                    <input
                        type="date"
                        value={value}
                        onChange={(e) => handleInputChange(qId, e.target.value)}
                        className="responder-input"
                        required={question.required}
                    />
                );
            case 'hand-map':
                return (
                    <div className="muscle-map-container" style={{ marginTop: '10px' }}>
                        <SelectorMano
                            valorInicial={value}
                            alSeleccionar={(zona) => handleInputChange(qId, zona)}
                        />
                        <div style={{ marginTop: '5px', fontSize: '0.9em', color: 'var(--text-secondary)' }}>
                            Zona seleccionada: <strong>{value ? (handZoneMap[value] || value.toUpperCase()) : "Ninguna"}</strong>
                        </div>
                    </div>
                );
            default:

                return null;
        }
    };

    const isQuestionVisible = (question) => {
        if (!question.dependsOn || !question.dependsValue) return true;

        const parentValue = respuestas[question.dependsOn];
        if (!parentValue) return false;

        if (Array.isArray(parentValue)) {
            return parentValue.includes(question.dependsValue);
        }
        // Handle dropdowns and radio buttons
        return parentValue.toString() === question.dependsValue.toString();
    };

    const visibleQuestions = questions.filter(isQuestionVisible);

    return (
        <div className={`responder-wrapper theme-${theme}`}>

            <div className="responder-container">
                <div className="responder-card">
                    <h1 className="responder-title">{formTitle}</h1>
                    {formDescription && <p className="responder-description">{formDescription}</p>}

                    {visibleQuestions.length === 0 ? (
                        <p className="responder-empty">Cargando formulario o no hay preguntas visibles...</p>
                    ) : (
                        <form onSubmit={handleSubmit} className="responder-form">
                            {visibleQuestions.map((question, index) => (
                                <div key={question.id} className="responder-question">
                                    <label className="responder-question-label">
                                        <span className="responder-q-number">{index + 1}.</span>
                                        <span className="responder-q-text">{question.text || `Pregunta`}</span>
                                        {question.required && <span className="responder-required">*</span>}
                                    </label>
                                    <div className="responder-input-wrapper">
                                        {question.image && (
                                            <div className="responder-question-image" style={{ marginBottom: '15px', textAlign: 'center' }}>
                                                <img src={question.image} alt="Pregunta" style={{ maxWidth: '100%', maxHeight: '450px', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                                            </div>
                                        )}
                                        {renderQuestionInput(question)}
                                    </div>
                                </div>
                            ))}

                            <button type="submit" className="responder-submit-btn" disabled={isSubmitting}>
                                {isSubmitting ? "Enviando..." : "Enviar Respuestas"}
                            </button>

                            {submitMessage && (
                                <div className={`responder-message ${submitMessage.includes('✓') ? 'success' : 'error'}`}>
                                    {submitMessage}
                                </div>
                            )}
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}


export default FormResponder;
