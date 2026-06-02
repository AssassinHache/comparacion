import React, { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'

export default function EvaluationChart({ evaluation, modelAName, modelBName, mode }) {
  const canvasRef = useRef(null)
  const chartInstanceRef = useRef(null)

  useEffect(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy()
      chartInstanceRef.current = null
    }

    if (canvasRef.current && evaluation) {
      const ctx = canvasRef.current.getContext('2d')
      
      const isTextOrVision = mode === 'text' || mode === 'vision'
      
      // Determine criteria keys & labels
      const criteriaKeys = isTextOrVision 
        ? ['prompt_adherence', 'coherence', 'creativity', 'accuracy', 'writing_quality']
        : ['prompt_adherence', 'composition', 'aesthetics', 'coherence', 'realism_artistry']

      const labels = isTextOrVision
        ? ['Adherencia al Prompt', 'Coherencia Narrativa', 'Creatividad y Estilo', 'Precisión / Veracidad', 'Calidad de Redacción']
        : ['Adherencia al Prompt', 'Composición y Encuadre', 'Estética e Iluminación', 'Coherencia Visual', 'Calidad Artística']

      // Extract values or use fallbacks
      const criteriaA = evaluation.criteria_a || {}
      const criteriaB = evaluation.criteria_b || {}

      const dataA = criteriaKeys.map(k => criteriaA[k] !== undefined ? criteriaA[k] : 8)
      const dataB = criteriaKeys.map(k => criteriaB[k] !== undefined ? criteriaB[k] : 8)

      // Create glowing gradient fills
      const fillGradA = ctx.createLinearGradient(0, 0, 0, 300)
      fillGradA.addColorStop(0, 'rgba(56, 189, 248, 0.45)')
      fillGradA.addColorStop(1, 'rgba(56, 189, 248, 0.05)')

      const fillGradB = ctx.createLinearGradient(0, 0, 0, 300)
      fillGradB.addColorStop(0, 'rgba(168, 85, 247, 0.45)')
      fillGradB.addColorStop(1, 'rgba(168, 85, 247, 0.05)')

      chartInstanceRef.current = new Chart(ctx, {
        type: 'radar',
        data: {
          labels,
          datasets: [
            {
              label: modelAName,
              data: dataA,
              borderColor: '#38bdf8',
              backgroundColor: fillGradA,
              borderWidth: 2.5,
              pointBackgroundColor: '#38bdf8',
              pointBorderColor: '#ffffff',
              pointHoverBackgroundColor: '#ffffff',
              pointHoverBorderColor: '#38bdf8',
              pointRadius: 4,
              pointHoverRadius: 6
            },
            {
              label: modelBName,
              data: dataB,
              borderColor: '#a855f7',
              backgroundColor: fillGradB,
              borderWidth: 2.5,
              pointBackgroundColor: '#a855f7',
              pointBorderColor: '#ffffff',
              pointHoverBackgroundColor: '#ffffff',
              pointHoverBorderColor: '#a855f7',
              pointRadius: 4,
              pointHoverRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                color: '#f4f4f5',
                font: { family: 'Plus Jakarta Sans', size: 12, weight: '700' },
                padding: 10,
                usePointStyle: true
              }
            },
            tooltip: {
              backgroundColor: '#18181b',
              titleFont: { family: 'Outfit', size: 12, weight: '700' },
              bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
              borderColor: '#27272a',
              borderWidth: 1,
              padding: 10,
              cornerRadius: 8,
              callbacks: {
                label: function(context) {
                  return ` ${context.dataset.label}: ${context.raw} / 10`
                }
              }
            }
          },
          scales: {
            r: {
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
              pointLabels: {
                color: '#a1a1aa',
                font: { family: 'Plus Jakarta Sans', size: 10, weight: '600' }
              },
              ticks: {
                backdropColor: 'transparent',
                color: 'rgba(255, 255, 255, 0.3)',
                font: { size: 9 },
                stepSize: 2,
                min: 0,
                max: 10
              }
            }
          }
        }
      })
    }

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy()
        chartInstanceRef.current = null
      }
    }
  }, [evaluation, modelAName, modelBName, mode])

  return (
    <div className="evaluation-chart-container">
      <canvas ref={canvasRef} />
    </div>
  )
}
