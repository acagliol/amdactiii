import { useCallback, useEffect, useRef, useState } from "react";

export type SourceKind = "camera" | "video";
export type SourceStatus = "starting" | "live" | "unavailable" | "no-video" | "playing" | "paused" | "ended";

export interface CameraOption {
  deviceId: string;
  label: string;
}

/**
 * Where the station's frames come from: the live camera or a recorded video file.
 * Both play in the same <video> element, so capturing a frame and watching the
 * scene work the same way for either source. Browsers only allow the camera on
 * https:// or localhost.
 */
export function useVideoSource() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileUrlRef = useRef<string | null>(null);
  const kindRef = useRef<SourceKind>("camera");
  const [kind, setKind] = useState<SourceKind>("camera");
  const [cameras, setCameras] = useState<CameraOption[]>([]);
  const [cameraId, setCameraId] = useState("");
  const [status, setStatus] = useState<SourceStatus>("starting");
  const [message, setMessage] = useState<string | null>(null);
  const [videoName, setVideoName] = useState<string | null>(null);

  kindRef.current = kind;

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  // Live camera: start when camera mode is on, restart when another camera is picked.
  useEffect(() => {
    if (kind !== "camera") return;
    let cancelled = false;

    async function startCamera() {
      setStatus("starting");
      if (!navigator.mediaDevices?.getUserMedia) {
        setStatus("unavailable");
        setMessage("This browser has no camera support. Use a recorded video or a photo instead.");
        return;
      }
      try {
        const choice: MediaTrackConstraints = cameraId ? { deviceId: { exact: cameraId } } : { facingMode: "environment" };
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { ...choice, width: { ideal: 1280 }, height: { ideal: 960 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        const element = videoRef.current;
        if (element) {
          element.removeAttribute("src");
          element.srcObject = stream;
          await element.play().catch(() => undefined);
        }
        setStatus("live");
        setMessage(null);
        // Camera names are only readable after the user allowed camera access.
        const devices = await navigator.mediaDevices.enumerateDevices();
        setCameras(
          devices
            .filter((device) => device.kind === "videoinput")
            .map((device, index) => ({ deviceId: device.deviceId, label: device.label || `Camera ${index + 1}` })),
        );
      } catch {
        setStatus("unavailable");
        setMessage("No camera access. Allow the camera in the browser, or use a recorded video or photo instead.");
      }
    }

    startCamera();
    return () => {
      cancelled = true;
      stopCamera();
    };
  }, [kind, cameraId, stopCamera]);

  // Follow play / pause / end of a recorded video.
  useEffect(() => {
    const element = videoRef.current;
    if (!element) return;
    const onPlay = () => kindRef.current === "video" && setStatus("playing");
    const onPause = () => kindRef.current === "video" && !element.ended && setStatus("paused");
    const onEnded = () => kindRef.current === "video" && setStatus("ended");
    element.addEventListener("play", onPlay);
    element.addEventListener("pause", onPause);
    element.addEventListener("ended", onEnded);
    return () => {
      element.removeEventListener("play", onPlay);
      element.removeEventListener("pause", onPause);
      element.removeEventListener("ended", onEnded);
    };
  }, []);

  // Free the recorded video's memory when the station closes.
  useEffect(() => () => void (fileUrlRef.current && URL.revokeObjectURL(fileUrlRef.current)), []);

  const switchToCamera = useCallback(() => {
    videoRef.current?.pause();
    setVideoName(null);
    setKind("camera");
  }, []);

  const switchToVideo = useCallback(() => {
    stopCamera();
    setKind("video");
    setStatus("no-video");
    setMessage(null);
  }, [stopCamera]);

  const loadVideo = useCallback(
    (file: File) => {
      stopCamera();
      setKind("video");
      if (fileUrlRef.current) URL.revokeObjectURL(fileUrlRef.current);
      const url = URL.createObjectURL(file);
      fileUrlRef.current = url;
      setVideoName(file.name);
      const element = videoRef.current;
      if (!element) return;
      element.srcObject = null;
      element.src = url;
      element.play().catch(() => setStatus("paused"));
    },
    [stopCamera],
  );

  const pause = useCallback(() => videoRef.current?.pause(), []);

  const resume = useCallback(() => {
    const element = videoRef.current;
    if (element && kindRef.current === "video" && !element.ended) void element.play().catch(() => undefined);
  }, []);

  const togglePlay = useCallback(() => {
    const element = videoRef.current;
    if (!element) return;
    if (element.paused || element.ended) void element.play().catch(() => undefined);
    else element.pause();
  }, []);

  /** Freeze the current frame as a JPEG: exactly the photo that gets checked. */
  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    const element = videoRef.current;
    if (!element || !element.videoWidth) return null;
    const canvas = document.createElement("canvas");
    canvas.width = element.videoWidth;
    canvas.height = element.videoHeight;
    canvas.getContext("2d")?.drawImage(element, 0, 0);
    return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
  }, []);

  /** "0:12" for a recorded video, the clock time for the live camera (used in the check log). */
  const timeLabel = useCallback((): string => {
    const element = videoRef.current;
    if (kindRef.current === "video" && element) {
      const seconds = Math.floor(element.currentTime);
      return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    }
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }, []);

  return {
    videoRef,
    kind,
    status,
    message,
    cameras,
    cameraId,
    videoName,
    setCameraId,
    switchToCamera,
    switchToVideo,
    loadVideo,
    pause,
    resume,
    togglePlay,
    captureFrame,
    timeLabel,
  };
}

export type VideoSource = ReturnType<typeof useVideoSource>;
