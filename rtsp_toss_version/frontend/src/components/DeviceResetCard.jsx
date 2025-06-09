import React, { useState } from 'react';
import { RotateCcw, AlertTriangle } from 'lucide-react';
import { useLocationMapping, useDeviceReset } from '../hooks/useApi';

const DeviceResetCard = () => {
  const [selectedLocation, setSelectedLocation] = useState('');
  const [showConfirm, setShowConfirm] = useState(false);
  
  const { data: locationMapping } = useLocationMapping();
  const { loading, execute: resetDevice } = useDeviceReset();

  const handleReset = async () => {
    if (!selectedLocation) {
      alert('위치를 선택해주세요.');
      return;
    }

    setShowConfirm(true);
  };

  const confirmReset = async () => {
    try {
      await resetDevice({
        location: selectedLocation
      });
      alert('장치 리셋이 완료되었습니다.');
      setShowConfirm(false);
    } catch (error) {
      alert(`장치 리셋 실패: ${error.message}`);
      setShowConfirm(false);
    }
  };

  const cancelReset = () => {
    setShowConfirm(false);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <RotateCcw size={20} />
          장치 리셋
        </h3>
      </div>
      
      <div className="card-content">
        <div className="form-group">
          <label className="form-label">리셋할 장치 위치</label>
          <select 
            className="select"
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
          >
            <option value="">위치 선택</option>
            {locationMapping && Object.entries(locationMapping).map(([code, displayName]) => (
              <option key={code} value={displayName}>{displayName}</option>
            ))}
          </select>
        </div>

        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          {!showConfirm ? (
            <button
              className="btn btn-warning"
              onClick={handleReset}
              disabled={loading || !selectedLocation}
            >
              <RotateCcw size={16} />
              장치 리셋
            </button>
          ) : (
            <div className="confirmation-dialog" style={{ 
              padding: 'var(--spacing-md)', 
              backgroundColor: 'var(--error-50)', 
              borderRadius: 'var(--border-radius)',
              border: '1px solid var(--error-200)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
                <AlertTriangle size={20} style={{ color: 'var(--error-600)' }} />
                <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: 'var(--error-700)' }}>
                  장치 리셋 확인
                </h4>
              </div>
              
              <p style={{ margin: '0 0 var(--spacing-md) 0', fontSize: '14px', color: 'var(--error-600)' }}>
                <strong>{selectedLocation}</strong> 장치를 리셋하시겠습니까?<br />
                이 작업은 장치를 재부팅하며, 진행 중인 모든 작업이 중단됩니다.
              </p>
              
              <div className="flex gap-2">
                <button
                  className="btn btn-danger"
                  onClick={confirmReset}
                  disabled={loading}
                >
                  {loading ? '리셋 중...' : '확인'}
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={cancelReset}
                  disabled={loading}
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--warning-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--warning-700)' }}>
            ⚠️ 장치 리셋 주의사항
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--warning-600)' }}>
            <li>장치 리셋은 해당 위치의 모든 네트워크 장비를 재부팅합니다</li>
            <li>진행 중인 스트리밍, 녹화 등의 작업이 모두 중단됩니다</li>
            <li>장치가 완전히 재시작되기까지 2-3분 정도 소요됩니다</li>
            <li>리셋 후 카메라와 스트리밍 서비스가 자동으로 재연결됩니다</li>
          </ul>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--primary-700)' }}>
            💡 언제 리셋을 사용하나요?
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--primary-600)' }}>
            <li>카메라 연결이 불안정하거나 응답하지 않을 때</li>
            <li>스트리밍 품질에 문제가 발생했을 때</li>
            <li>네트워크 장비에 오류가 발생했을 때</li>
            <li>일반적인 문제 해결 방법으로 해결되지 않을 때</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DeviceResetCard; 