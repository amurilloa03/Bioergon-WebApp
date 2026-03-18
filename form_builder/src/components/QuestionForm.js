import React from "react";
import "../styles/QuestionForm.css";

function QuestionForm({ question, onUpdate }) {
    const handleQuestionChange = (e) => {
        onUpdate(question.id, { question: e.target.value });
    };

    const handleRequiredChange = (e) => {
        onUpdate(question.id, { required: e.target.checked });
    };

    const handleOptionChange = (index, value) => {
        const newOptions = [...question.options];
        newOptions[index] = value;
        onUpdate(question.id, { options: newOptions });
    };

    const addOption = () => {
        const newOptions = [...question.options, `Opción ${question.options.length + 1}`];
        onUpdate(question.id, { options: newOptions });
    };

    const removeOption = (index) => {
        const newOptions = question.options.filter((_, i) => i !== index);
        onUpdate(question.id, { options: newOptions });
    };

    return (
        <div className="question-form">
            <h4>Editar Pregunta</h4>

            <div className="form-group">
                <label htmlFor="questionText">Texto de la Pregunta</label>
                <textarea
                    id="questionText"
                    value={question.question}
                    onChange={handleQuestionChange}
                    placeholder="Ingresa el texto de la pregunta"
                    rows="3"
                />
            </div>

            <div className="form-group checkbox">
                <label htmlFor="required">
                    <input
                        id="required"
                        type="checkbox"
                        checked={question.required}
                        onChange={handleRequiredChange}
                    />
                    Pregunta requerida
                </label>
            </div>

            {(question.type === "multiple-choice" ||
                question.type === "checkbox" ||
                question.type === "dropdown") && (
                    <div className="form-group">
                        <label>Opciones</label>
                        <div className="options-list">
                            {question.options.map((option, index) => (
                                <div key={index} className="option-item">
                                    <input
                                        type="text"
                                        value={option}
                                        onChange={(e) => handleOptionChange(index, e.target.value)}
                                        placeholder={`Opción ${index + 1}`}
                                    />
                                    <button
                                        className="btn-remove-option"
                                        onClick={() => removeOption(index)}
                                        disabled={question.options.length <= 1}
                                        title="Eliminar opción"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))}
                        </div>
                        <button className="btn-add-option" onClick={addOption}>
                            + Añadir Opción
                        </button>
                    </div>
                )}

            {question.type === "rating" && (
                <div className="form-group">
                    <p className="info-text">
                        ⭐ Las preguntas de calificación mostrarán una escala de 1 a 5
                    </p>
                </div>
            )}

            {question.type === "date" && (
                <div className="form-group">
                    <p className="info-text">📅 Los usuarios podrán seleccionar una fecha</p>
                </div>
            )}
        </div>
    );
}

export default QuestionForm;
