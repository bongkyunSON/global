import React, { useState } from 'react';
import { Radio, Square, Youtube } from 'lucide-react';
import { useServers, useLocations, useRtmpStream, useRtmpStop } from '../hooks/useApi';

const RtmpStreamCard = () => {
  const [location, setLocation] = useState('');
  const [server, setServer] = useState('');
  const [streamKey, setStreamKey] = useState('');
  const [bitrate, setBitrate] = useState(3000);
  
  const { data: servers } = useServers();
  const { data: locations } = useLocations();
  
  const { loading: streamLoading, execute: startStream } = useRtmpStream();
  const { loading: stopLoading, execute: stopStream } = useRtmpStop();

  const handleStart = async () => {
    if (!location || !server || !streamKey) {
      alert('모든 필드를 입력해주세요.');
      return;
    }

    try {
      await startStream({
        location,
        ip: server,
        stream_key: streamKey,
        bitrate: parseInt(bitrate)
      });
      alert('RTMP 송출이 시작되었습니다.');
    } catch (error) {
      alert(`RTMP 송출 시작 실패: ${error.message}`);
    }
  };

  const handleStop = async () => {
    try {
      await stopStream();
      alert('RTMP 송출이 중지되었습니다.');
    } catch (error) {
      alert(`RTMP 송출 중지 실패: ${error.message}`);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Radio size={20} />
          RTMP 실시간 송출
        </h3>
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
            <label className="form-label">
              <Youtube size={16} style={{ display: 'inline', marginRight: '4px' }} />
              YouTube 스트림 키
            </label>
            <input
              type="password"
              className="input"
              value={streamKey}
              onChange={(e) => setStreamKey(e.target.value)}
              placeholder="YouTube Live 스트림 키를 입력하세요"
            />
            <small style={{ color: 'var(--gray-500)', fontSize: '12px' }}>
              YouTube Studio → 라이브 → 스트림 키 복사
            </small>
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
              YouTube 권장: 4500-9000 Kbps
            </small>
          </div>
        </div>

        <div className="flex gap-4" style={{ marginTop: 'var(--spacing-lg)' }}>
          <button
            className="btn btn-primary"
            onClick={handleStart}
            disabled={streamLoading || !location || !server || !streamKey}
          >
            <Radio size={16} />
            {streamLoading ? '송출 시작 중...' : '송출 시작'}
          </button>
          
          <button
            className="btn btn-danger"
            onClick={handleStop}
            disabled={stopLoading}
          >
            <Square size={16} />
            {stopLoading ? '중지 중...' : '송출 중지'}
          </button>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--warning-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--warning-700)' }}>
            📡 RTMP 송출 안내
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--warning-600)' }}>
            <li>YouTube Live 방송을 위해서는 스트림 키가 필요합니다</li>
            <li>송출 전에 YouTube Studio에서 라이브 스트리밍을 설정하세요</li>
            <li>안정적인 네트워크 연결이 필요합니다 (업로드 속도 &gt; 비트레이트 × 1.5)</li>
            <li>송출 중에는 프로세스가 백그라운드에서 실행됩니다</li>
          </ul>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)', backgroundColor: 'var(--success-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--success-700)' }}>
            💡 비트레이트 가이드
          </h4>
          <div style={{ fontSize: '13px', color: 'var(--success-600)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--spacing-sm)' }}>
              <div>• 1080p: 4500-9000 Kbps</div>
              <div>• 720p: 2500-5000 Kbps</div>
              <div>• 480p: 1000-3000 Kbps</div>
              <div>• 모바일: 1000-2500 Kbps</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RtmpStreamCard; 