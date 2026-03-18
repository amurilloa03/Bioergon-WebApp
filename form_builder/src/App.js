import React from "react";
import "./App.css";
import FormBuilder from "./components/FormBuilder";
import FormResponder from "./components/FormResponder";
import StatsDashboard from "./components/StatsDashboard";

function App() {
  // Detectar si estamos en modo responder o editar según la ruta
  const currentPath = window.location.pathname;
  const isResponder = currentPath.includes('/responder-formulario');
  const isStats = currentPath.includes('/estadisticas-formulario');

  return (
    <div className="app-container">
      {isResponder ? <FormResponder /> : (isStats ? <StatsDashboard /> : <FormBuilder />)}
    </div>
  );
}

export default App;
