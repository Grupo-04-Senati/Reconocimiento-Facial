import { useRef, useCallback, useState, useEffect } from 'react';
import Webcam from 'react-webcam';
import { Camera, CameraOff, RotateCcw, Radio } from 'lucide-react';

interface CameraCaptureProps {
  onCapture: (photo: string) => void;
  disabled?: boolean;
  autoCapture?: boolean;
  autoCaptureInterval?: number;
}

export function CameraCapture({ onCapture, disabled, autoCapture = false, autoCaptureInterval = 3000 }: CameraCaptureProps) {
  const webcamRef = useRef<Webcam>(null);
  const [enabled, setEnabled] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const captureFrame = useCallback(() => {
    if (!webcamRef.current) return;
    const src = webcamRef.current.getScreenshot();
    if (src) {
      onCapture(src);
    }
  }, [onCapture]);

  const capture = useCallback(() => {
    if (!webcamRef.current) return;
    const src = webcamRef.current.getScreenshot();
    if (src) {
      setPreview(src);
      onCapture(src);
    }
  }, [onCapture]);

  useEffect(() => {
    if (autoCapture && enabled && !disabled) {
      intervalRef.current = setInterval(() => {
        captureFrame();
      }, autoCaptureInterval);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoCapture, enabled, disabled, autoCaptureInterval, captureFrame]);

  const retake = () => {
    setPreview(null);
  };

  return (
    <div className="camera-capture">
      <div className="camera-viewport">
        {enabled ? (
          preview && !autoCapture ? (
            <img src={preview} alt="Captura" className="camera-preview" />
          ) : (
            <Webcam ref={webcamRef} screenshotFormat="image/jpeg" screenshotQuality={0.85} className="camera-feed" mirrored />
          )
        ) : (
          <div className="camera-off-state">
            <CameraOff size={48} />
            <p>Camara desactivada</p>
          </div>
        )}
        {enabled && (!preview || autoCapture) && (
          <div className="camera-overlay">
            <div className="camera-frame" />
          </div>
        )}
        {enabled && autoCapture && (
          <div className="absolute top-3 left-3 flex items-center gap-2 bg-red-600 text-white text-xs font-bold px-3 py-1.5 rounded-full animate-pulse z-10">
            <Radio size={12} />
            EN VIVO
          </div>
        )}
      </div>
      <div className="camera-controls">
        <button className="cam-btn" onClick={() => { setEnabled(!enabled); setPreview(null); }} disabled={disabled}>
          {enabled ? <CameraOff size={18} /> : <Camera size={18} />}
          {enabled ? 'Desactivar' : 'Activar Camara'}
        </button>
        {enabled && !autoCapture && !preview && (
          <button className="cam-btn primary" onClick={capture} disabled={disabled}>
            <Camera size={18} /> Capturar
          </button>
        )}
        {preview && !autoCapture && (
          <button className="cam-btn" onClick={retake}>
            <RotateCcw size={18} /> Volver a capturar
          </button>
        )}
      </div>
    </div>
  );
}
