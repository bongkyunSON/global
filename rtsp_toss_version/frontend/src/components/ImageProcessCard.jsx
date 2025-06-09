import React, { useState, useEffect } from 'react';
import { Image, Upload, Download, Eye, Key, Trash2, Scissors, FileSearch } from 'lucide-react';
import { useImageProcess, useImageResize, useImageOcr } from '../hooks/useApi';

const ImageProcessCard = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [width, setWidth] = useState(400);
  const [processResult, setProcessResult] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [savedApiKeys, setSavedApiKeys] = useState([]);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  
  const { loading: loadingProcess, execute: processImage } = useImageProcess();
  const { loading: loadingResize, execute: resizeImage } = useImageResize();
  const { loading: loadingOcr, execute: ocrImage } = useImageOcr();

  // 로컬스토리지에서 저장된 API 키들 불러오기
  useEffect(() => {
    const keys = JSON.parse(localStorage.getItem('ocrApiKeys') || '[]');
    setSavedApiKeys(keys);
    if (keys.length > 0) {
      setApiKey(keys[0]); // 첫 번째 저장된 키를 기본값으로 설정
    }
  }, []);

  // API 키 저장하기
  const saveApiKey = () => {
    if (!apiKey.trim()) {
      alert('API 키를 입력해주세요.');
      return;
    }

    // 중복 확인
    if (savedApiKeys.includes(apiKey.trim())) {
      alert('이미 저장된 API 키입니다.');
      return;
    }

    const newKeys = [apiKey.trim(), ...savedApiKeys].slice(0, 5); // 최대 5개까지 저장
    setSavedApiKeys(newKeys);
    localStorage.setItem('ocrApiKeys', JSON.stringify(newKeys));
    setShowApiKeyInput(false);
    alert('API 키가 저장되었습니다.');
  };

  // API 키 삭제하기
  const deleteApiKey = (keyToDelete) => {
    const newKeys = savedApiKeys.filter(key => key !== keyToDelete);
    setSavedApiKeys(newKeys);
    localStorage.setItem('ocrApiKeys', JSON.stringify(newKeys));
    
    // 현재 선택된 키가 삭제되었다면 첫 번째 키로 변경
    if (apiKey === keyToDelete) {
      setApiKey(newKeys.length > 0 ? newKeys[0] : '');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('이미지 파일만 업로드 가능합니다.');
        return;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB
        alert('파일 크기는 10MB 이하여야 합니다.');
        return;
      }
      setSelectedFile(file);
      setProcessResult(null);
    }
  };

  const handleProcess = async () => {
    if (!selectedFile) {
      alert('처리할 이미지 파일을 선택해주세요.');
      return;
    }

    if (!apiKey.trim()) {
      alert('OCR API 키를 입력해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('width', width.toString());
    formData.append('api_key', apiKey.trim());

    try {
      const result = await processImage(formData);
      setProcessResult(result);
    } catch (error) {
      alert(`이미지 처리 실패: ${error.message}`);
    }
  };

  const handleResizeOnly = async () => {
    if (!selectedFile) {
      alert('처리할 이미지 파일을 선택해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('width', width.toString());

    try {
      const result = await resizeImage(formData);
      setProcessResult(result);
    } catch (error) {
      alert(`이미지 크기 조정 실패: ${error.message}`);
    }
  };

  const handleOcrOnly = async () => {
    if (!selectedFile) {
      alert('처리할 이미지 파일을 선택해주세요.');
      return;
    }

    if (!apiKey.trim()) {
      alert('OCR API 키를 입력해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('api_key', apiKey.trim());

    try {
      const result = await ocrImage(formData);
      setProcessResult(result);
    } catch (error) {
      alert(`OCR 처리 실패: ${error.message}`);
    }
  };

  const downloadResult = () => {
    if (processResult?.resized_image) {
      const link = document.createElement('a');
      link.href = `data:image/jpeg;base64,${processResult.resized_image}`;
      link.download = `processed_${selectedFile.name}`;
      link.click();
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Image size={20} />
          이미지 크기 조정 및 OCR
        </h3>
      </div>
      
      <div className="card-content">
        {/* API 키 설정 섹션 */}
        <div className="form-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <label className="form-label">
            <Key size={16} style={{ display: 'inline', marginRight: '4px' }} />
            OCR API 키
          </label>
          
          {savedApiKeys.length > 0 && (
            <div style={{ marginBottom: 'var(--spacing-sm)' }}>
              <select 
                className="input"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                style={{ marginBottom: 'var(--spacing-xs)' }}
              >
                <option value="">API 키 선택...</option>
                {savedApiKeys.map((key, index) => (
                  <option key={index} value={key}>
                    {key.substring(0, 10)}...{key.substring(key.length - 4)} {index === 0 ? '(기본)' : ''}
                  </option>
                ))}
              </select>
              
              <div style={{ display: 'flex', gap: 'var(--spacing-xs)', flexWrap: 'wrap' }}>
                {savedApiKeys.map((key, index) => (
                  <div key={index} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '4px',
                    padding: '2px 6px',
                    backgroundColor: key === apiKey ? 'var(--primary-100)' : 'var(--gray-100)',
                    borderRadius: '4px',
                    fontSize: '11px',
                    border: key === apiKey ? '1px solid var(--primary-300)' : '1px solid var(--gray-200)'
                  }}>
                    <span 
                      onClick={() => setApiKey(key)}
                      style={{ cursor: 'pointer', color: key === apiKey ? 'var(--primary-700)' : 'var(--gray-600)' }}
                    >
                      {key.substring(0, 8)}...
                    </span>
                    <Trash2 
                      size={12} 
                      style={{ cursor: 'pointer', color: 'var(--danger-500)' }}
                      onClick={() => deleteApiKey(key)}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {showApiKeyInput ? (
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)', alignItems: 'end' }}>
              <div style={{ flex: 1 }}>
                <input
                  type="text"
                  className="input"
                  placeholder="Upstage API 키를 입력하세요..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>
              <button className="btn btn-primary" onClick={saveApiKey}>저장</button>
              <button 
                className="btn btn-secondary" 
                onClick={() => setShowApiKeyInput(false)}
              >
                취소
              </button>
            </div>
          ) : (
            <button 
              className="btn btn-secondary"
              onClick={() => setShowApiKeyInput(true)}
              style={{ fontSize: '12px', padding: '4px 8px' }}
            >
              <Key size={14} />
              새 API 키 추가
            </button>
          )}
          
          <small style={{ color: 'var(--gray-500)', fontSize: '11px', display: 'block', marginTop: '4px' }}>
            Upstage OCR API 키가 필요합니다. 저장된 키는 브라우저에 안전하게 보관됩니다.
          </small>
        </div>

        <div className="grid grid-cols-2">
          <div className="form-group">
            <label className="form-label">이미지 파일</label>
            <input
              type="file"
              className="input"
              accept="image/*"
              onChange={handleFileChange}
            />
            {selectedFile && (
              <small style={{ color: 'var(--success-600)', fontSize: '12px' }}>
                선택된 파일: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </small>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">출력 너비 (px)</label>
            <input
              type="number"
              className="input"
              value={width}
              onChange={(e) => setWidth(parseInt(e.target.value) || 400)}
              min="100"
              max="2000"
              step="50"
            />
            <small style={{ color: 'var(--gray-500)', fontSize: '12px' }}>
              권장: 400-800px
            </small>
          </div>
        </div>

        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          <button
            className="btn btn-primary"
            onClick={handleProcess}
            disabled={loadingProcess || !selectedFile || !apiKey.trim()}
            style={{ marginRight: 'var(--spacing-sm)' }}
          >
            <Upload size={16} />
            {loadingProcess ? '처리 중...' : '전체 처리 (크기조정 + OCR)'}
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={handleResizeOnly}
            disabled={loadingResize || !selectedFile}
            style={{ marginRight: 'var(--spacing-sm)' }}
          >
            <Scissors size={16} />
            {loadingResize ? '처리 중...' : '크기 조정만'}
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={handleOcrOnly}
            disabled={loadingOcr || !selectedFile || !apiKey.trim()}
          >
            <FileSearch size={16} />
            {loadingOcr ? '처리 중...' : 'OCR만'}
          </button>
          
          {!apiKey.trim() && (
            <div style={{ marginTop: 'var(--spacing-sm)' }}>
              <small style={{ color: 'var(--danger-500)', fontSize: '12px' }}>
                OCR 기능을 사용하려면 API 키가 필요합니다
              </small>
            </div>
          )}
        </div>

        {processResult && (
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <h4 style={{ marginBottom: 'var(--spacing-md)', fontSize: '16px', fontWeight: '600' }}>
              처리 결과
            </h4>
            
            <div className="grid grid-cols-1" style={{ gap: 'var(--spacing-md)' }}>
              {processResult.resized_image && (
                <div>
                  <div className="flex justify-between items-center" style={{ marginBottom: 'var(--spacing-sm)' }}>
                    <h5 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>처리된 이미지</h5>
                    <button
                      className="btn btn-secondary"
                      onClick={downloadResult}
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      <Download size={14} />
                      다운로드
                    </button>
                  </div>
                  <div style={{ 
                    border: '1px solid var(--gray-200)', 
                    borderRadius: 'var(--border-radius)',
                    padding: 'var(--spacing-sm)',
                    backgroundColor: 'var(--gray-50)',
                    textAlign: 'center'
                  }}>
                    <img 
                      src={`data:image/jpeg;base64,${processResult.resized_image}`}
                      alt="Processed"
                      style={{ 
                        maxWidth: '100%', 
                        maxHeight: '300px',
                        borderRadius: 'var(--border-radius)'
                      }}
                    />
                  </div>
                </div>
              )}

              {processResult.ocr_text && (
                <div>
                  <h5 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600' }}>
                    <Eye size={14} style={{ display: 'inline', marginRight: '4px' }} />
                    OCR 텍스트 추출 결과
                  </h5>
                  <div style={{ 
                    border: '1px solid var(--gray-200)', 
                    borderRadius: 'var(--border-radius)',
                    padding: 'var(--spacing-md)',
                    backgroundColor: 'white',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                    maxHeight: '200px',
                    overflow: 'auto',
                    color: processResult.ocr_text.includes('오류') || processResult.ocr_text.includes('API 키가 필요합니다') ? 'var(--danger-600)' : 'inherit'
                  }}>
                    {processResult.ocr_text}
                  </div>
                </div>
              )}

              <div style={{ 
                padding: 'var(--spacing-sm)', 
                backgroundColor: 'var(--primary-50)', 
                borderRadius: 'var(--border-radius)',
                fontSize: '13px',
                color: 'var(--primary-600)'
              }}>
                <div><strong>파일명:</strong> {processResult.original_filename}</div>
                {processResult.width && processResult.height && (
                  <div><strong>처리 후 크기:</strong> {processResult.width} x {processResult.height} px</div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--primary-700)' }}>
            🖼️ 이미지 처리 기능
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--primary-600)' }}>
            <li><strong>전체 처리:</strong> 이미지 크기 조정 + OCR 텍스트 추출</li>
            <li><strong>크기 조정만:</strong> 이미지를 지정된 너비로 자동 조정 (비율 유지)</li>
            <li><strong>OCR만:</strong> 이미지 내 텍스트 추출 (Upstage API)</li>
            <li>JPEG, PNG 형식 지원</li>
            <li>처리된 이미지 다운로드 가능</li>
            <li>API 키는 로컬스토리지에 안전하게 저장</li>
          </ul>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)', backgroundColor: 'var(--warning-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--warning-700)' }}>
            📝 사용 팁
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--warning-600)' }}>
            <li>Upstage AI 계정에서 API 키를 발급받아 OCR 기능 사용</li>
            <li>크기 조정만 원한다면 API 키 없이도 사용 가능</li>
            <li>텍스트가 명확한 고화질 이미지일수록 OCR 정확도가 높습니다</li>
            <li>너무 작은 크기로 조정하면 텍스트 인식이 어려울 수 있습니다</li>
            <li>한글, 영문, 숫자 텍스트 인식을 지원합니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ImageProcessCard; 