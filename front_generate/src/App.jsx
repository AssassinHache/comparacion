import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  // Mode Selection: 'text' | 'vision' | 'creation'
  const [arenaMode, setArenaMode] = useState('text')

  // Common inputs
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('Fantasía')
  const [aspectRatio, setAspectRatio] = useState('16:9')

  // Text mode specific
  const [contentType, setContentType] = useState('Cuento')
  const [length, setLength] = useState(150)

  // Vision mode specific
  const [visionImage, setVisionImage] = useState(null)
  const [visionImageB64, setVisionImageB64] = useState('')
  const [visionImageMime, setVisionImageMime] = useState('image/jpeg')
  const fileInputRef = useRef(null)

  // Creation mode specific
  const [creationType, setCreationType] = useState('imagen') // 'imagen' | 'video'

  // Loading & status states
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stepMessage, setStepMessage] = useState('')
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [activeTabMode, setActiveTabMode] = useState('text') // stores the mode of the current active result

  // Stats and voting states
  const [stats, setStats] = useState({
    text_votes: { gemini: 0, 'gpt-4o': 0 },
    vision_votes: { gemini: 0, 'gpt-4o': 0 },
    image_votes: { stability: 0, google: 0 },
    video_votes: { a2e: 0, stability: 0 },
    total_comparisons: 0,
    history: []
  })
  const [voted, setVoted] = useState(null) // tracks if user voted in this run: 'left' | 'right'

  // Load stats on mount
  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Error al obtener estadisticas:', err)
    }
  }

  // Handle Image Upload for Vision
  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setVisionImage(file)
      setVisionImageMime(file.type)
      
      const reader = new FileReader()
      reader.onloadend = () => {
        setVisionImageB64(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current.click()
  }

  const startComparison = async () => {
    if (!prompt.trim()) return
    if (arenaMode === 'vision' && !visionImageB64) {
      setError('Por favor, selecciona o sube una imagen para el analisis multimodal.')
      return
    }

    setIsLoading(true)
    setError(null)
    setResults(null)
    setVoted(null)
    setProgress(0)
    setStepMessage('Conectando con los servidores de procesamiento...')
    setActiveTabMode(arenaMode) // lock the mode of the active result

    try {
      let endpoint = '/api/generate/text'
      let payload = {}

      if (arenaMode === 'text') {
        endpoint = '/api/generate/text'
        payload = {
          prompt,
          content_type: contentType,
          style,
          length
        }
      } else if (arenaMode === 'vision') {
        endpoint = '/api/generate/vision'
        payload = {
          prompt,
          image_base64: visionImageB64,
          mime_type: visionImageMime
        }
      } else if (arenaMode === 'creation') {
        endpoint = '/api/generate/creation'
        payload = {
          prompt,
          style,
          aspect_ratio: aspectRatio,
          creation_type: creationType
        }
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Ocurrio un error en el servidor.')
      }

      const { task_id } = await response.json()
      pollTaskStatus(task_id)
    } catch (err) {
      setError(err.message || 'Error al iniciar la comparacion.')
      setIsLoading(false)
    }
  }

  const pollTaskStatus = (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/generate/status/${id}`)
        if (!response.ok) {
          throw new Error('Error al consultar el estado de la tarea.')
        }

        const data = await response.json()
        setProgress(data.progress)
        setStepMessage(data.step_message)

        if (data.status === 'completed') {
          clearInterval(interval)
          setResults(data.results)
          setIsLoading(false)
          fetchStats() // refresh stats
        } else if (data.status === 'failed') {
          clearInterval(interval)
          setError(data.step_message || 'El procesamiento de la tarea fallo.')
          setIsLoading(false)
        }
      } catch (err) {
        clearInterval(interval)
        setError(err.message || 'Error de conexion durante el procesamiento.')
        setIsLoading(false)
      }
    }, 2000)
  }

  const handleVote = async (category, model, side) => {
    if (voted) return // Prevent double voting

    try {
      const response = await fetch('/api/vote', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ category, model, prompt }),
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data.stats)
        setVoted(side)
      }
    } catch (err) {
      console.error('Error al registrar voto:', err)
    }
  }

  // Helper percentages calculation
  const getProgressPercentages = () => {
    if (arenaMode === 'text') {
      const total = stats.text_votes.gemini + stats.text_votes['gpt-4o']
      const a = total > 0 ? Math.round((stats.text_votes.gemini / total) * 100) : 50
      return { a, b: 100 - a, labelA: 'Gemini', labelB: 'GPT-4o' }
    } else if (arenaMode === 'vision') {
      const total = stats.vision_votes.gemini + stats.vision_votes['gpt-4o']
      const a = total > 0 ? Math.round((stats.vision_votes.gemini / total) * 100) : 50
      return { a, b: 100 - a, labelA: 'Gemini', labelB: 'GPT-4o' }
    } else { // creation
      if (creationType === 'imagen') {
        const total = stats.image_votes.stability + stats.image_votes.google
        const a = total > 0 ? Math.round((stats.image_votes.stability / total) * 100) : 50
        return { a, b: 100 - a, labelA: 'Stability', labelB: 'Pollinations' }
      } else {
        const total = stats.video_votes.a2e + stats.video_votes.stability
        const a = total > 0 ? Math.round((stats.video_votes.a2e / total) * 100) : 50
        return { a, b: 100 - a, labelA: 'A2E Kling', labelB: 'Stability' }
      }
    }
  }

  const statsPct = getProgressPercentages()

  // Detailed Statistics Calculations for the new explicitly large statistics dashboard
  const textTotal = (stats.text_votes?.gemini || 0) + (stats.text_votes?.['gpt-4o'] || 0)
  const visionTotal = (stats.vision_votes?.gemini || 0) + (stats.vision_votes?.['gpt-4o'] || 0)
  const imageTotal = (stats.image_votes?.google || 0) + (stats.image_votes?.stability || 0)
  const videoTotal = (stats.video_votes?.a2e || 0) + (stats.video_votes?.stability || 0)
  const totalVotesCount = textTotal + visionTotal + imageTotal + videoTotal

  // Win percentages for splitting progress bars in all categories
  const textGeminiPct = textTotal > 0 ? Math.round((stats.text_votes.gemini / textTotal) * 100) : 50
  const textLlamaPct = 100 - textGeminiPct

  const visionGemini25Pct = visionTotal > 0 ? Math.round((stats.vision_votes.gemini / visionTotal) * 100) : 50
  const visionGemini15Pct = 100 - visionGemini25Pct

  const imageGooglePct = imageTotal > 0 ? Math.round((stats.image_votes.google / imageTotal) * 100) : 50
  const imageStabilityPct = 100 - imageGooglePct

  const videoA2EPct = videoTotal > 0 ? Math.round((stats.video_votes.a2e / videoTotal) * 100) : 50
  const videoStabilityPct = 100 - videoA2EPct

  // Leaderboard data preparation
  const leaderboardList = [
    {
      name: 'Google Gemini 2.5 Flash',
      category: 'Texto y Visión (Modelo A)',
      votes: (stats.text_votes?.gemini || 0) + (stats.vision_votes?.gemini || 0),
      totalDuels: textTotal + visionTotal,
      winRate: (textTotal + visionTotal) > 0 ? Math.round((((stats.text_votes?.gemini || 0) + (stats.vision_votes?.gemini || 0)) / (textTotal + visionTotal)) * 100) : 0,
      icon: '🧠'
    },
    {
      name: 'Llama 3 (Pollinations)',
      category: 'Generación de Texto (Modelo B)',
      votes: stats.text_votes?.['gpt-4o'] || 0,
      totalDuels: textTotal,
      winRate: textTotal > 0 ? Math.round(((stats.text_votes?.['gpt-4o'] || 0) / textTotal) * 100) : 0,
      icon: '📝'
    },
    {
      name: 'Google Gemini 1.5 Flash',
      category: 'Análisis de Visión (Modelo B)',
      votes: stats.vision_votes?.['gpt-4o'] || 0,
      totalDuels: visionTotal,
      winRate: visionTotal > 0 ? Math.round(((stats.vision_votes?.['gpt-4o'] || 0) / visionTotal) * 100) : 0,
      icon: '👁️'
    },
    {
      name: 'Google Imagen 3',
      category: 'Generación de Imagen (Modelo A)',
      votes: stats.image_votes?.google || 0,
      totalDuels: imageTotal,
      winRate: imageTotal > 0 ? Math.round(((stats.image_votes?.google || 0) / imageTotal) * 100) : 0,
      icon: '🎨'
    },
    {
      name: 'Pollinations Flux (Stable)',
      category: 'Generación de Imagen (Modelo B)',
      votes: stats.image_votes?.stability || 0,
      totalDuels: imageTotal,
      winRate: imageTotal > 0 ? Math.round(((stats.image_votes?.stability || 0) / imageTotal) * 100) : 0,
      icon: '⚡'
    },
    {
      name: 'A2E Kling',
      category: 'Generación de Video (Modelo A)',
      votes: stats.video_votes?.a2e || 0,
      totalDuels: videoTotal,
      winRate: videoTotal > 0 ? Math.round(((stats.video_votes?.a2e || 0) / videoTotal) * 100) : 0,
      icon: '🎬'
    },
    {
      name: 'Stability Video SVD',
      category: 'Generación de Video (Modelo B)',
      votes: stats.video_votes?.stability || 0,
      totalDuels: videoTotal,
      winRate: videoTotal > 0 ? Math.round(((stats.video_votes?.stability || 0) / videoTotal) * 100) : 0,
      icon: '🌀'
    }
  ]

  // Sort by total votes descending, then by win rate descending
  const sortedLeaderboard = [...leaderboardList].sort((a, b) => {
    if (b.votes !== a.votes) return b.votes - a.votes
    return b.winRate - a.winRate
  })

  // Global Arena Leader Model
  const globalLeaderModel = sortedLeaderboard[0] && sortedLeaderboard[0].votes > 0 ? sortedLeaderboard[0] : null

  // Arena Activity Ranking
  const arenaActivity = [
    { name: 'Texto', total: textTotal, icon: '📝' },
    { name: 'Visión Multimodal', total: visionTotal, icon: '👁️' },
    { name: 'Imagen', total: imageTotal, icon: '🎨' },
    { name: 'Video', total: videoTotal, icon: '🎬' }
  ].sort((a, b) => b.total - a.total)

  const topActiveArena = arenaActivity[0] && arenaActivity[0].total > 0 ? arenaActivity[0] : null

  return (
    <div className="app-container">
      {/* Dynamic Glass Header */}
      <header className="app-header">
        <div className="header-title-wrapper">
          <span className="logo-badge">Version Multimodal</span>
          <h1>Comparador de Modelos de Inteligencia Artificial</h1>
          <p>Plataforma para evaluar y contrastar el rendimiento de modelos en Texto, Vision e Imagenes</p>
        </div>
        <div className="total-comparisons-badge">
          Votos Totales: {stats.total_comparisons}
        </div>
      </header>

      {/* Mode navigation bar */}
      <div className="arena-mode-navbar">
        <button 
          className={`mode-nav-btn ${arenaMode === 'text' ? 'active' : ''}`}
          onClick={() => !isLoading && setArenaMode('text')}
        >
          Generacion de Texto (Gemini vs Llama)
        </button>
        <button 
          className={`mode-nav-btn ${arenaMode === 'vision' ? 'active' : ''}`}
          onClick={() => !isLoading && setArenaMode('vision')}
        >
          Analisis Multimodal de Imagen (Gemini 2.5 vs Gemini 1.5)
        </button>
        <button 
          className={`mode-nav-btn ${arenaMode === 'creation' ? 'active' : ''}`}
          onClick={() => !isLoading && setArenaMode('creation')}
        >
          Generacion de Imagen y Video (Google vs Pollinations / A2E)
        </button>
      </div>

      <main className="dashboard-grid">
        {/* Sidebar Controls */}
        <aside className="sidebar-panel">
          <h2 className="section-title">
            {arenaMode === 'text' && 'Generacion de Texto'}
            {arenaMode === 'vision' && 'Analisis Multimodal'}
            {arenaMode === 'creation' && 'Generacion Visual'}
          </h2>

          {/* VISION MODE IMAGE INPUT */}
          {arenaMode === 'vision' && (
            <div className="form-group">
              <label>Subir Imagen</label>
              <div 
                className="image-upload-dropzone" 
                onClick={triggerFileInput}
                style={{ backgroundImage: visionImageB64 ? `url(${visionImageB64})` : 'none' }}
              >
                {!visionImageB64 && (
                  <>
                    <span className="upload-icon-fallback">Subir Archivo</span>
                    <p className="upload-text">Selecciona una imagen de tu sistema</p>
                  </>
                )}
              </div>
              <input
                type="file"
                ref={fileInputRef}
                className="hidden-file-input"
                accept="image/*"
                onChange={handleImageChange}
                disabled={isLoading}
                style={{ display: 'none' }}
              />
            </div>
          )}

          {/* MAIN PROMPT FOR ALL MODES */}
          <div className="form-group">
            <label htmlFor="prompt-input">
              {arenaMode === 'text' && 'Instruccion para Generacion de Texto'}
              {arenaMode === 'vision' && 'Instruccion para Analisis Multimodal'}
              {arenaMode === 'creation' && 'Prompt Descriptivo para Imagen / Video'}
            </label>
            <textarea
              id="prompt-input"
              className="textarea-field"
              placeholder={
                arenaMode === 'text' ? 'Escribe aqui tu peticion...' :
                arenaMode === 'vision' ? 'Escribe que deben hacer los modelos con la imagen...' :
                'Escribe la descripcion de la imagen o video a generar...'
              }
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {/* TEXT MODE PARAMS */}
          {arenaMode === 'text' && (
            <>
              <div className="form-group">
                <label htmlFor="type-select">Formato del Texto</label>
                <select
                  id="type-select"
                  className="select-field"
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                  disabled={isLoading}
                >
                  <option value="Cuento">Cuento / Relato</option>
                  <option value="Artículo">Articulo Critico</option>
                  <option value="Poema">Poema Libre</option>
                  <option value="Marketing Copy">Copia de Marketing</option>
                </select>
              </div>

              <div className="slider-group">
                <div className="slider-header">
                  <label>Extension</label>
                  <span className="slider-value">{length} palabras</span>
                </div>
                <input
                  type="range"
                  min="80"
                  max="300"
                  step="10"
                  value={length}
                  onChange={(e) => setLength(parseInt(e.target.value))}
                  disabled={isLoading}
                />
              </div>
            </>
          )}

          {/* CREATION MODE SPECIFICS */}
          {arenaMode === 'creation' && (
            <>
              <div className="form-group">
                <label>Tipo de Formato Visual</label>
                <div className="creation-type-toggle">
                  <button 
                    className={`toggle-btn ${creationType === 'imagen' ? 'active' : ''}`}
                    onClick={() => setCreationType('imagen')}
                    disabled={isLoading}
                  >
                    Imagen
                  </button>
                  <button 
                    className={`toggle-btn ${creationType === 'video' ? 'active' : ''}`}
                    onClick={() => setCreationType('video')}
                    disabled={isLoading}
                  >
                    Video
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="aspect-select">Relacion de Aspecto</label>
                <select
                  id="aspect-select"
                  className="select-field"
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  disabled={isLoading}
                >
                  <option value="16:9">Horizontal (16:9)</option>
                  <option value="9:16">Vertical (9:16)</option>
                  <option value="1:1">Cuadrado (1:1)</option>
                </select>
              </div>
            </>
          )}

          {/* STYLE SELECTION (for Text and Creation) */}
          {arenaMode !== 'vision' && (
            <div className="form-group">
              <label htmlFor="style-select">Estilo Visual</label>
              <select
                id="style-select"
                className="select-field"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                disabled={isLoading}
              >
                <option value="Fantasía">Fantasia Artistica</option>
                <option value="Ciencia ficción">Ciencia Ficcion / Cinematic</option>
                <option value="Marketing">Marketing / Premium</option>
              </select>
            </div>
          )}

          {/* INITIATE BUTTON */}
          <button
            className="btn-primary"
            onClick={startComparison}
            disabled={isLoading || !prompt.trim()}
          >
            {isLoading ? 'Procesando...' : 'Ejecutar Comparacion'}
          </button>

          {/* Statistics summary widget */}
          <div className="stats-summary-card">
            <h3 className="stats-title">
              Estadisticas Globales de Votos
            </h3>
            
            <div className="stats-row">
              <div className="stats-labels">
                <span>{statsPct.labelA} ({statsPct.a}%)</span>
                <span>{statsPct.labelB} ({statsPct.b}%)</span>
              </div>
              <div className="stats-bar-outer">
                <div className="stats-bar-fill-a" style={{ width: `${statsPct.a}%` }} />
                <div className="stats-bar-fill-b" style={{ width: `${statsPct.b}%` }} />
              </div>
            </div>
          </div>
        </aside>

        {/* Workspace Display */}
        <section className="comparison-arena">
          {error && (
            <div className="error-banner">
              Error detectado: {error}
            </div>
          )}

          {isLoading ? (
            <div className="loading-wrapper">
              <div className="loader-spinner"></div>
              <h3 className="loading-title">Procesando Comparacion</h3>
              <p className="loading-step">{stepMessage}</p>
              
              <div className="progress-container">
                <div className="progress-bar" style={{ width: `${progress}%` }}></div>
              </div>
              <p className="loading-tips">
                {progress < 30 
                  ? 'Estableciendo comunicacion con los modelos...' 
                  : progress < 70 
                    ? 'Procesando las instrucciones en paralelo...' 
                    : 'Guardando y preparando la visualizacion de datos...'}
              </p>
            </div>
          ) : results ? (
            <div className="arena-columns-wrapper">
              {/* Reference Image on Vision Mode */}
              {activeTabMode === 'vision' && visionImageB64 && (
                <div className="vision-reference-card">
                  <span className="content-label">Imagen de Referencia</span>
                  <img src={visionImageB64} alt="Referencia" className="vision-ref-img" />
                </div>
              )}

              <div className="arena-columns">
                {/* COLUMN LEFT: Gemini or Stability */}
                <div className={`model-column-card ${activeTabMode === 'creation' ? 'stability-theme' : 'gemini-theme'}`}>
                  <div className="card-header">
                    <div className="model-info">
                      <div className="model-meta">
                        <span className="model-brand-name">
                          {activeTabMode === 'creation' ? (creationType === 'imagen' ? 'Google Imagen' : 'A2E AI') : 'Google Gemini'}
                        </span>
                        <span className="model-codename">
                          {activeTabMode === 'text' && 'gemini-2.5-flash'}
                          {activeTabMode === 'vision' && 'gemini-2.5-flash'}
                          {activeTabMode === 'creation' && (creationType === 'imagen' ? 'Imagen 3.0' : 'A2E Kling / Wan')}
                        </span>
                      </div>
                    </div>
                    <span className="provider-badge">Modelo A</span>
                  </div>

                  {/* RENDER CONTENT LEFT */}
                  <div className="card-content-section">
                    <span className="content-label">Resultado</span>
                    
                    {/* TEXT OR VISION MODES */}
                    {(activeTabMode === 'text' || activeTabMode === 'vision') && (
                      <div className="generated-text-container">
                        {results.text_gemini.split('\n\n').map((para, idx) => (
                          <p key={idx}>{para}</p>
                        ))}
                      </div>
                    )}

                    {/* CREATION MODE IMAGE */}
                    {activeTabMode === 'creation' && creationType === 'imagen' && (
                      <div className="image-render-box">
                        {results.image_base64_a ? (
                          <img 
                            src={`data:${results.mime_type_a};base64,${results.image_base64_a}`} 
                            alt="Stability AI" 
                            className="rendered-img"
                          />
                        ) : (
                          <div className="video-loading-placeholder">
                            <p>Error en la generacion de imagen.</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* CREATION MODE VIDEO */}
                    {activeTabMode === 'creation' && creationType === 'video' && (
                      <div className={`video-render-box ${aspectRatio === '1:1' ? 'aspect-1-1' : ''}`}>
                        {results.video_a2e ? (
                          <video 
                            className="video-player" 
                            src={results.video_a2e} 
                            controls 
                            loop 
                            autoPlay 
                            muted 
                            playsInline
                          />
                        ) : (
                          <div className="video-loading-placeholder">
                            <p>Error en la generacion de video.</p>
                          </div>
                        )}
                        <span className="video-meta-tag">A2E AI</span>
                      </div>
                    )}
                  </div>

                  {/* VOTING BUTTON LEFT */}
                  <div className="voting-container">
                    <button 
                      className={`voting-btn ${voted === 'left' ? 'voted' : ''}`}
                      onClick={() => {
                        const category = activeTabMode === 'text' ? 'text' : activeTabMode === 'vision' ? 'vision' : (creationType === 'imagen' ? 'image' : 'video')
                        const model = activeTabMode === 'creation' ? (creationType === 'imagen' ? 'google' : 'a2e') : 'gemini'
                        handleVote(category, model, 'left')
                      }}
                      disabled={voted !== null}
                    >
                      <span>{voted === 'left' ? 'Voto Registrado' : 'Votar por este resultado'}</span>
                    </button>
                  </div>
                </div>

                {/* COLUMN RIGHT: OpenAI GPT-4o or Google Imagen / Stability Video */}
                <div className={`model-column-card ${activeTabMode === 'creation' ? 'google-theme' : 'openai-theme'}`}>
                  <div className="card-header">
                    <div className="model-info">
                      <div className="model-meta">
                        <span className="model-brand-name">
                          {activeTabMode === 'creation' ? (creationType === 'imagen' ? 'Pollinations.ai' : 'Stability AI') : (activeTabMode === 'vision' ? 'Google Gemini' : 'Llama 3')}
                        </span>
                        <span className="model-codename">
                          {activeTabMode === 'text' && 'Llama-3 (Pollinations)'}
                          {activeTabMode === 'vision' && 'gemini-1.5-flash'}
                          {activeTabMode === 'creation' && (creationType === 'imagen' ? 'Flux Model' : 'Stable Video Diffusion')}
                        </span>
                      </div>
                    </div>
                    <span className="provider-badge">Modelo B</span>
                  </div>

                  {/* RENDER CONTENT RIGHT */}
                  <div className="card-content-section">
                    <span className="content-label">Resultado</span>
                    
                    {/* TEXT OR VISION MODES */}
                    {(activeTabMode === 'text' || activeTabMode === 'vision') && (
                      <div className="generated-text-container">
                        {results.text_openai.split('\n\n').map((para, idx) => (
                          <p key={idx}>{para}</p>
                        ))}
                      </div>
                    )}

                    {/* CREATION MODE IMAGE */}
                    {activeTabMode === 'creation' && creationType === 'imagen' && (
                      <div className="image-render-box">
                        {results.image_base64_b ? (
                          <img 
                            src={`data:${results.mime_type_b};base64,${results.image_base64_b}`} 
                            alt="Pollinations.ai" 
                            className="rendered-img"
                          />
                        ) : (
                          <div className="video-loading-placeholder">
                            <p>Error en la generacion de imagen.</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* CREATION MODE VIDEO */}
                    {activeTabMode === 'creation' && creationType === 'video' && (
                      <div className={`video-render-box ${aspectRatio === '1:1' ? 'aspect-1-1' : ''}`}>
                        {results.video_stability ? (
                          <video 
                            className="video-player" 
                            src={results.video_stability} 
                            controls 
                            loop 
                            autoPlay 
                            muted 
                            playsInline
                          />
                        ) : (
                          <div className="video-loading-placeholder">
                            <p>Error en la generacion de video.</p>
                          </div>
                        )}
                        <span className="video-meta-tag">Stability Video</span>
                      </div>
                    )}
                  </div>

                  {/* VOTING BUTTON RIGHT */}
                  <div className="voting-container">
                    <button 
                      className={`voting-btn ${voted === 'right' ? 'voted' : ''}`}
                      onClick={() => {
                        const category = activeTabMode === 'text' ? 'text' : activeTabMode === 'vision' ? 'vision' : (creationType === 'imagen' ? 'image' : 'video')
                        const model = activeTabMode === 'creation' ? (creationType === 'imagen' ? 'stability' : 'stability') : 'gpt-4o'
                        handleVote(category, model, 'right')
                      }}
                      disabled={voted !== null}
                    >
                      <span>{voted === 'right' ? 'Voto Registrado' : 'Votar por este resultado'}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* AUTOMATIC EVALUATION SCOREBOARD */}
              {results.evaluation && (
                <div className="automatic-evaluation-card">
                  <h3 className="evaluation-title">Evaluacion de Coherencia Automatica (Analisis del Juez IA)</h3>
                  <div className="evaluation-scores-container">
                    <div className="score-block model-a-score">
                      <span className="score-label">Puntaje Modelo A</span>
                      <div className="score-circle-glow">
                        <span className="score-number">{results.evaluation.score_a}</span>
                        <span className="score-max">/ 10</span>
                      </div>
                      <span className="score-model-name">
                        {activeTabMode === 'creation' ? 'Google Imagen' : 'Google Gemini 2.5'}
                      </span>
                    </div>

                    <div className="score-divider">VS</div>

                    <div className="score-block model-b-score">
                      <span className="score-label">Puntaje Modelo B</span>
                      <div className="score-circle-glow">
                        <span className="score-number">{results.evaluation.score_b}</span>
                        <span className="score-max">/ 10</span>
                      </div>
                      <span className="score-model-name">
                        {activeTabMode === 'creation' ? (creationType === 'imagen' ? 'Pollinations.ai' : 'Stability AI') : (activeTabMode === 'vision' ? 'Google Gemini 1.5' : 'Llama 3')}
                      </span>
                    </div>
                  </div>
                  <div className="evaluation-analysis-block">
                    <span className="analysis-label">Analisis Comparativo Detallado</span>
                    <p className="analysis-text">{results.evaluation.analysis}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-arena">
              <h3>Sistema Listo</h3>
              <p>
                {arenaMode === 'text' && 'Ingresa una instruccion para iniciar la comparacion narrativa de texto (Gemini vs GPT-4o).'}
                {arenaMode === 'vision' && 'Carga una imagen y define la instruccion para comparar el analisis visual (Gemini Vision vs GPT-4o Vision).'}
                {arenaMode === 'creation' && 'Ingresa la descripcion para comparar la generacion de imagen o video (Stability vs Pollinations / A2E).'}
              </p>
            </div>
          )}

          {/* ================= GORGEOUS DETAILED GLOBAL STATS DASHBOARD ================= */}
          <div className="global-stats-dashboard">
            <div className="stats-dashboard-header">
              <div className="stats-dashboard-title-wrapper">
                <h2 className="stats-dashboard-title">
                  📊 Dashboard de Rendimiento y Estadísticas de Modelos
                </h2>
                <p className="stats-dashboard-subtitle">
                  Análisis global detallado de las preferencias y rendimiento de cada modelo en tiempo real.
                </p>
              </div>
            </div>

            {/* Metric Summary Cards Grid */}
            <div className="stats-metrics-grid">
              <div className="metric-card">
                <div className="metric-icon-wrapper">
                  🗳️
                </div>
                <div className="metric-details">
                  <span className="metric-value">{totalVotesCount}</span>
                  <span className="metric-label">Votos Registrados</span>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrapper leader-icon">
                  🏆
                </div>
                <div className="metric-details">
                  <span className="metric-value" style={{ fontSize: globalLeaderModel ? '1.15rem' : '1.75rem' }}>
                    {globalLeaderModel ? globalLeaderModel.name : 'Sin Votos'}
                  </span>
                  <span className="metric-label">
                    {globalLeaderModel ? `Líder Global (${globalLeaderModel.votes} votos)` : 'Líder General'}
                  </span>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrapper activity-icon">
                  🔥
                </div>
                <div className="metric-details">
                  <span className="metric-value" style={{ fontSize: topActiveArena ? '1.25rem' : '1.75rem' }}>
                    {topActiveArena ? `${topActiveArena.name}` : 'Ninguna'}
                  </span>
                  <span className="metric-label">
                    {topActiveArena ? `Arena Más Activa (${topActiveArena.total} duelos)` : 'Arena Favorita'}
                  </span>
                </div>
              </div>
            </div>

            {/* Grid of Split Progress Bars (All categories at once) */}
            <h3 className="leaderboard-title" style={{ marginTop: '0.5rem', marginBottom: '-0.5rem' }}>
              🎯 Distribución de Votos por Categoría de Combate
            </h3>
            
            <div className="arenas-split-grid">
              {/* Category 1: Texto */}
              <div className="arena-split-card text-card">
                <div className="arena-split-header">
                  <span className="arena-split-title">📝 Texto (Gemini vs Llama)</span>
                  <span className="arena-split-total">{textTotal} votos</span>
                </div>
                <div className="competitor-row">
                  <div className="competitor-info">
                    <span className="competitor-name">Google Gemini 2.5</span>
                    <span className="competitor-stats">
                      {stats.text_votes?.gemini || 0} votos ({textGeminiPct}%)
                      {stats.text_votes?.gemini > stats.text_votes?.['gpt-4o'] && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                  <div className="competitor-info">
                    <span className="competitor-name">Llama 3 (Pollinations)</span>
                    <span className="competitor-stats">
                      {stats.text_votes?.['gpt-4o'] || 0} votos ({textLlamaPct}%)
                      {stats.text_votes?.['gpt-4o'] > stats.text_votes?.gemini && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                </div>
                <div className="arena-bar-wrapper">
                  <div className="arena-progress-bar">
                    <div className="arena-progress-fill-a" style={{ width: `${textGeminiPct}%` }} />
                    <div className="arena-progress-fill-b" style={{ width: `${textLlamaPct}%` }} />
                  </div>
                </div>
                <div className="arena-card-footer">
                  <span className={`arena-leader-tag ${stats.text_votes?.gemini !== stats.text_votes?.['gpt-4o'] ? 'leader' : 'tie'}`}>
                    {stats.text_votes?.gemini > stats.text_votes?.['gpt-4o'] ? '🏆 Líder: Gemini' : stats.text_votes?.gemini < stats.text_votes?.['gpt-4o'] ? '🏆 Líder: Llama 3' : '⚖️ Empate Técnico'}
                  </span>
                  <span className="arena-dominance-pct">
                    {textTotal > 0 ? `Margen: ${Math.abs(textGeminiPct - textLlamaPct)}%` : 'Sin datos'}
                  </span>
                </div>
              </div>

              {/* Category 2: Visión */}
              <div className="arena-split-card vision-card">
                <div className="arena-split-header">
                  <span className="arena-split-title">👁️ Visión (Gemini 2.5 vs 1.5)</span>
                  <span className="arena-split-total">{visionTotal} votos</span>
                </div>
                <div className="competitor-row">
                  <div className="competitor-info">
                    <span className="competitor-name">Gemini 2.5 Flash</span>
                    <span className="competitor-stats">
                      {stats.vision_votes?.gemini || 0} votos ({visionGemini25Pct}%)
                      {stats.vision_votes?.gemini > stats.vision_votes?.['gpt-4o'] && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                  <div className="competitor-info">
                    <span className="competitor-name">Gemini 1.5 Flash</span>
                    <span className="competitor-stats">
                      {stats.vision_votes?.['gpt-4o'] || 0} votos ({visionGemini15Pct}%)
                      {stats.vision_votes?.['gpt-4o'] > stats.vision_votes?.gemini && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                </div>
                <div className="arena-bar-wrapper">
                  <div className="arena-progress-bar">
                    <div className="arena-progress-fill-a" style={{ width: `${visionGemini25Pct}%` }} />
                    <div className="arena-progress-fill-b" style={{ width: `${visionGemini15Pct}%` }} />
                  </div>
                </div>
                <div className="arena-card-footer">
                  <span className={`arena-leader-tag ${stats.vision_votes?.gemini !== stats.vision_votes?.['gpt-4o'] ? 'leader' : 'tie'}`}>
                    {stats.vision_votes?.gemini > stats.vision_votes?.['gpt-4o'] ? '🏆 Líder: Gemini 2.5' : stats.vision_votes?.gemini < stats.vision_votes?.['gpt-4o'] ? '🏆 Líder: Gemini 1.5' : '⚖️ Empate Técnico'}
                  </span>
                  <span className="arena-dominance-pct">
                    {visionTotal > 0 ? `Margen: ${Math.abs(visionGemini25Pct - visionGemini15Pct)}%` : 'Sin datos'}
                  </span>
                </div>
              </div>

              {/* Category 3: Imagen */}
              <div className="arena-split-card image-card">
                <div className="arena-split-header">
                  <span className="arena-split-title">🎨 Imagen (Imagen 3 vs Flux)</span>
                  <span className="arena-split-total">{imageTotal} votos</span>
                </div>
                <div className="competitor-row">
                  <div className="competitor-info">
                    <span className="competitor-name">Google Imagen 3</span>
                    <span className="competitor-stats">
                      {stats.image_votes?.google || 0} votos ({imageGooglePct}%)
                      {stats.image_votes?.google > stats.image_votes?.stability && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                  <div className="competitor-info">
                    <span className="competitor-name">Pollinations Flux</span>
                    <span className="competitor-stats">
                      {stats.image_votes?.stability || 0} votos ({imageStabilityPct}%)
                      {stats.image_votes?.stability > stats.image_votes?.google && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                </div>
                <div className="arena-bar-wrapper">
                  <div className="arena-progress-bar">
                    <div className="arena-progress-fill-a" style={{ width: `${imageGooglePct}%` }} />
                    <div className="arena-progress-fill-b" style={{ width: `${imageStabilityPct}%` }} />
                  </div>
                </div>
                <div className="arena-card-footer">
                  <span className={`arena-leader-tag ${stats.image_votes?.google !== stats.image_votes?.stability ? 'leader' : 'tie'}`}>
                    {stats.image_votes?.google > stats.image_votes?.stability ? '🏆 Líder: Imagen 3' : stats.image_votes?.google < stats.image_votes?.stability ? '🏆 Líder: Flux' : '⚖️ Empate Técnico'}
                  </span>
                  <span className="arena-dominance-pct">
                    {imageTotal > 0 ? `Margen: ${Math.abs(imageGooglePct - imageStabilityPct)}%` : 'Sin datos'}
                  </span>
                </div>
              </div>

              {/* Category 4: Video */}
              <div className="arena-split-card video-card">
                <div className="arena-split-header">
                  <span className="arena-split-title">🎬 Video (A2E vs Stability)</span>
                  <span className="arena-split-total">{videoTotal} votos</span>
                </div>
                <div className="competitor-row">
                  <div className="competitor-info">
                    <span className="competitor-name">A2E Kling</span>
                    <span className="competitor-stats">
                      {stats.video_votes?.a2e || 0} votos ({videoA2EPct}%)
                      {stats.video_votes?.a2e > stats.video_votes?.stability && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                  <div className="competitor-info">
                    <span className="competitor-name">Stability Video SVD</span>
                    <span className="competitor-stats">
                      {stats.video_votes?.stability || 0} votos ({videoStabilityPct}%)
                      {stats.video_votes?.stability > stats.video_votes?.a2e && <span className="competitor-pill winner">Líder</span>}
                    </span>
                  </div>
                </div>
                <div className="arena-bar-wrapper">
                  <div className="arena-progress-bar">
                    <div className="arena-progress-fill-a" style={{ width: `${videoA2EPct}%` }} />
                    <div className="arena-progress-fill-b" style={{ width: `${videoStabilityPct}%` }} />
                  </div>
                </div>
                <div className="arena-card-footer">
                  <span className={`arena-leader-tag ${stats.video_votes?.a2e !== stats.video_votes?.stability ? 'leader' : 'tie'}`}>
                    {stats.video_votes?.a2e > stats.video_votes?.stability ? '🏆 Líder: A2E Kling' : stats.video_votes?.a2e < stats.video_votes?.stability ? '🏆 Líder: Stability Video' : '⚖️ Empate Técnico'}
                  </span>
                  <span className="arena-dominance-pct">
                    {videoTotal > 0 ? `Margen: ${Math.abs(videoA2EPct - videoStabilityPct)}%` : 'Sin datos'}
                  </span>
                </div>
              </div>
            </div>

            {/* Leaderboard Table Section */}
            <div className="leaderboard-section">
              <h3 className="leaderboard-title">
                🏆 Tabla de Clasificación General de Modelos (Leaderboard)
              </h3>
              <div className="leaderboard-table-wrapper">
                <table className="leaderboard-table">
                  <thead>
                    <tr>
                      <th>Puesto</th>
                      <th>Modelo de Inteligencia Artificial</th>
                      <th>Categoría Principal</th>
                      <th>Votos Globales</th>
                      <th>Porcentaje de Victorias</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedLeaderboard.map((model, idx) => {
                      const rankMedal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '';
                      const rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : 'rank-other';
                      
                      return (
                        <tr key={idx}>
                          <td className="rank-cell">
                            <span className={`rank-badge ${rankClass}`}>
                              {rankMedal ? rankMedal : idx + 1}
                            </span>
                          </td>
                          <td className="model-cell">
                            <span style={{ marginRight: '0.4rem' }}>{model.icon}</span> {model.name}
                          </td>
                          <td className="category-cell">
                            {model.category}
                          </td>
                          <td className="votes-cell">
                            {model.votes} votos
                          </td>
                          <td className="winrate-cell">
                            <span style={{ fontWeight: 800, color: model.winRate > 50 ? '#34d399' : model.winRate === 0 ? '#94a3b8' : '#fb7185' }}>
                              {model.winRate}%
                            </span>
                            <div className="winrate-bar-outer">
                              <div className="winrate-bar-inner" style={{ width: `${model.winRate}%` }} />
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Duels History by Prompt Log Table */}
          {stats.history && stats.history.length > 0 && (
            <div className="comparison-history-section">
              <h3 className="history-section-title">Historial de Comparaciones por Prompt</h3>
              <div className="history-table-wrapper">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Prompt</th>
                      <th>Formato / Arena</th>
                      <th>Modelo Mas Acertado (Ganador)</th>
                      <th>Fecha y Hora</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.history.map((item, idx) => {
                      const categoryLabels = {
                        text: "Generacion de Texto",
                        vision: "Analisis Multimodal",
                        image: "Generacion de Imagen",
                        video: "Generacion de Video"
                      };
                      
                      const winnerLabels = {
                        gemini: "Google Gemini 2.5",
                        'gpt-4o': "Llama 3",
                        google: "Google Imagen",
                        stability: "Pollinations Flux",
                        a2e: "A2E Kling"
                      };
                      
                      // Map vision category winner labels to the correct version
                      let winnerName = winnerLabels[item.winner] || item.winner;
                      if (item.category === 'vision') {
                        winnerName = item.winner === 'gemini' ? 'Google Gemini 2.5' : 'Google Gemini 1.5';
                      } else if (item.category === 'video') {
                        winnerName = item.winner === 'a2e' ? 'A2E Kling' : 'Stability Video';
                      }

                      return (
                        <tr key={idx}>
                          <td className="history-prompt-cell" title={item.prompt}>
                            {item.prompt.length > 70 ? item.prompt.substring(0, 68) + "..." : item.prompt}
                          </td>
                          <td>
                            <span className={`category-badge badge-${item.category}`}>
                              {categoryLabels[item.category] || item.category}
                            </span>
                          </td>
                          <td>
                            <span className={`winner-badge winner-${item.winner}`}>
                              {winnerName}
                            </span>
                          </td>
                          <td className="history-date-cell">{item.timestamp}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
