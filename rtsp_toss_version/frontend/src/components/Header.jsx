import React from 'react';
import { Monitor, Wifi } from 'lucide-react';

const Header = ({ version }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <Monitor className="logo-icon" />
            <div className="logo-text">
              <h1>정책세미나실 모니터링 시스템</h1>
              <span className="version">v{version}</span>
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <div className="status-indicator success">
            <Wifi size={16} />
            <span>연결됨</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header; 