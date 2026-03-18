import React from "react";
import "../styles/QuestionList.css";
import QuestionCard from "./QuestionCard";

function QuestionList({
    questions,
    selectedQuestionId,
    onSelectQuestion,
    onDeleteQuestion,
    onDuplicateQuestion,
    onMoveQuestion,
}) {
    return (
        <div className="question-list">
            {questions.map((question, index) => (
                <QuestionCard
                    key={question.id}
                    question={question}
                    isSelected={selectedQuestionId === question.id}
                    index={index}
                    totalQuestions={questions.length}
                    onSelect={() => onSelectQuestion(question.id)}
                    onDelete={() => onDeleteQuestion(question.id)}
                    onDuplicate={() => onDuplicateQuestion(question.id)}
                    onMoveUp={() => onMoveQuestion(question.id, "up")}
                    onMoveDown={() => onMoveQuestion(question.id, "down")}
                />
            ))}
        </div>
    );
}

export default QuestionList;
