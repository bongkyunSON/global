import React, { useState, useEffect } from 'react';
import { Video, Radio, Camera, RotateCcw, Image, Activity, Settings, History } from 'lucide-react';
import RtspStreamCard from './components/RtspStreamCard';
import RtmpStreamCard from './components/RtmpStreamCard';
import CameraControlCard from './components/CameraControlCard';
import DeviceResetCard from './components/DeviceResetCard';
import ImageAnalysisCard from './components/ImageAnalysisCard';
import ProcessMonitorCard from './components/ProcessMonitorCard';
import AnalysisHistoryCard from './components/AnalysisHistoryCard';
import Header from './components/Header';
import './styles/App.css';

function App() {
  const [activeTab, setActiveTab] = useState('rtsp');
  const [version, setVersion] = useState('1.0.0');

  useEffect(() => {
    // 버전 정보 로드 (캐시 버스팅 및 캐시 무효화)
    const timestamp = Date.now();
    console.log('버전 정보 로딩 시작...', timestamp);
    
    fetch(`/version.json?t=${timestamp}`, {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    })
      .then(response => {
        console.log('버전 응답 상태:', response.status, response.statusText);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('버전 데이터 로드 성공:', data);
        setVersion(data.version || '2.0.0');
      })
      .catch(error => {
        console.error('버전 로딩 실패:', error);
        // fallback으로 2.0.0 설정
        setVersion('2.0.0');
      });
  }, []);

  const tabs = [
    { id: 'rtsp', label: 'RTSP 스트림', icon: Video },
    { id: 'rtmp', label: 'RTMP 송출', icon: Radio },
    { id: 'camera', label: '카메라 제어', icon: Camera },
    { id: 'reset', label: '장치 리셋', icon: RotateCcw },
    { id: 'analysis', label: 'AI 포스터 분석', icon: Image },
    { id: 'history', label: '분석 히스토리', icon: History },
    { id: 'monitor', label: '프로세스 모니터', icon: Activity },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'rtsp':
        return <RtspStreamCard />;
      case 'rtmp':
        return <RtmpStreamCard />;
      case 'camera':
        return <CameraControlCard />;
      case 'reset':
        return <DeviceResetCard />;
      case 'analysis':
        return <ImageAnalysisCard />;
      case 'monitor':
        return <ProcessMonitorCard />;
      case 'history':
        return <AnalysisHistoryCard />;
      default:
        return <RtspStreamCard />;
    }
  };

  return (
    <div className="app">
      <Header version={version} />
      
      <div className="app-container">
        <nav className="sidebar">
          <div className="sidebar-content">
            <div className="sidebar-header">
              <Settings className="sidebar-icon" />
              <h2>기능 메뉴</h2>
            </div>
            
            <div className="nav-tabs">
              {tabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    <Icon size={20} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </nav>

        <main className="main-content">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App; 