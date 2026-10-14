import { useCallback, useEffect, useRef, useState } from "react";

export type CameraStatus = "starting" | "live" | "unavailable";

/**
 * Live camera preview for the workstation. `captureFrame` freezes the current
 * video frame as a JPEG, which is exactly the photo that gets checked.
 * Browsers only allow the camera on https:// or localhost.
 */
export function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState<CameraStatus>("starting");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelled = false;

    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setStatus("unavailable");
        setMessage("This browser has no camera support. Upload a photo instead.");
        return;
      }
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 960 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => undefined);
        }
        setStatus("live");
      } catch {
        setStatus("unavailable");
        setMessage("No camera access. Allow the camera in the browser, or upload a photo instead.");
      }
    }

    start();
    return () => {
      cancelled = true;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return null;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
  }, []);

  return { videoRef, status, message, captureFrame };
}
