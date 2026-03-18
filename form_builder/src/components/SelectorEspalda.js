import React, { useState } from 'react';
// Si prefieres el CSS en un archivo aparte, crea SelectorEspalda.css en la misma carpeta e impórtalo:
// import './SelectorEspalda.css'; 

const SelectorEspalda = ({ alSeleccionar, valorInicial }) => {
  const [zonaActiva, setZonaActiva] = useState(valorInicial || null);

  const manejarClick = (zona) => {
    setZonaActiva(zona);
    // Comunicar al componente padre (FormResponder.js) que se ha elegido algo
    if (alSeleccionar) {
      alSeleccionar(zona);
    }
  };

  const zonas = [
    { id: 'cuello', label: '🧣 Cuello' },
    { id: 'hombro', label: '💪 Hombros' },
    { id: 'columna', label: '🦴 Columna T.' },
    { id: 'lumbar', label: '🪵 Lumbar' },
    { id: 'cadera', label: '🍑 Cadera' },
    { id: 'muneca', label: '⌚ Muñeca' },
    { id: 'mano', label: '✋ Mano' },
    { id: 'pierna', label: '🦵 Pierna Post.' },
    { id: 'rodilla', label: '⚪ Rodilla' },
    { id: 'tobillo', label: '🦶 Tobillo' },
    { id: 'pie', label: '👟 Pie' },
  ];

  // ESTILOS EN LINEA (Para evitarte crear archivos CSS extra si no quieres)
  const styles = {
    contenedor: { display: 'flex', height: '500px', border: '1px solid #ccc', borderRadius: '8px', overflow: 'hidden', background: '#f4f4f4', fontFamily: 'sans-serif' },
    panel: { width: '250px', background: 'linear-gradient(180deg, #8e44ad, #c0392b)', color: 'white', display: 'flex', flexDirection: 'column', padding: '1rem', overflowY: 'auto' },
    boton: (activo) => ({ padding: '8px', marginBottom: '5px', background: activo ? 'white' : 'rgba(255,255,255,0.2)', color: activo ? '#c0392b' : 'white', fontWeight: activo ? 'bold' : 'normal', cursor: 'pointer', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }),
    areaVisual: { flexGrow: 1, position: 'relative', overflow: 'hidden', background: 'white', display: 'flex', justifyContent: 'center' },
    lienzo: { position: 'relative', width: '750px', height: '900px', transformOrigin: 'top center', transform: 'scale(0.55)' }, // Ajusta scale si se ve muy grande
    imgBase: { width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 },
    imgOverlay: (visible) => ({ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, opacity: visible ? 1 : 0, transition: 'opacity 0.3s', pointerEvents: 'none' }),
    svg: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 10 },
    zonaClick: { fill: 'transparent', cursor: 'pointer' }
  };

  // RUTA DE IMAGENES: Ahora apuntan a /static/images/mapa-cuerpo/
  const rutaImg = (nombre) => `/static/images/mapa-cuerpo/${nombre}`;

  return (
    <div style={styles.contenedor}>
      {/* PANEL LATERAL */}
      <div style={styles.panel}>
        <h3>Zona Afectada</h3>
        <div>
          {zonas.map((z) => (
            <div key={z.id} style={styles.boton(zonaActiva === z.id)} onClick={() => manejarClick(z.id)}>
              <span>{z.label}</span>
              {zonaActiva === z.id && <span>✓</span>}
            </div>
          ))}
        </div>
      </div>

      {/* ÁREA VISUAL */}
      <div style={styles.areaVisual}>
        <div style={styles.lienzo}>
          <img style={styles.imgBase} src={rutaImg('Gemini_Generated_Image_asrv58asrv58asrv.png')} alt="Base" />
          
          <img style={styles.imgOverlay(zonaActiva === 'cuello')} src={rutaImg('cuello.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'hombro')} src={rutaImg('hombros (2).jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'columna')} src={rutaImg('columna (2).jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'lumbar')} src={rutaImg('lumbar.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'cadera')} src={rutaImg('Gemini_Generated_Image_hacpxnhacpxnhacp.png')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'pierna')} src={rutaImg('piernas.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'rodilla')} src={rutaImg('rodillaatras.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'tobillo')} src={rutaImg('tobillo.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'pie')} src={rutaImg('pies.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'muneca')} src={rutaImg('muñecas.jpg')} alt="" />
          <img style={styles.imgOverlay(zonaActiva === 'mano')} src={rutaImg('manos.jpg')} alt="" />

          <svg style={styles.svg} viewBox="0 0 750 900">
             <rect style={styles.zonaClick} onClick={() => manejarClick('cuello')} x="338" y="114" width="75" height="48" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('hombro')} x="287" y="185" width="50" height="50" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('hombro')} x="417" y="185" width="50" height="50" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('columna')} x="345" y="162" width="60" height="180" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('lumbar')} x="320" y="315" width="105" height="72" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('cadera')} x="310" y="380" width="120" height="120" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('pierna')} x="300" y="480" width="90" height="132" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('pierna')} x="380" y="480" width="90" height="132" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('rodilla')} x="315" y="585" width="46" height="56" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('rodilla')} x="390" y="590" width="46" height="56" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('tobillo')} x="314" y="785" width="30" height="20" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('tobillo')} x="400" y="785" width="30" height="20" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('pie')} x="300" y="805" width="55" height="46" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('pie')} x="390" y="805" width="55" height="46" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('muneca')} x="240" y="400" width="40" height="36" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('muneca')} x="470" y="400" width="40" height="36" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('mano')} x="240" y="440" width="40" height="80" />
             <rect style={styles.zonaClick} onClick={() => manejarClick('mano')} x="470" y="440" width="40" height="80" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default SelectorEspalda;