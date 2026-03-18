import React from "react";
import "../styles/QuestionCard.css";

function QuestionCard({
    question,
    isSelected,
    index,
    totalQuestions,
    onSelect,
    onDelete,
    onDuplicate,
    onMoveUp,
    onMoveDown,
}) {
    const getTypeLabel = (type) => {
        const labels = {
            "short-text": "Respuesta Corta",
            "long-text": "Respuesta Larga",
            "multiple-choice": "Opción Múltiple",
            checkbox: "Casillas (Multi)",
            dropdown: "Desplegable",
            rating: "Calificación",
            date: "Fecha",
        };
        return labels[type] || type;
    };

    const getTypeEmoji = (type) => {
        const emojis = {
            "short-text": "📝",
            "long-text": "📄",
            "multiple-choice": "◉",
            checkbox: "☑",
            dropdown: "▼",
            rating: "⭐",
            date: "📅",
        };
        return emojis[type] || "❓";
    };

    return (
        <div
            className={`question-card ${isSelected ? "selected" : ""}`}
            onClick={onSelect}
        >
            <div className="question-card-header">
                <div className="question-number-type">
                    <span className="question-number">{index + 1}</span>
                    <span className="question-type">
                        {getTypeEmoji(question.type)} {getTypeLabel(question.type)}
                    </span>
                    {question.required && <span className="required-badge">*</span>}
                </div>
                <div className="question-actions">
                    <button
                        className="action-btn"
                        onClick={(e) => {
                            e.stopPropagation();
                            onMoveUp();
                        }}
                        disabled={index === 0}
                        title="Mover arriba"
                    >
                        ↑
                    </button>
                    <button
                        className="action-btn"
                        onClick={(e) => {
                            e.stopPropagation();
                            onMoveDown();
                        }}
                        disabled={index === totalQuestions - 1}
                        title="Mover abajo"
                    >
                        ↓
                    </button>
                    <button
                        className="action-btn duplicate"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDuplicate();
                        }}
                        title="Duplicar"
                    >
                        📋
                    </button>
                    <button
                        className="action-btn delete"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                        title="Eliminar"
                    >
                        🗑
                    </button>
                </div>
            </div>
            <div className="question-card-content">
                <p className="question-text">{question.question || "Sin pregunta aún"}</p>
                {question.options && question.options.length > 0 && (
                    <div className="question-preview-options">
                        {question.options.slice(0, 3).map((opt, i) => (
                            <span key={i} className="option-badge">
                                {opt}
                            </span>
                        ))}
                        {question.options.length > 3 && (
                            <span className="option-badge">+{question.options.length - 3}</span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default QuestionCard;
