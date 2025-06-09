import React, { useEffect } from 'react';
import { Activity, Square, RefreshCw } from 'lucide-react';
import { useProcesses, useProcessStop } from '../hooks/useApi';

const ProcessMonitorCard = () => {
  const { data: processes, loading, refetch } = useProcesses();
  const { loading: stopLoading, execute: stopProcess } = useProcessStop();

  useEffect(() => {
    // 3초마다 프로세스 목록 새로고침
    const interval = setInterval(() => {
      refetch();
    }, 3000);

    return () => clearInterval(interval);
  }, [refetch]);

  const handleStopProcess = async (pid) => {
    if (window.confirm(`프로세스 ${pid}를 종료하시겠습니까?`)) {
      try {
        await stopProcess(pid);
        alert(`프로세스 ${pid}가 종료되었습니다.`);
        refetch();
      } catch (error) {
        alert(`프로세스 종료 실패: ${error.message}`);
      }
    }
  };

  const getProcessTypeLabel = (type) => {
    switch (type) {
      case 'rtsp':
        return 'RTSP 재생';
      case 'rtmp':
        return 'RTMP 송출';
      case 'record':
        return '녹화';
      default:
        return type;
    }
  };

  const getProcessTypeColor = (type) => {
    switch (type) {
      case 'rtsp':
        return 'primary';
      case 'rtmp':
        return 'warning';
      case 'record':
        return 'error';
      default:
        return 'info';
    }
  };

  const getTotalProcessCount = () => {
    if (!processes) return 0;
    return (processes.rtsp?.length || 0) + 
           (processes.rtmp?.length || 0) + 
           (processes.record?.length || 0);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Activity size={20} />
          프로세스 모니터링
        </h3>
        <div className="flex items-center gap-2">
          <div className="status-indicator info">
            <span>실행 중: {getTotalProcessCount()}개</span>
          </div>
          <button
            className="btn btn-secondary"
            onClick={refetch}
            disabled={loading}
            style={{ padding: '4px 8px', fontSize: '12px' }}
          >
            <RefreshCw size={14} />
            새로고침
          </button>
        </div>
      </div>
      
      <div className="card-content">
        {loading && (
          <div className="text-center" style={{ padding: 'var(--spacing-lg)' }}>
            <div className="loading"></div>
            <p style={{ marginTop: 'var(--spacing-sm)', color: 'var(--gray-500)' }}>
              프로세스 정보를 불러오는 중...
            </p>
          </div>
        )}

        {!loading && getTotalProcessCount() === 0 && (
          <div className="text-center" style={{ padding: 'var(--spacing-lg)', color: 'var(--gray-500)' }}>
            <Activity size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.3 }} />
            <p>실행 중인 프로세스가 없습니다.</p>
            <p style={{ fontSize: '13px' }}>
              RTSP 재생, RTMP 송출, 녹화 작업을 시작하면 여기에 표시됩니다.
            </p>
          </div>
        )}

        {!loading && processes && (
          <div className="grid grid-cols-1" style={{ gap: 'var(--spacing-md)' }}>
            {/* RTSP 프로세스 */}
            {processes.rtsp && processes.rtsp.length > 0 && (
              <div>
                <h4 style={{ marginBottom: 'var(--spacing-sm)', fontSize: '16px', fontWeight: '600', color: 'var(--primary-700)' }}>
                  RTSP 스트림 재생 ({processes.rtsp.length}개)
                </h4>
                <div className="grid grid-cols-1" style={{ gap: 'var(--spacing-sm)' }}>
                  {processes.rtsp.map((process) => (
                    <div key={process.pid} className="process-item" style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: 'var(--spacing-sm) var(--spacing-md)',
                      border: '1px solid var(--primary-200)',
                      borderRadius: 'var(--border-radius)',
                      backgroundColor: 'var(--primary-50)'
                    }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                          <span className={`status-indicator ${getProcessTypeColor(process.type)}`}>
                            {getProcessTypeLabel(process.type)}
                          </span>
                          <span style={{ fontSize: '13px', color: 'var(--gray-600)' }}>
                            PID: {process.pid}
                          </span>
                        </div>
                      </div>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleStopProcess(process.pid)}
                        disabled={stopLoading}
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        <Square size={12} />
                        종료
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* RTMP 프로세스 */}
            {processes.rtmp && processes.rtmp.length > 0 && (
              <div>
                <h4 style={{ marginBottom: 'var(--spacing-sm)', fontSize: '16px', fontWeight: '600', color: 'var(--warning-700)' }}>
                  RTMP 송출 ({processes.rtmp.length}개)
                </h4>
                <div className="grid grid-cols-1" style={{ gap: 'var(--spacing-sm)' }}>
                  {processes.rtmp.map((process) => (
                    <div key={process.pid} className="process-item" style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: 'var(--spacing-sm) var(--spacing-md)',
                      border: '1px solid var(--warning-200)',
                      borderRadius: 'var(--border-radius)',
                      backgroundColor: 'var(--warning-50)'
                    }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                          <span className={`status-indicator ${getProcessTypeColor(process.type)}`}>
                            {getProcessTypeLabel(process.type)}
                          </span>
                          <span style={{ fontSize: '13px', color: 'var(--gray-600)' }}>
                            PID: {process.pid}
                          </span>
                        </div>
                      </div>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleStopProcess(process.pid)}
                        disabled={stopLoading}
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        <Square size={12} />
                        종료
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 녹화 프로세스 */}
            {processes.record && processes.record.length > 0 && (
              <div>
                <h4 style={{ marginBottom: 'var(--spacing-sm)', fontSize: '16px', fontWeight: '600', color: 'var(--error-700)' }}>
                  녹화 ({processes.record.length}개)
                </h4>
                <div className="grid grid-cols-1" style={{ gap: 'var(--spacing-sm)' }}>
                  {processes.record.map((process) => (
                    <div key={process.pid} className="process-item" style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: 'var(--spacing-sm) var(--spacing-md)',
                      border: '1px solid var(--error-200)',
                      borderRadius: 'var(--border-radius)',
                      backgroundColor: 'var(--error-50)'
                    }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                          <span className={`status-indicator ${getProcessTypeColor(process.type)}`}>
                            {getProcessTypeLabel(process.type)}
                          </span>
                          <span style={{ fontSize: '13px', color: 'var(--gray-600)' }}>
                            PID: {process.pid}
                          </span>
                        </div>
                      </div>
                      <button
                        className="btn btn-danger"
                        onClick={() => handleStopProcess(process.pid)}
                        disabled={stopLoading}
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        <Square size={12} />
                        종료
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--primary-700)' }}>
            📊 프로세스 모니터링
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--primary-600)' }}>
            <li>실행 중인 모든 스트리밍 관련 프로세스를 실시간으로 모니터링합니다</li>
            <li>각 프로세스는 고유한 PID(Process ID)로 구분됩니다</li>
            <li>프로세스 목록은 3초마다 자동으로 새로고침됩니다</li>
            <li>개별 프로세스를 선택적으로 종료할 수 있습니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ProcessMonitorCard; 