import axios from 'axios';

const API_BASE_URL = '/api';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터 추가
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API 함수들
export const apiService = {
  // 서버 정보
  async getServers() {
    const response = await api.get('/servers');
    return response.data;
  },

  async getLocations() {
    const response = await api.get('/locations');
    return response.data;
  },

  async getLocationMapping() {
    const response = await api.get('/location_mapping');
    return response.data;
  },

  // RTSP 관련
  async playRtspStream(data) {
    const response = await api.post('/rtsp/play', data);
    return response.data;
  },

  async stopRtspStream() {
    const response = await api.post('/rtsp/stop');
    return response.data;
  },

  async startRecording(data) {
    const response = await api.post('/rtsp/record', data);
    return response.data;
  },

  async stopRecording() {
    const response = await api.post('/rtsp/record/stop');
    return response.data;
  },

  async getRecordingStatus() {
    const response = await api.get('/rtsp/record/status');
    return response.data;
  },

  // RTMP 관련
  async startRtmpStream(data) {
    const response = await api.post('/rtmp/stream', data);
    return response.data;
  },

  async stopRtmpStream() {
    const response = await api.post('/rtmp/stop');
    return response.data;
  },

  // 카메라 관련
  async getCameras() {
    const response = await api.get('/cameras');
    return response.data;
  },

  async controlCamera(data) {
    const response = await api.post('/camera/control', data);
    return response.data;
  },

  async getCameraStatus(name) {
    const response = await api.get(`/camera/status?name=${encodeURIComponent(name)}`);
    return response.data;
  },

  // 장치 리셋
  async getResetIps() {
    const response = await api.get('/reset_ips');
    return response.data;
  },

  async resetDevice(data) {
    const response = await api.post('/device/reset', data);
    return response.data;
  },

  // 프로세스 관리
  async getProcesses() {
    const response = await api.get('/processes');
    return response.data;
  },

  async stopProcess(pid) {
    const response = await api.post(`/process/${pid}/stop`);
    return response.data;
  },

  // 이미지 처리
  async processImage(formData) {
    const response = await api.post('/image/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 이미지 크기 조정만
  async resizeImageOnly(formData) {
    const response = await api.post('/image/resize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // OCR만
  async ocrImageOnly(formData) {
    const response = await api.post('/image/ocr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 포스터 분석 (구조화된 정보 추출)
  async analyzePoster(formData) {
    const response = await api.post('/poster/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 포스터 OCR + 분석 (텍스트와 구조화된 정보 함께 추출)
  async extractPosterWithOcr(formData) {
    const response = await api.post('/poster/extract-with-ocr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default apiService; 