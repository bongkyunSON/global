import React, { useState, useEffect } from 'react';
import { Video, Radio, Camera, RotateCcw, Image, Activity, Settings } from 'lucide-react';
import RtspStreamCard from './components/RtspStreamCard';
import RtmpStreamCard from './components/RtmpStreamCard';
import CameraControlCard from './components/CameraControlCard';
import DeviceResetCard from './components/DeviceResetCard';
import ImageProcessCard from './components/ImageProcessCard';
import ProcessMonitorCard from './components/ProcessMonitorCard';
import Header from './components/Header';
import './styles/App.css';

function App() {
  const [activeTab, setActiveTab] = useState('rtsp');
  const [version, setVersion] = useState('1.0.0');

  useEffect(() => {
    // 버전 정보 로드
    fetch('/version.json')
      .then(response => response.json())
      .then(data => setVersion(data.version))
      .catch(error => console.log('Version loading failed:', error));
  }, []);

  const tabs = [
    { id: 'rtsp', label: 'RTSP 스트림', icon: Video },
    { id: 'rtmp', label: 'RTMP 송출', icon: Radio },
    { id: 'camera', label: '카메라 제어', icon: Camera },
    { id: 'reset', label: '장치 리셋', icon: RotateCcw },
    { id: 'image', label: '이미지 처리', icon: Image },
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
      case 'image':
        return <ImageProcessCard />;
      case 'monitor':
        return <ProcessMonitorCard />;
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