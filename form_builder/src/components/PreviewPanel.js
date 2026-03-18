import React, { useState } from "react";
import "../styles/PreviewPanel.css";

function PreviewPanel({ formData }) {
    const [answers, setAnswers] = useState({});

    const renderQuestion = (question, index) => {
        const handleChange = (value) => {
            setAnswers({
                ...answers,
                [question.id]: value,
            });
        };

        const handleOptionChange = (option) => {
            const currentAnswers = answers[question.id] || [];
            if (currentAnswers.includes(option)) {
                setAnswers({
                    ...answers,
                    [question.id]: currentAnswers.filter((a) => a !== option),
                });
            } else {
                setAnswers({
                    ...answers,
                    [question.id]: [...currentAnswers, option],
                });
            }
        };

        return (
            <div key={question.id} className="preview-question">
                <label className="question-label">
                    {index + 1}. {question.question}
                    {question.required && <span className="required">*</span>}
                </label>

                {question.type === "short-text" && (
                    <input
                        type="text"
                        placeholder="Respuesta corta"
                        value={answers[question.id] || ""}
                        onChange={(e) => handleChange(e.target.value)}
                        className="preview-input"
                    />
                )}

                {question.type === "long-text" && (
                    <textarea
                        placeholder="Respuesta larga"
                        value={answers[question.id] || ""}
                        onChange={(e) => handleChange(e.target.value)}
                        rows="4"
                        className="preview-textarea"
                    />
                )}

                {question.type === "multiple-choice" && (
                    <div className="preview-options">
                        {question.options.map((option, i) => (
                            <label key={i} className="radio-label">
                                <input
                                    type="radio"
                                    name={`question-${question.id}`}
                                    value={option}
                                    checked={answers[question.id] === option}
                                    onChange={() => handleChange(option)}
                                />
                                {option}
                            </label>
                        ))}
                    </div>
                )}

                {question.type === "checkbox" && (
                    <div className="preview-options">
                        {question.options.map((option, i) => (
                            <label key={i} className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={(answers[question.id] || []).includes(option)}
                                    onChange={() => handleOptionChange(option)}
                                />
                                {option}
                            </label>
                        ))}
                    </div>
                )}

                {question.type === "dropdown" && (
                    <select
                        value={answers[question.id] || ""}
                        onChange={(e) => handleChange(e.target.value)}
                        className="preview-select"
                    >
                        <option value="">Selecciona una opción</option>
                        {question.options.map((option, i) => (
                            <option key={i} value={option}>
                                {option}
                            </option>
                        ))}
                    </select>
                )}

                {question.type === "rating" && (
                    <div className="preview-rating">
                        {[1, 2, 3, 4, 5].map((star) => (
                            <button
                                key={star}
                                className={`star ${answers[question.id] === star ? "selected" : ""
                                    }`}
                                onClick={() => handleChange(star)}
                            >
                                ★
                            </button>
                        ))}
                    </div>
                )}

                {question.type === "date" && (
                    <input
                        type="date"
                        value={answers[question.id] || ""}
                        onChange={(e) => handleChange(e.target.value)}
                        className="preview-input"
                    />
                )}
            </div>
        );
    };

    return (
        <div className="preview-panel">
            <div className="preview-form">
                <div className="preview-header">
                    <h2>{formData.formTitle}</h2>
                    {formData.formDescription && <p>{formData.formDescription}</p>}
                </div>

                <div className="preview-questions">
                    {formData.questions.length === 0 ? (
                        <p className="empty-preview">No hay preguntas para mostrar</p>
                    ) : (
                        formData.questions.map((question, index) =>
                            renderQuestion(question, index)
                        )
                    )}
                </div>

                <div className="preview-footer">
                    <button className="btn-submit">Enviar Respuestas</button>
                </div>
            </div>
        </div>
    );
}

export default PreviewPanel;
