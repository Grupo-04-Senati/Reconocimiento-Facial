import React, { useCallback, useRef, useState } from 'react'
import Webcam from 'react-webcam'
import { Camera, RotateCcw } from 'lucide-react'

interface CameraCaptureProps {
  onCapture: (imageSrc: string) => void
  disabled?: boolean
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, disabled = false }) => {
  const webcamRef = useRef<Webcam>(null)
  const [capturing, setCapturing] = useState(false)
  const [hasCapture, setHasCapture] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)

  const capture = useCallback(() => {
    if (!webcamRef.current) return
    setCapturing(true)
    const imageSrc = webcamRef.current.getScreenshot()
    if (imageSrc) {
      setPreview(imageSrc)
      setHasCapture(true)
      onCapture(imageSrc)
    }
    setCapturing(false)
  }, [onCapture])

  const retake = useCallback(() => {
    setPreview(null)
    setHasCapture(false)
  }, [])

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative w-full max-w-md rounded-xl overflow-hidden border-2 border-gray-200 bg-black">
        {preview ? (
          <img src={preview} alt="Captura" className="w-full" />
        ) : (
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            screenshotQuality={0.8}
            videoConstraints={{
              width: 640,
              height: 480,
              facingMode: 'user',
            }}
            className="w-full"
          />
        )}
        {capturing && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <div className="text-white text-lg">Procesando...</div>
          </div>
        )}
      </div>

      <div className="flex gap-3">
        {hasCapture ? (
          <button
            onClick={retake}
            className="flex items-center gap-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            <RotateCcw size={18} />
            Volver a capturar
          </button>
        ) : (
          <button
            onClick={capture}
            disabled={disabled || capturing}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <Camera size={20} />
            Capturar rostro
          </button>
        )}
      </div>
    </div>
  )
}

export default CameraCapture
