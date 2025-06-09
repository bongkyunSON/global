import React, { useState } from 'react';
import { Camera, Power, PowerOff } from 'lucide-react';
import { useLocationMapping, useCameraControl } from '../hooks/useApi';

const CameraControlCard = () => {
  const [selectedCamera, setSelectedCamera] = useState('');
  
  const { data: locationMapping } = useLocationMapping();
  const { loading, execute: controlCamera } = useCameraControl();

  const handlePowerControl = async (powerOn) => {
    if (!selectedCamera) {
      alert('카메라를 선택해주세요.');
      return;
    }

    try {
      await controlCamera({
        camera_name: selectedCamera,
        power_on: powerOn
      });
      alert(`카메라가 ${powerOn ? '켜졌' : '꺼졌'}습니다.`);
    } catch (error) {
      alert(`카메라 제어 실패: ${error.message}`);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Camera size={20} />
          카메라 전원 제어
        </h3>
      </div>
      
      <div className="card-content">
        <div className="form-group">
          <label className="form-label">제어할 카메라 선택</label>
          <select 
            className="select"
            value={selectedCamera}
            onChange={(e) => setSelectedCamera(e.target.value)}
          >
            <option value="">카메라 선택</option>
            {locationMapping && Object.entries(locationMapping).map(([code, displayName]) => (
              <option key={code} value={displayName}>{displayName}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-4" style={{ marginTop: 'var(--spacing-lg)' }}>
          <button
            className="btn btn-success"
            onClick={() => handlePowerControl(true)}
            disabled={loading || !selectedCamera}
          >
            <Power size={16} />
            {loading ? '제어 중...' : '전원 켜기'}
          </button>
          
          <button
            className="btn btn-danger"
            onClick={() => handlePowerControl(false)}
            disabled={loading || !selectedCamera}
          >
            <PowerOff size={16} />
            {loading ? '제어 중...' : '전원 끄기'}
          </button>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--primary-700)' }}>
            🎥 카메라 제어 정보
          </h4>
          <div style={{ fontSize: '13px', color: 'var(--primary-600)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--spacing-xs)' }}>
              <div><strong>HTTP 제어:</strong> 1세, 2간, 3간, 4간, 6간, 7간, 9간, 10간, 11간</div>
              <div><strong>VISCA 제어:</strong> 1소, 2소, 2세, 3세, 5간, 8간</div>
            </div>
          </div>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)', backgroundColor: 'var(--warning-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--warning-700)' }}>
            ⚠️ 주의사항
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--warning-600)' }}>
            <li>카메라 전원을 끄면 해당 위치의 스트리밍이 중단됩니다</li>
            <li>전원을 켜고 나서 카메라가 완전히 부팅되기까지 1-2분 정도 소요됩니다</li>
            <li>네트워크 상태에 따라 제어 명령이 지연될 수 있습니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CameraControlCard; 