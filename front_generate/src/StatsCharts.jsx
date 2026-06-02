import React, { useEffect, useRef, useState } from 'react'
import Chart from 'chart.js/auto'

export default function StatsCharts({ stats }) {
  const [activeChartTab, setActiveChartTab] = useState('grid') // 'grid' | 'winrates' | 'providers' | 'history'

  const doughnutCanvasRef = useRef(null)
  const polarCanvasRef = useRef(null)
  const barCanvasRef = useRef(null)
  const lineCanvasRef = useRef(null)

  const singleDoughnutCanvasRef = useRef(null)
  const singlePolarCanvasRef = useRef(null)
  const singleBarCanvasRef = useRef(null)
  const singleLineCanvasRef = useRef(null)

  // Chart instances trackers
  const chartInstances = useRef({
    doughnut: null,
    polar: null,
    bar: null,
    line: null,
    single: null
  })

  // Calculate stats values
  const textTotal = (stats.text_votes?.gemini || 0) + (stats.text_votes?.['gpt-4o'] || 0)
  const visionTotal = (stats.vision_votes?.gemini || 0) + (stats.vision_votes?.['gpt-4o'] || 0)
  const imageTotal = (stats.image_votes?.google || 0) + (stats.image_votes?.stability || 0)
  const videoTotal = (stats.video_votes?.a2e || 0) + (stats.video_votes?.stability || 0)
  const totalVotesCount = textTotal + visionTotal + imageTotal + videoTotal

  // Win rates calculation
  const getWinRate = (votes, total) => (total > 0 ? Math.round((votes / total) * 100) : 0)

  const modelsData = [
    { name: 'Gemini 2.5 (Texto)', rate: getWinRate(stats.text_votes?.gemini || 0, textTotal), color: '#38bdf8' },
    { name: 'GPT-4o (Texto)', rate: getWinRate(stats.text_votes?.['gpt-4o'] || 0, textTotal), color: '#10b981' },
    { name: 'Gemini 2.5 (Visión)', rate: getWinRate(stats.vision_votes?.gemini || 0, visionTotal), color: '#0ea5e9' },
    { name: 'GPT-4o (Visión)', rate: getWinRate(stats.vision_votes?.['gpt-4o'] || 0, visionTotal), color: '#60a5fa' },
    { name: 'Imagen 3 (Imagen)', rate: getWinRate(stats.image_votes?.google || 0, imageTotal), color: '#fbbf24' },
    { name: 'Flux (Imagen)', rate: getWinRate(stats.image_votes?.stability || 0, imageTotal), color: '#8b5cf6' },
    { name: 'A2E Kling (Video)', rate: getWinRate(stats.video_votes?.a2e || 0, videoTotal), color: '#f97316' },
    { name: 'SVD Video (Video)', rate: getWinRate(stats.video_votes?.stability || 0, videoTotal), color: '#ec4899' }
  ]

  // Provider share calculation
  const providerVotes = {
    Google: (stats.text_votes?.gemini || 0) + (stats.vision_votes?.gemini || 0) + (stats.image_votes?.google || 0),
    OpenAI: (stats.text_votes?.['gpt-4o'] || 0) + (stats.vision_votes?.['gpt-4o'] || 0),
    StabilityAI: (stats.image_votes?.stability || 0) + (stats.video_votes?.stability || 0),
    A2E: stats.video_votes?.a2e || 0
  }

  // Common Options
  const getCommonOptions = (titleText) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#e4e4e7',
          font: { family: 'Plus Jakarta Sans', size: 11, weight: '500' },
          padding: 15,
          usePointStyle: true
        }
      },
      title: {
        display: true,
        text: titleText,
        color: '#ffffff',
        font: { family: 'Outfit', size: 14, weight: '700' },
        padding: { bottom: 15 }
      },
      tooltip: {
        backgroundColor: '#18181b',
        titleFont: { family: 'Outfit', size: 12, weight: '700' },
        bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
        borderColor: '#27272a',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        displayColors: true
      }
    }
  })

  // Destroy all charts utility
  const destroyCharts = () => {
    Object.keys(chartInstances.current).forEach((key) => {
      if (chartInstances.current[key]) {
        chartInstances.current[key].destroy()
        chartInstances.current[key] = null
      }
    })
  }

  // Create Doughnut Chart (Provider share)
  const initDoughnutChart = (canvas) => {
    if (!canvas) return null
    const ctx = canvas.getContext('2d')
    
    // Create subtle gradients
    const gGoogle = ctx.createLinearGradient(0, 0, 0, 400)
    gGoogle.addColorStop(0, '#0284c7')
    gGoogle.addColorStop(1, '#38bdf8')

    const gStability = ctx.createLinearGradient(0, 0, 0, 400)
    gStability.addColorStop(0, '#7c3aed')
    gStability.addColorStop(1, '#a855f7')

    const gMeta = ctx.createLinearGradient(0, 0, 0, 400)
    gMeta.addColorStop(0, '#059669')
    gMeta.addColorStop(1, '#34d399')

    const gA2E = ctx.createLinearGradient(0, 0, 0, 400)
    gA2E.addColorStop(0, '#ea580c')
    gA2E.addColorStop(1, '#fb923c')

    return new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Google AI', 'Stability AI', 'OpenAI', 'A2E AI'],
        datasets: [{
          data: [providerVotes.Google, providerVotes.StabilityAI, providerVotes.OpenAI, providerVotes.A2E],
          backgroundColor: [gGoogle, gStability, gMeta, gA2E],
          borderColor: '#121214',
          borderWidth: 2,
          hoverOffset: 12
        }]
      },
      options: {
        ...getCommonOptions('Distribución por Proveedor (Votos Totales)'),
        cutout: '65%'
      }
    })
  }

  // Create Polar Area Chart (Arena Volume)
  const initPolarChart = (canvas) => {
    if (!canvas) return null
    const ctx = canvas.getContext('2d')
    return new Chart(ctx, {
      type: 'polarArea',
      data: {
        labels: ['Texto', 'Visión Multimodal', 'Imagen', 'Video'],
        datasets: [{
          data: [textTotal, visionTotal, imageTotal, videoTotal],
          backgroundColor: [
            'rgba(56, 189, 248, 0.4)',
            'rgba(96, 165, 250, 0.4)',
            'rgba(251, 191, 36, 0.4)',
            'rgba(236, 72, 153, 0.4)'
          ],
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }]
      },
      options: {
        ...getCommonOptions('Actividad por Arena (Votos Acumulados)'),
        scales: {
          r: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            angleLines: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              backdropColor: 'transparent',
              color: '#a1a1aa',
              font: { size: 9 }
            }
          }
        }
      }
    })
  }

  // Create Bar Chart (Win Rates)
  const initBarChart = (canvas) => {
    if (!canvas) return null
    const ctx = canvas.getContext('2d')
    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: modelsData.map(m => m.name),
        datasets: [{
          label: 'Porcentaje de Preferencia (%)',
          data: modelsData.map(m => m.rate),
          backgroundColor: modelsData.map(m => m.color),
          borderRadius: 6,
          borderWidth: 0,
          barPercentage: 0.6
        }]
      },
      options: {
        ...getCommonOptions('Tasa de Victoria de Cada Modelo'),
        indexAxis: 'y',
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#a1a1aa', font: { family: 'Plus Jakarta Sans' } },
            max: 100
          },
          y: {
            grid: { display: false },
            ticks: { color: '#ffffff', font: { family: 'Plus Jakarta Sans', weight: 'bold' } }
          }
        }
      }
    })
  }

  // Create Line Chart (Chronological progress)
  const initLineChart = (canvas) => {
    if (!canvas) return null
    const ctx = canvas.getContext('2d')
    
    // Process timeline
    const sorted = [...(stats.history || [])].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    const labels = ['Inicio']
    const googleSeries = [0]
    const competitorSeries = [0]
    const totalSeries = [0]

    let gVotes = 0
    let cVotes = 0
    let tVotes = 0

    sorted.forEach((item, idx) => {
      tVotes++
      // classify winner
      if (['gemini', 'google', 'a2e'].includes(item.winner)) {
        gVotes++
      } else {
        cVotes++
      }

      let timeLabel = ''
      try {
        const d = new Date(item.timestamp)
        timeLabel = `${d.getDate()}/${d.getMonth()+1} ${d.getHours()}:${d.getMinutes() < 10 ? '0' + d.getMinutes() : d.getMinutes()}`
      } catch (e) {
        timeLabel = item.timestamp
      }

      labels.push(timeLabel)
      googleSeries.push(gVotes)
      competitorSeries.push(cVotes)
      totalSeries.push(tVotes)
    })

    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Modelos Google/A2E (Ganados)',
            data: googleSeries,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.05)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: labels.length > 15 ? 0 : 3
          },
          {
            label: 'Competidores (Ganados)',
            data: competitorSeries,
            borderColor: '#a855f7',
            backgroundColor: 'rgba(168, 85, 247, 0.05)',
            fill: true,
            tension: 0.35,
            borderWidth: 2,
            pointRadius: labels.length > 15 ? 0 : 3
          },
          {
            label: 'Total Acumulado',
            data: totalSeries,
            borderColor: '#e4e4e7',
            borderWidth: 1.5,
            borderDash: [5, 5],
            fill: false,
            tension: 0.2,
            pointRadius: 0
          }
        ]
      },
      options: {
        ...getCommonOptions('Evolución de Preferencias en el Tiempo'),
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.03)' },
            ticks: { color: '#a1a1aa', font: { family: 'Plus Jakarta Sans', size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#a1a1aa', font: { family: 'Plus Jakarta Sans' } }
          }
        }
      }
    })
  }

  // Watch tab updates and reload charts
  useEffect(() => {
    destroyCharts()

    if (activeChartTab === 'grid') {
      chartInstances.current.doughnut = initDoughnutChart(doughnutCanvasRef.current)
      chartInstances.current.polar = initPolarChart(polarCanvasRef.current)
      chartInstances.current.bar = initBarChart(barCanvasRef.current)
      chartInstances.current.line = initLineChart(lineCanvasRef.current)
    } else if (activeChartTab === 'winrates') {
      chartInstances.current.single = initBarChart(singleBarCanvasRef.current)
    } else if (activeChartTab === 'providers') {
      chartInstances.current.single = initDoughnutChart(singleDoughnutCanvasRef.current)
    } else if (activeChartTab === 'history') {
      chartInstances.current.single = initLineChart(singleLineCanvasRef.current)
    }

    return () => destroyCharts()
  }, [activeChartTab, stats])

  return (
    <div className="stats-charts-container">
      <div className="charts-control-bar">
        <h3 className="charts-section-subtitle">Visualización de Estadísticas Avanzadas</h3>
        <div className="chart-tabs">
          <button 
            className={`chart-tab-btn ${activeChartTab === 'grid' ? 'active' : ''}`}
            onClick={() => setActiveChartTab('grid')}
          >
            Vista General
          </button>
          <button 
            className={`chart-tab-btn ${activeChartTab === 'winrates' ? 'active' : ''}`}
            onClick={() => setActiveChartTab('winrates')}
          >
            Tasas de Victoria
          </button>
          <button 
            className={`chart-tab-btn ${activeChartTab === 'providers' ? 'active' : ''}`}
            onClick={() => setActiveChartTab('providers')}
          >
            Cuotas por Proveedor
          </button>
          <button 
            className={`chart-tab-btn ${activeChartTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveChartTab('history')}
          >
            Historial de Crecimiento
          </button>
        </div>
      </div>

      {totalVotesCount === 0 ? (
        <div className="no-votes-placeholder">
          <div className="placeholder-icon">📊</div>
          <h4>Sin Votos Registrados Aún</h4>
          <p>Los gráficos interactivos se generarán de forma automática una vez que comiences a votar por tus modelos favoritos.</p>
        </div>
      ) : activeChartTab === 'grid' ? (
        <div className="charts-dashboard-grid">
          <div className="chart-wrapper-card">
            <div className="chart-canvas-container">
              <canvas ref={doughnutCanvasRef} />
            </div>
            <div className="chart-info-footer">
              <p>Google lidera la cuota de participación con un total de <strong>{providerVotes.Google}</strong> votos, seguido por Stability AI con <strong>{providerVotes.StabilityAI}</strong>.</p>
            </div>
          </div>

          <div className="chart-wrapper-card">
            <div className="chart-canvas-container">
              <canvas ref={polarCanvasRef} />
            </div>
            <div className="chart-info-footer">
              <p>Muestra el volumen acumulado de duelos por cada arena. La arena de mayor interacción es <strong>{textTotal >= visionTotal && textTotal >= imageTotal && textTotal >= videoTotal ? 'Texto' : visionTotal >= imageTotal && visionTotal >= videoTotal ? 'Visión' : imageTotal >= videoTotal ? 'Imagen' : 'Video'}</strong>.</p>
            </div>
          </div>

          <div className="chart-wrapper-card full-width">
            <div className="chart-canvas-container bar-height">
              <canvas ref={barCanvasRef} />
            </div>
            <div className="chart-info-footer">
              <p>Compara el porcentaje individual de victorias (winrate) de cada modelo en su respectivo formato de evaluación.</p>
            </div>
          </div>

          <div className="chart-wrapper-card full-width">
            <div className="chart-canvas-container line-height">
              <canvas ref={lineCanvasRef} />
            </div>
            <div className="chart-info-footer">
              <p>Evolución acumulativa de duelos decididos. Evalúa la tendencia competitiva de los modelos de Google contra competidores independientes.</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="single-chart-focused-card">
          {activeChartTab === 'winrates' && (
            <div className="chart-canvas-container focused-height">
              <canvas ref={singleBarCanvasRef} />
            </div>
          )}
          {activeChartTab === 'providers' && (
            <div className="chart-canvas-container focused-height">
              <canvas ref={singleDoughnutCanvasRef} />
            </div>
          )}
          {activeChartTab === 'history' && (
            <div className="chart-canvas-container focused-height">
              <canvas ref={singleLineCanvasRef} />
            </div>
          )}
          
          <div className="focused-chart-details">
            <h4>Análisis y Observaciones Clave</h4>
            {activeChartTab === 'winrates' && (
              <ul>
                <li>Este gráfico compara el rendimiento relativo de los modelos en duelos directos.</li>
                <li>Un porcentaje superior al 50% indica preferencia mayoritaria de los usuarios sobre su competidor en la arena.</li>
                <li>Los datos ayudan a discernir si las diferencias entre modelos (como Gemini frente a GPT-4o) realmente ofrecen una mejora perceptible para el usuario final.</li>
              </ul>
            )}
            {activeChartTab === 'providers' && (
              <ul>
                <li>Agrupa todos los votos de la plataforma según la empresa proveedora de la tecnología subyacente.</li>
                <li>Permite ver la penetración de ecosistemas como el de <strong>Google AI</strong> frente a proveedores como <strong>OpenAI</strong> o especialistas como <strong>Stability AI</strong> o <strong>A2E</strong>.</li>
                <li>Excelente para analizar si hay una tendencia a favor de soluciones monolíticas o si los usuarios prefieren herramientas de nicho.</li>
              </ul>
            )}
            {activeChartTab === 'history' && (
              <ul>
                <li>Muestra la trayectoria cronológica del total de votos registrados paso a paso.</li>
                <li>Permite identificar tendencias temporales y rachas de victorias seguidas de cada ecosistema.</li>
                <li>Los picos en la pendiente reflejan momentos de alta actividad de pruebas en la arena.</li>
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
