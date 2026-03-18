import React, { useState, useEffect, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler
} from 'chart.js';
import { Bar, Doughnut, Radar } from 'react-chartjs-2';


ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler
);

const StatsDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    d_from: '',
    d_to: ''
  });

  const urlParams = new URLSearchParams(window.location.search);
  const formId = urlParams.get('form_id');

  const fetchStats = useCallback(() => {
    if (!formId) {
      setError("No se proporcionó ID de formulario");
      setLoading(false);
      return;
    }

    setLoading(true);
    let url = `/api/formularios/${formId}/stats`;
    const params = new URLSearchParams();
    if (filters.d_from) params.append('d_from', filters.d_from);
    if (filters.d_to) params.append('d_to', filters.d_to);

    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error("Error cargando estadísticas");
        return res.json();
      })
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [formId, filters]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  if (error) return <div className="stats-message error">Error: {error}</div>;

  const renderTextResponses = (question) => {
    if (!question.responses || question.responses.length === 0) {
      return <p className="no-data">No hay respuestas de texto aún.</p>;
    }

    return (
      <div className="text-responses-list">
        {question.responses.map((resp, i) => (
          <div key={i} className="text-resp-item">
            <span className="bullet">•</span> {resp}
          </div>
        ))}
      </div>
    );
  };

  const renderChart = (question, index) => {
    const isChoice = ['multiple-choice', 'dropdown', 'checkboxes', 'checkbox', 'muscle-map', 'hand-map'].includes(question.type);
    const isRating = question.type === 'rating';
    const isText = ['short-text', 'long-text', 'email', 'number', 'phone', 'date'].includes(question.type);

    const colorPalettes = [
      // Palette 0: Saturated / Vibrant (Bright colors)
      [
        'rgba(59, 130, 246, 0.85)', 'rgba(239, 68, 68, 0.85)', 'rgba(16, 185, 129, 0.85)',
        'rgba(245, 158, 11, 0.85)', 'rgba(139, 92, 246, 0.85)', 'rgba(6, 182, 212, 0.85)',
        'rgba(236, 72, 153, 0.85)', 'rgba(132, 204, 22, 0.85)', 'rgba(249, 115, 22, 0.85)'
      ],
      // Palette 1: Pastel (Soft, bright but desaturated colors)
      [
        'rgba(196, 181, 253, 0.85)', 'rgba(167, 243, 208, 0.85)', 'rgba(253, 230, 138, 0.85)',
        'rgba(191, 219, 254, 0.85)', 'rgba(254, 205, 211, 0.85)', 'rgba(165, 243, 252, 0.85)',
        'rgba(233, 213, 255, 0.85)', 'rgba(254, 215, 170, 0.85)', 'rgba(252, 231, 243, 0.85)'
      ],
      // Palette 2: Monochromatic Blues
      [
        'rgba(30, 58, 138, 0.85)', 'rgba(37, 99, 235, 0.85)', 'rgba(96, 165, 250, 0.85)',
        'rgba(147, 197, 253, 0.85)', 'rgba(191, 219, 254, 0.85)', 'rgba(29, 78, 216, 0.85)',
        'rgba(59, 130, 246, 0.85)', 'rgba(219, 234, 254, 0.85)', 'rgba(239, 246, 255, 0.85)'
      ],
      // Palette 3: Earth Tones & Warm
      [
        'rgba(180, 83, 9, 0.85)', 'rgba(202, 138, 4, 0.85)', 'rgba(217, 119, 6, 0.85)',
        'rgba(154, 52, 18, 0.85)', 'rgba(113, 63, 18, 0.85)', 'rgba(161, 98, 7, 0.85)',
        'rgba(63, 98, 18, 0.85)', 'rgba(20, 83, 45, 0.85)', 'rgba(234, 179, 8, 0.85)'
      ],
      // Palette 4: Soft Greens & Teals
      [
        'rgba(13, 148, 136, 0.85)', 'rgba(45, 212, 191, 0.85)', 'rgba(52, 211, 153, 0.85)',
        'rgba(16, 185, 129, 0.85)', 'rgba(94, 234, 212, 0.85)', 'rgba(20, 184, 166, 0.85)',
        'rgba(5, 150, 105, 0.85)', 'rgba(4, 120, 87, 0.85)', 'rgba(6, 95, 70, 0.85)'
      ]
    ];
    
    const paletteIndex = index !== undefined ? index : 0;
    const currentPalette = colorPalettes[paletteIndex % colorPalettes.length];

    if (isChoice) {
      const labels = Object.keys(question.data);
      const values = Object.values(question.data);
      const isHorizontalBar = ['checkboxes', 'checkbox', 'muscle-map', 'hand-map'].includes(question.type);

      const data = {
        labels,
        datasets: [{
          label: 'Respuestas',
          data: values,
          backgroundColor: currentPalette,
          borderColor: isHorizontalBar ? 'rgba(0,0,0,0)' : '#ffffff',
          borderWidth: isHorizontalBar ? 0 : 2,
          hoverOffset: isHorizontalBar ? 0 : 5
        }]
      };

      return (
        <div className="chart-wrapper">
          <div className="chart-header">
            <h4>{question.title}</h4>
            <span className="badge">{question.total_answered} respuestas</span>
          </div>
          <div className="chart-container">
            {isHorizontalBar ?
              <Bar data={data} options={{
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                maintainAspectRatio: false,
                scales: { 
                    x: { grid: { color: 'rgba(0,0,0,0.05)' }, border: { dash: [4, 4] } }, 
                    y: { grid: { display: false } } 
                }
              }} /> :
              <Doughnut data={data} options={{ 
                  maintainAspectRatio: false, 
                  cutout: '65%',
                  plugins: { legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 8, padding: 20 } } } 
              }} />
            }
          </div>
        </div>
      );
    }

    if (isRating) {
      const labels = ['1 ⭐', '2 ⭐', '3 ⭐', '4 ⭐', '5 ⭐'];
      const values = [1, 2, 3, 4, 5].map(star => question.distribution[star] || 0);

      const data = {
        labels,
        datasets: [{
          label: 'Frecuencia de Votos',
          data: values,
          backgroundColor: 'rgba(245, 158, 11, 0.4)', // Amber transparent
          borderColor: 'rgba(245, 158, 11, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(245, 158, 11, 1)',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: 'rgba(245, 158, 11, 1)',
          fill: true
        }]
      };

      return (
        <div className="chart-wrapper">
          <div className="chart-header">
            <h4>{question.title}</h4>
            <div className="header-meta">
              <span className="average-badge">{question.average} ★ Media</span>
            </div>
          </div>
          <div className="chart-container" style={{ padding: '10px' }}>
            <Radar data={data} options={{
              maintainAspectRatio: false,
              scales: {
                r: {
                    angleLines: { color: 'rgba(0,0,0,0.1)' },
                    grid: { color: 'rgba(0,0,0,0.1)' },
                    pointLabels: { font: { size: 12, weight: 'bold' }, color: '#64748b' },
                    ticks: { display: false, stepSize: 1 }
                }
              },
              plugins: { legend: { display: false }, tooltip: { callbacks: { label: function(context) { return context.raw + ' votos'; } } } }
            }} />
          </div>
        </div>
      );
    }

    if (isText) {
      return (
        <div className="chart-wrapper text-wrapper">
          <div className="chart-header">
            <h4>{question.title}</h4>
            <span className="badge">{question.total_answered} respuestas</span>
          </div>
          {renderTextResponses(question)}
        </div>
      );
    }

    return null;
  };

  return (
    <div className="stats-dashboard">
      <header className="stats-header">
        <div className="header-left">
          <button className="btn-back" onClick={() => window.location.href = '/formularios'}>
            ← Volver
          </button>
          <div className="title-wrapper">
            <h2>Análisis de Resultados</h2>
            <p className="subtitle">Usa los filtros para segmentar la información</p>
          </div>
        </div>

        {stats && (
          <div className="summary-pill">
            <div className="summary-val">{stats.total_responses}</div>
            <div className="summary-lab">Resultados</div>
          </div>
        )}
      </header>

      <section className="filter-bar">
        <div className="filter-group">
          <label>Desde</label>
          <input type="date" name="d_from" value={filters.d_from} onChange={handleFilterChange} />
        </div>
        <div className="filter-group">
          <label>Hasta</label>
          <input type="date" name="d_to" value={filters.d_to} onChange={handleFilterChange} />
        </div>
        <button className="btn-refresh" onClick={fetchStats} disabled={loading}>
          {loading ? '...' : 'Actualizar'}
        </button>
      </section>

      {loading ? (
        <div className="stats-loader">
          <div className="spinner"></div>
          <p>Extrayendo conocimientos...</p>
        </div>
      ) : (
        <div className="charts-grid">
          {stats.questions.map((q, index) => (
            <div key={q.id} className="chart-card">
              {renderChart(q, index) || (
                <div className="chart-placeholder">
                  <div className="chart-header">
                    <h4>{q.title}</h4>
                  </div>
                  <div className="placeholder-content">
                    <p>Métricas no disponibles para "{q.type}"</p>
                    <span className="badge">{q.total_answered} respuestas</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <style>{`
        :root {
          --stats-bg: #f8fafc;
          --stats-card: rgba(255, 255, 255, 0.8);
          --stats-border: rgba(226, 232, 240, 0.8);
          --stats-primary: #6366f1;
          --stats-accent: #10b981;
          --stats-text: #0f172a;
          --stats-muted: #64748b;
        }

        .stats-dashboard {
          padding: 40px 24px;
          max-width: 1300px;
          margin: 0 auto;
          color: var(--stats-text);
          font-family: 'Inter', system-ui, sans-serif;
          min-height: 100vh;
        }

        .stats-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 32px;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .stats-header h2 {
          font-size: 32px;
          font-weight: 800;
          margin: 0;
          color: var(--stats-text);
          letter-spacing: -0.025em;
        }

        .title-wrapper {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .subtitle {
          margin: 0;
          font-size: 14px;
          color: var(--stats-muted);
          font-weight: 500;
        }

        .btn-back {
          background: white;
          border: 1px solid var(--stats-border);
          padding: 10px 18px;
          border-radius: 12px;
          color: var(--stats-text);
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
          box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .btn-back:hover {
          background: rgba(255,255,255,0.1);
          transform: translateX(-4px);
        }

        .summary-pill {
          display: flex;
          align-items: center;
          background: linear-gradient(135deg, var(--stats-primary), #6d28d9);
          padding: 8px 16px;
          border-radius: 99px;
          box-shadow: 0 10px 20px -5px rgba(139, 92, 246, 0.3);
          gap: 12px;
        }

        .summary-val {
          font-size: 24px;
          font-weight: 800;
        }

        .summary-lab {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-weight: 700;
          opacity: 0.8;
        }

        .filter-bar {
          display: flex;
          gap: 20px;
          background: var(--stats-card);
          backdrop-filter: blur(12px);
          padding: 24px 32px;
          border-radius: 20px;
          border: 1px solid var(--stats-border);
          margin-bottom: 40px;
          align-items: flex-end;
          box-shadow: var(--shadow-md);
        }

        .filter-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .filter-group label {
          font-size: 12px;
          font-weight: 700;
          color: var(--stats-muted);
          text-transform: uppercase;
        }

        .filter-group input {
          background: white;
          border: 1px solid var(--stats-border);
          border-radius: 10px;
          padding: 10px 14px;
          color: var(--stats-text);
          font-family: inherit;
          font-size: 14px;
        }

        .btn-refresh {
          background: var(--stats-primary);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 10px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
        }

        .btn-refresh:hover:not(:disabled) {
          background: var(--primary-hover);
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3);
        }

        .btn-refresh:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
          gap: 24px;
        }

        .chart-card {
          background: var(--stats-card);
          backdrop-filter: blur(12px);
          border: 1px solid var(--stats-border);
          border-radius: 24px;
          padding: 24px;
          transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .chart-card:hover {
          transform: scale(1.02);
          border-color: rgba(255,255,255,0.2);
        }

        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 24px;
          gap: 16px;
        }

        .chart-header h4 {
          margin: 0;
          font-size: 18px;
          font-weight: 700;
          color: white;
          line-height: 1.4;
        }

        .badge {
          background: rgba(0,0,0,0.05);
          padding: 4px 10px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          color: var(--stats-muted);
          white-space: nowrap;
        }

        .average-badge {
          background: rgba(255, 206, 86, 0.15);
          color: #fbbf24;
          padding: 4px 10px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 700;
        }

        .header-meta {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 6px;
        }

        .chart-container {
          min-height: 280px;
          width: 100%;
          position: relative;
        }

        .text-responses-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          max-height: 300px;
          overflow-y: auto;
          padding-right: 8px;
        }

        .text-responses-list::-webkit-scrollbar { width: 6px; }
        .text-responses-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

        .text-resp-item {
          background: rgba(15, 23, 42, 0.4);
          padding: 14px;
          border-radius: 12px;
          font-size: 14px;
          line-height: 1.5;
          color: #e2e8f0;
          border-left: 3px solid var(--stats-primary);
        }

        .bullet {
          color: var(--stats-primary);
          font-weight: 900;
          margin-right: 6px;
        }

        .no-data {
          color: var(--stats-muted);
          text-align: center;
          font-style: italic;
          padding: 40px 0;
        }

        .stats-loader {
          text-align: center;
          padding: 120px 0;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(255,255,255,0.05);
          border-top: 4px solid var(--stats-primary);
          border-radius: 50%;
          margin: 0 auto 20px;
          animation: spin 1s linear infinite;
        }

        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        @media (max-width: 768px) {
          .stats-header { flex-direction: column; align-items: flex-start; gap: 20px; }
          .filter-bar { flex-direction: column; align-items: stretch; }
          .charts-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
};

export default StatsDashboard;
