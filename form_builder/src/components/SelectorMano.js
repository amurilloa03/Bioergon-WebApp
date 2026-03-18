import React, { useState } from 'react';

const SelectorMano = ({ alSeleccionar, valorInicial }) => {
    const [zonaActiva, setZonaActiva] = useState(valorInicial || null);

    const manejarClick = (id) => {
        setZonaActiva(id);
        if (alSeleccionar) {
            alSeleccionar(id);
        }
    };

    const zonas = [
        { id: 'pulgar', label: 'Zona A' },
        { id: 'indice', label: 'Zona B' },
        { id: 'corazon', label: 'Zona C' },
        { id: 'anular', label: 'Zona D' },
        { id: 'menique', label: 'Zona E' },
        { id: 'palma', label: 'Zona F' }
    ];

    const styles = {
        contenedor: { display: 'flex', height: '500px', border: '1px solid #ccc', borderRadius: '8px', overflow: 'hidden', background: '#f4f4f4', fontFamily: 'sans-serif' },
        panel: { width: '250px', background: 'linear-gradient(180deg, #3498db, #2c3e50)', color: 'white', display: 'flex', flexDirection: 'column', padding: '1rem', overflowY: 'auto' },
        boton: (activo) => ({ padding: '8px', marginBottom: '5px', background: activo ? 'white' : 'rgba(255,255,255,0.2)', color: activo ? '#2980b9' : 'white', fontWeight: activo ? 'bold' : 'normal', cursor: 'pointer', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }),
        areaVisual: { flexGrow: 1, position: 'relative', overflow: 'hidden', background: 'white', display: 'flex', justifyContent: 'center' },
        lienzo: { position: 'relative', width: '600px', height: '600px', transformOrigin: 'top center', transform: 'scale(1.0)' },
        imgBase: { width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 },
        imgOverlay: (visible) => ({ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, opacity: visible ? 1 : 0, transition: 'opacity 0.3s', pointerEvents: 'none' }),
        svg: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 10 },
        zonaClick: { fill: 'transparent', cursor: 'pointer' }
    };

    const rutaImg = (nombre) => `/static/images/mapa-mano/${nombre}`;

    return (
        <div style={styles.contenedor}>
            <div style={styles.panel}>
                <h3>Dolor en la Mano</h3>
                <div>
                    {zonas.map((z) => (
                        <div key={z.id} style={styles.boton(zonaActiva === z.id)} onClick={() => manejarClick(z.id)}>
                            <span>{z.label}</span>
                            {zonaActiva === z.id && <span>✓</span>}
                        </div>
                    ))}
                </div>
            </div>

            <div style={styles.areaVisual}>
                <div style={styles.lienzo}>
                    <img style={styles.imgBase} src={rutaImg('mano.png')} alt="Mano Base" />

                    <img style={styles.imgOverlay(zonaActiva === 'pulgar')} src={rutaImg('mano_a.png')} alt="Zona A" />
                    <img style={styles.imgOverlay(zonaActiva === 'indice')} src={rutaImg('mano_b.png')} alt="Zona B" />
                    <img style={styles.imgOverlay(zonaActiva === 'corazon')} src={rutaImg('mano_c.png')} alt="Zona C" />
                    <img style={styles.imgOverlay(zonaActiva === 'anular')} src={rutaImg('mano_d.png')} alt="Zona D" />
                    <img style={styles.imgOverlay(zonaActiva === 'menique')} src={rutaImg('mano_e.png')} alt="Zona E" />
                    <img style={styles.imgOverlay(zonaActiva === 'palma')} src={rutaImg('mano_f.png')} alt="Zona F" />

                    <svg style={styles.svg} viewBox="0 0 600 600">
                        {/* Coordenadas aproximadas para los dedos y palma */}
                        <path style={styles.zonaClick} onClick={() => manejarClick('pulgar')} d="M120,380 Q100,280 180,240 L210,310 Z" />
                        <path style={styles.zonaClick} onClick={() => manejarClick('indice')} d="M220,220 Q230,50 280,60 L310,210 Z" />
                        <path style={styles.zonaClick} onClick={() => manejarClick('corazon')} d="M310,210 Q340,30 395,40 L400,200 Z" />
                        <path style={styles.zonaClick} onClick={() => manejarClick('anular')} d="M400,200 Q450,55 510,95 L470,220 Z" />
                        <path style={styles.zonaClick} onClick={() => manejarClick('menique')} d="M470,220 Q560,180 580,280 L490,300 Z" />
                        <path style={styles.zonaClick} onClick={() => manejarClick('palma')} d="M220,240 L470,220 L490,500 L210,500 Z" />
                    </svg>
                </div>
            </div>
        </div>
    );
};

export default SelectorMano;
