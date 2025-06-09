import React, { useState } from 'react';
import { Play, Square, VideoIcon, CircleDot } from 'lucide-react';
import { useServers, useLocations, useRtspStream, useRtspStop, useRecording, useRecordingStop, useRecordingStatus } from '../hooks/useApi';

const RtspStreamCard = () => {
  const [location, setLocation] = useState('');
  const [server, setServer] = useState('');
  const [bitrate, setBitrate] = useState(3000);
  
  const { data: servers } = useServers();
  const { data: locations } = useLocations();
  const { data: recordingStatus, refetch: refetchRecordingStatus } = useRecordingStatus();
  
  const { loading: playLoading, execute: playStream } = useRtspStream();
  const { loading: stopLoading, execute: stopStream } = useRtspStop();
  const { loading: recordLoading, execute: startRecording } = useRecording();
  const { loading: stopRecordLoading, execute: stopRecording } = useRecordingStop();

  const handlePlay = async () => {
    if (!location || !server) {
      alert('위치와 서버를 선택해주세요.');
      return;
    }

    try {
      await playStream({
        location,
        ip: server,
        bitrate: parseInt(bitrate)
      });
      alert('RTSP 스트림이 시작되었습니다.');
    } catch (error) {
      alert(`스트림 시작 실패: ${error.message}`);
    }
  };

  const handleStop = async () => {
    try {
      await stopStream();
      alert('모든 RTSP 스트림이 중지되었습니다.');
    } catch (error) {
      alert(`스트림 중지 실패: ${error.message}`);
    }
  };

  const handleRecord = async () => {
    if (!location || !server) {
      alert('위치와 서버를 선택해주세요.');
      return;
    }

    try {
      await startRecording({
        location,
        ip: server,
        bitrate: parseInt(bitrate)
      });
      alert('녹화가 시작되었습니다.');
      refetchRecordingStatus();
    } catch (error) {
      alert(`녹화 시작 실패: ${error.message}`);
    }
  };

  const handleStopRecord = async () => {
    try {
      await stopRecording();
      alert('녹화가 중지되었습니다.');
      refetchRecordingStatus();
    } catch (error) {
      alert(`녹화 중지 실패: ${error.message}`);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <VideoIcon size={20} />
          RTSP 스트림 재생 및 녹화
        </h3>
        {recordingStatus?.is_recording && (
          <div className="status-indicator error">
            <CircleDot size={16} />
            <span>녹화 중</span>
          </div>
        )}
      </div>
      
      <div className="card-content">
        <div className="grid grid-cols-2">
          <div className="form-group">
            <label className="form-label">스트림 위치</label>
            <select 
              className="select"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            >
              <option value="">위치 선택</option>
              {locations?.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">RTSP 서버</label>
            <select 
              className="select"
              value={server}
              onChange={(e) => setServer(e.target.value)}
            >
              <option value="">서버 선택</option>
              {servers && Object.entries(servers).map(([ip, name]) => (
                <option key={ip} value={ip}>{name} ({ip})</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">비트레이트 (Kbps)</label>
            <input
              type="number"
              className="input"
              value={bitrate}
              onChange={(e) => setBitrate(e.target.value)}
              min="1000"
              max="10000"
              step="500"
            />
            <small style={{ color: 'var(--gray-500)', fontSize: '12px' }}>
              권장: 3000-5000 Kbps
            </small>
          </div>
        </div>

        <div className="grid grid-cols-2" style={{ marginTop: 'var(--spacing-lg)' }}>
          <div>
            <h4 style={{ marginBottom: 'var(--spacing-md)', fontSize: '16px', fontWeight: '600' }}>
              스트림 재생
            </h4>
            <div className="flex gap-2">
              <button
                className="btn btn-primary"
                onClick={handlePlay}
                disabled={playLoading || !location || !server}
              >
                <Play size={16} />
                {playLoading ? '시작 중...' : '재생 시작'}
              </button>
              
              <button
                className="btn btn-danger"
                onClick={handleStop}
                disabled={stopLoading}
              >
                <Square size={16} />
                {stopLoading ? '중지 중...' : '재생 중지'}
              </button>
            </div>
          </div>

          <div>
            <h4 style={{ marginBottom: 'var(--spacing-md)', fontSize: '16px', fontWeight: '600' }}>
              스트림 녹화
            </h4>
            <div className="flex gap-2">
              <button
                className="btn btn-success"
                onClick={handleRecord}
                disabled={recordLoading || recordingStatus?.is_recording || !location || !server}
              >
                <CircleDot size={16} />
                {recordLoading ? '시작 중...' : '녹화 시작'}
              </button>
              
              <button
                className="btn btn-warning"
                onClick={handleStopRecord}
                disabled={stopRecordLoading || !recordingStatus?.is_recording}
              >
                <Square size={16} />
                {stopRecordLoading ? '중지 중...' : '녹화 중지'}
              </button>
            </div>
          </div>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--primary-700)' }}>
            📝 사용 안내
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--primary-600)' }}>
            <li>재생 시 MPV 또는 FFplay 플레이어가 자동으로 실행됩니다</li>
            <li>녹화 파일은 ~/Desktop/rtsp_recordings/ 폴더에 저장됩니다</li>
            <li>비트레이트가 높을수록 화질이 좋지만 더 많은 대역폭을 사용합니다</li>
            <li>녹화 중에는 모니터링 창이 함께 표시됩니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RtspStreamCard; 