import { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

// 기본 API 훅
export const useApi = (apiFunction, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, dependencies);

  return { data, loading, error, execute };
};

// 자동 로드되는 API 훅
export const useApiLoad = (apiFunction, dependencies = []) => {
  const { data, loading, error, execute } = useApi(apiFunction, dependencies);

  useEffect(() => {
    execute();
  }, dependencies);

  return { data, loading, error, refetch: execute };
};

// RTSP 관련 훅들
export const useRtspStream = () => {
  return useApi(apiService.playRtspStream);
};

export const useRtspStop = () => {
  return useApi(apiService.stopRtspStream);
};

export const useRecording = () => {
  return useApi(apiService.startRecording);
};

export const useRecordingStop = () => {
  return useApi(apiService.stopRecording);
};

export const useRecordingStatus = () => {
  return useApiLoad(apiService.getRecordingStatus);
};

// RTMP 관련 훅들
export const useRtmpStream = () => {
  return useApi(apiService.startRtmpStream);
};

export const useRtmpStop = () => {
  return useApi(apiService.stopRtmpStream);
};

// 카메라 관련 훅들
export const useCameraControl = () => {
  return useApi(apiService.controlCamera);
};

export const useCameraStatus = (cameraName) => {
  return useApiLoad(
    () => apiService.getCameraStatus(cameraName),
    [cameraName]
  );
};

// 장치 리셋 훅
export const useDeviceReset = () => {
  return useApi(apiService.resetDevice);
};

// 프로세스 관리 훅들
export const useProcesses = () => {
  return useApiLoad(apiService.getProcesses);
};

export const useProcessStop = () => {
  return useApi(apiService.stopProcess);
};

// 이미지 처리 훅
export const useImageProcess = () => {
  return useApi(apiService.processImage);
};

// 이미지 크기 조정만
export const useImageResize = () => {
  return useApi(apiService.resizeImageOnly);
};

// OCR만
export const useImageOcr = () => {
  return useApi(apiService.ocrImageOnly);
};

// 포스터 분석만
export const usePosterAnalyze = () => {
  return useApi(apiService.analyzePoster);
};

// 포스터 OCR + 분석
export const usePosterExtractWithOcr = () => {
  return useApi(apiService.extractPosterWithOcr);
};

// 서버 정보 훅들
export const useServers = () => {
  return useApiLoad(apiService.getServers);
};

export const useLocations = () => {
  return useApiLoad(apiService.getLocations);
};

export const useLocationMapping = () => {
  return useApiLoad(apiService.getLocationMapping);
};

export const useCameras = () => {
  return useApiLoad(apiService.getCameras);
};

export const useResetIps = () => {
  return useApiLoad(apiService.getResetIps);
}; 