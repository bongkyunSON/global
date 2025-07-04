import React, { useState, useEffect } from 'react';
import { Image, Upload, Download, Eye, Key, Trash2, Scissors, FileSearch, Brain, BookOpen, Loader, Copy, Check } from 'lucide-react';
import { useImageProcess, useImageResize, useImageOcr, usePosterAnalyze, usePosterExtractWithOcr } from '../hooks/useApi';

const ImageAnalysisCard = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedFilePreview, setSelectedFilePreview] = useState(null);
  const [width, setWidth] = useState(400);
  const [processResult, setProcessResult] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [savedApiKeys, setSavedApiKeys] = useState([]);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [activeMode, setActiveMode] = useState('resize'); // 'resize', 'ocr', 'process', 'analyze', 'extract'
  const [copiedOcr, setCopiedOcr] = useState(false);
  const [copiedPoster, setCopiedPoster] = useState(false);
  
  const { loading: loadingProcess, execute: processImage } = useImageProcess();
  const { loading: loadingResize, execute: resizeImage } = useImageResize();
  const { loading: loadingOcr, execute: ocrImage } = useImageOcr();
  const { loading: loadingAnalyze, execute: analyzePoster } = usePosterAnalyze();
  const { loading: loadingExtract, execute: extractPosterWithOcr } = usePosterExtractWithOcr();

  // 로컬스토리지에서 저장된 API 키들 불러오기
  useEffect(() => {
    const keys = JSON.parse(localStorage.getItem('ocrApiKeys') || '[]');
    setSavedApiKeys(keys);
    if (keys.length > 0) {
      setApiKey(keys[0]); // 첫 번째 저장된 키를 기본값으로 설정
    }
    
    // 저장된 분석 상태 복원
    const savedState = localStorage.getItem('imageAnalysisState');
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        if (state.processResult) {
          setProcessResult(state.processResult);
        }
        if (state.activeMode) {
          setActiveMode(state.activeMode);
        }
        if (state.width) {
          setWidth(state.width);
        }
      } catch (error) {
        console.error('저장된 상태 복원 실패:', error);
      }
    }
  }, []);

  // 분석 결과를 로컬 스토리지에 저장
  useEffect(() => {
    if (processResult) {
      const stateToSave = {
        processResult,
        activeMode,
        width,
        timestamp: Date.now()
      };
      localStorage.setItem('imageAnalysisState', JSON.stringify(stateToSave));
    }
  }, [processResult, activeMode, width]);

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
      
      // 이전 미리보기 URL 정리
      if (selectedFilePreview) {
        URL.revokeObjectURL(selectedFilePreview);
      }
      
      // 새 미리보기 URL 생성
      const previewUrl = URL.createObjectURL(file);
      setSelectedFile(file);
      setSelectedFilePreview(previewUrl);
      setProcessResult(null);
    }
  };

  const handleExecute = async () => {
    if (!selectedFile) {
      alert('처리할 이미지 파일을 선택해주세요.');
      return;
    }

    const needsApiKey = ['ocr', 'process', 'analyze', 'extract'].includes(activeMode);
    if (needsApiKey && !apiKey.trim()) {
      alert('API 키를 입력해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    
    if (activeMode === 'resize' || activeMode === 'process') {
      formData.append('width', width.toString());
    }
    
    if (needsApiKey) {
      formData.append('api_key', apiKey.trim());
    }

    try {
      let result;
      
      if (activeMode === 'process') {
        // 전체 처리: 크기조정 + OCR + 포스터분석을 모두 수행
        // 1. 먼저 이미지 크기조정만 수행 (OCR 중복 방지)
        const resizeFormData = new FormData();
        resizeFormData.append('file', selectedFile);
        resizeFormData.append('width', width.toString());
        
        const resizeResult = await resizeImage(resizeFormData);
        
        // 2. OCR + 포스터 분석을 함께 수행
        const posterFormData = new FormData();
        posterFormData.append('file', selectedFile);
        posterFormData.append('api_key', apiKey.trim());
        
        const posterResult = await extractPosterWithOcr(posterFormData);
        
        // 3. 결과 통합
        result = {
          ...resizeResult,  // 크기조정 결과 (resized_image, width, height 등)
          ocr_text: posterResult.success ? posterResult.ocr_text : "OCR 처리 실패",
          poster_info: posterResult.success ? posterResult.poster_info : null,
          poster_analysis_success: posterResult.success,
          poster_error: posterResult.success ? null : posterResult.error
        };
      } else {
        // 기존 단일 모드 처리
        switch (activeMode) {
          case 'resize':
            result = await resizeImage(formData);
            break;
          case 'ocr':
            result = await ocrImage(formData);
            break;
          case 'analyze':
            result = await analyzePoster(formData);
            break;
          case 'extract':
            result = await extractPosterWithOcr(formData);
            break;
          default:
            throw new Error('알 수 없는 모드입니다.');
        }
      }
      
      setProcessResult(result);
      
      // 분석 완료 후 저장 상태 알림
      const hasOcrResult = result.ocr_text && (activeMode === 'ocr' || activeMode === 'process' || activeMode === 'extract');
      const hasAiResult = result.poster_info && (activeMode === 'analyze' || activeMode === 'process' || activeMode === 'extract');
      
      if (hasOcrResult || hasAiResult) {
        let saveMessage = '분석이 완료되어 자동으로 저장되었습니다!';
        if (hasOcrResult && hasAiResult) {
          saveMessage = 'OCR 텍스트와 AI 분석 결과가 모두 저장되었습니다!';
        } else if (hasOcrResult) {
          saveMessage = 'OCR 텍스트 결과가 저장되었습니다!';
        } else if (hasAiResult) {
          saveMessage = 'AI 분석 결과가 저장되었습니다!';
        }
        
        // 성공 알림 (비간섭적으로)
        setTimeout(() => {
          console.log(saveMessage);
          // 필요시 토스트 알림 등을 추가할 수 있음
        }, 500);
      }
      
    } catch (error) {
      alert(`처리 실패: ${error.message}`);
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

  const renderPosterInfo = (posterInfo) => {
    if (!posterInfo || typeof posterInfo !== 'object') {
      return <div className="text-gray-500">포스터 정보를 추출할 수 없습니다.</div>;
    }

    return (
      <div className="poster-info">
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: 'var(--spacing-md)' 
        }}>
          <h4 style={{ margin: 0, color: 'var(--primary-600)' }}>
            📋 추출된 포스터 정보
          </h4>
          <button
            onClick={() => copyToClipboard(formatPosterInfoForCopy(posterInfo), 'poster')}
            style={{
              padding: '4px 8px',
              backgroundColor: copiedPoster ? 'var(--success-500)' : 'var(--gray-100)',
              color: copiedPoster ? 'white' : 'var(--gray-600)',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'all 0.2s ease'
            }}
            title="포스터 분석 결과 복사"
          >
            {copiedPoster ? <Check size={12} /> : <Copy size={12} />}
            {copiedPoster ? '복사됨' : '복사'}
          </button>
        </div>
        <div className="info-grid" style={{ 
          display: 'grid', 
          gap: 'var(--spacing-sm)',
          fontSize: '14px'
        }}>
          {Object.entries(posterInfo).map(([key, value]) => (
            <div key={key} className="info-item" style={{
              padding: 'var(--spacing-sm)',
              backgroundColor: 'var(--gray-50)',
              borderRadius: '6px',
              border: '1px solid var(--gray-200)'
            }}>
              <div style={{ 
                fontWeight: '600', 
                color: 'var(--gray-700)',
                marginBottom: '4px'
              }}>
                {key}
              </div>
              <div style={{ color: 'var(--gray-600)' }}>
                {(() => {
                  try {
                    if (value === null || value === undefined) return '정보 없음';
                    if (typeof value === 'string') return value;
                    if (Array.isArray(value)) return value.join(', ');
                    if (typeof value === 'object') {
                      return Object.entries(value).map(([k, v]) => `${k}: ${String(v)}`).join(', ');
                    }
                    return String(value);
                  } catch (error) {
                    return '[렌더링 오류]';
                  }
                })()}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const isLoading = loadingProcess || loadingResize || loadingOcr || loadingAnalyze || loadingExtract;

  const modes = [
    { id: 'process', label: '전체 처리', icon: Upload, description: '크기 조정 + OCR + 포스터 분석 (모든 기능)', needsApiKey: true, isMain: true },
    { id: 'resize', label: '크기 조정만', icon: Scissors, description: '이미지를 지정된 너비로 자동 조정 (비율 유지)', needsApiKey: false },
    { id: 'ocr', label: 'OCR만', icon: FileSearch, description: '이미지 내 텍스트 추출', needsApiKey: true },
    { id: 'analyze', label: '포스터 분석', icon: Brain, description: '구조화된 정보만 추출', needsApiKey: true },
    { id: 'extract', label: 'OCR + 포스터 분석', icon: BookOpen, description: 'OCR 텍스트 + 구조화된 정보 추출', needsApiKey: true }
  ];

  const copyToClipboard = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text);
      
      if (type === 'ocr') {
        setCopiedOcr(true);
        setTimeout(() => setCopiedOcr(false), 2000);
      } else if (type === 'poster') {
        setCopiedPoster(true);
        setTimeout(() => setCopiedPoster(false), 2000);
      }
    } catch (err) {
      console.error('복사 실패:', err);
      // 대체 방법
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      
      if (type === 'ocr') {
        setCopiedOcr(true);
        setTimeout(() => setCopiedOcr(false), 2000);
      } else if (type === 'poster') {
        setCopiedPoster(true);
        setTimeout(() => setCopiedPoster(false), 2000);
      }
    }
  };

  const formatPosterInfoForCopy = (posterInfo) => {
    if (!posterInfo || typeof posterInfo !== 'object') {
      return '포스터 정보를 추출할 수 없습니다.';
    }
    
    return Object.entries(posterInfo)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : (value || '정보 없음')}`)
      .join('\n');
  };

  // 컴포넌트 언마운트 시 미리보기 URL 정리
  useEffect(() => {
    return () => {
      if (selectedFilePreview) {
        URL.revokeObjectURL(selectedFilePreview);
      }
    };
  }, [selectedFilePreview]);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Image size={20} />
          이미지 분석 (통합)
        </h3>
      </div>
      
      <div className="card-content">
        {/* API 키 설정 섹션 */}
        <div className="form-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <label className="form-label">
            <Key size={16} style={{ display: 'inline', marginRight: '4px' }} />
            API 키 (Upstage)
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
                      onClick={() => deleteApiKey(key)}
                      style={{ cursor: 'pointer', color: 'var(--error-500)' }}
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
            Upstage API 키가 필요합니다. 저장된 키는 브라우저에 안전하게 보관됩니다.
          </small>
        </div>

        {/* 처리 모드 선택 */}
        <div className="form-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <label className="form-label">처리 모드</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--spacing-sm)' }}>
            {modes.map(mode => {
              const Icon = mode.icon;
              const isMainMode = mode.isMain;
              return (
                <label key={mode.id} style={{ 
                  display: 'flex', 
                  flexDirection: 'column',
                  gap: '4px',
                  cursor: 'pointer',
                  padding: 'var(--spacing-sm)',
                  borderRadius: '8px',
                  border: `2px solid ${
                    activeMode === mode.id 
                      ? (isMainMode ? 'var(--success-600)' : 'var(--primary-400)') 
                      : (isMainMode ? 'var(--success-500)' : 'var(--gray-300)')
                  }`,
                  backgroundColor: isMainMode 
                    ? (activeMode === mode.id ? 'var(--success-600)' : 'var(--success-500)')
                    : (activeMode === mode.id ? 'var(--primary-50)' : 'white'),
                  transition: 'all 0.2s ease',
                  boxShadow: isMainMode 
                    ? (activeMode === mode.id ? '0 4px 12px rgba(34, 197, 94, 0.5)' : '0 2px 8px rgba(34, 197, 94, 0.3)')
                    : 'none'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input
                      type="radio"
                      value={mode.id}
                      checked={activeMode === mode.id}
                      onChange={(e) => setActiveMode(e.target.value)}
                      style={isMainMode ? { 
                        accentColor: 'white',
                        transform: 'scale(1.1)'
                      } : {}}
                    />
                    <Icon size={16} style={{ color: isMainMode ? 'white' : 'inherit' }} />
                    <strong style={{ color: isMainMode ? 'white' : 'inherit' }}>
                      {mode.label}
                      {isMainMode && ' ⭐'}
                    </strong>
                    {mode.needsApiKey && <Key size={12} style={{ color: isMainMode ? 'rgba(255, 255, 255, 0.9)' : 'var(--warning-500)' }} />}
                  </div>
                  <small style={{ 
                    color: isMainMode ? 'rgba(255, 255, 255, 0.95)' : 'var(--gray-600)', 
                    fontSize: '11px', 
                    marginLeft: '20px',
                    fontWeight: isMainMode ? '500' : 'normal'
                  }}>
                    {mode.description}
                  </small>
                </label>
              );
            })}
          </div>
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

          {(activeMode === 'resize' || activeMode === 'process') && (
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
          )}
        </div>

        {/* 선택된 이미지 미리보기 */}
        {selectedFilePreview && (
          <div style={{ marginTop: 'var(--spacing-lg)' }}>
            <h4 style={{ marginBottom: 'var(--spacing-md)', fontSize: '16px', fontWeight: '600' }}>
              📷 선택된 이미지
            </h4>
            <div style={{ 
              border: '1px solid var(--gray-200)', 
              borderRadius: 'var(--border-radius)',
              padding: 'var(--spacing-sm)',
              backgroundColor: 'var(--gray-50)',
              textAlign: 'center'
            }}>
              <img 
                src={selectedFilePreview}
                alt="Selected file preview"
                style={{ 
                  maxWidth: '100%', 
                  maxHeight: '300px',
                  borderRadius: 'var(--border-radius)',
                  objectFit: 'contain'
                }}
              />
            </div>
          </div>
        )}

        <div style={{ marginTop: 'var(--spacing-lg)' }}>
          <button
            className={`btn ${activeMode === 'process' ? 'btn-success' : 'btn-primary'}`}
            onClick={handleExecute}
            disabled={isLoading || !selectedFile || (modes.find(m => m.id === activeMode)?.needsApiKey && !apiKey.trim())}
            style={{ 
              marginRight: 'var(--spacing-sm)',
              ...(activeMode === 'process' && {
                background: 'linear-gradient(135deg, var(--success-500) 0%, var(--success-600) 100%)',
                border: 'none',
                boxShadow: '0 4px 12px rgba(34, 197, 94, 0.3)',
                fontWeight: '600',
                fontSize: '14px'
              })
            }}
          >
            {isLoading ? (
              <>
                <Loader className="animate-spin" size={16} />
                처리 중...
              </>
            ) : (
              <>
                {React.createElement(modes.find(m => m.id === activeMode)?.icon || Upload, { size: 16 })}
                {modes.find(m => m.id === activeMode)?.label || '처리'}
                {activeMode === 'process' && ' 🚀'}
              </>
            )}
          </button>
          
          {modes.find(m => m.id === activeMode)?.needsApiKey && !apiKey.trim() && (
            <div style={{ marginTop: 'var(--spacing-sm)' }}>
              <small style={{ color: 'var(--danger-500)', fontSize: '12px' }}>
                이 기능을 사용하려면 API 키가 필요합니다
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
              {/* 원본 이미지 (크기 조정 모드가 아닐 때만 표시) */}
              {selectedFilePreview && activeMode !== 'resize' && activeMode !== 'process' && (
                <div>
                  <h5 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600' }}>
                    📷 원본 이미지
                  </h5>
                  <div style={{ 
                    border: '1px solid var(--gray-200)', 
                    borderRadius: 'var(--border-radius)',
                    padding: 'var(--spacing-sm)',
                    backgroundColor: 'var(--gray-50)',
                    textAlign: 'center'
                  }}>
                    <img 
                      src={selectedFilePreview}
                      alt="Original"
                      style={{ 
                        maxWidth: '100%', 
                        maxHeight: '250px',
                        borderRadius: 'var(--border-radius)',
                        objectFit: 'contain'
                      }}
                    />
                  </div>
                </div>
              )}

              {/* 처리된 이미지 (크기 조정된 경우) */}
              {processResult.resized_image && (
                <div>
                  <div className="flex justify-between items-center" style={{ marginBottom: 'var(--spacing-sm)' }}>
                    <h5 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>
                      {activeMode === 'resize' ? '🔧 크기 조정된 이미지' : '🔧 처리된 이미지'}
                    </h5>
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
                        maxHeight: '250px',
                        borderRadius: 'var(--border-radius)',
                        objectFit: 'contain'
                      }}
                    />
                  </div>
                </div>
              )}

              {/* OCR 텍스트 결과 */}
              {processResult.ocr_text && (
                <div>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: 'var(--spacing-sm)' 
                  }}>
                    <h5 style={{ margin: 0, fontSize: '14px', fontWeight: '600' }}>
                      <Eye size={14} style={{ display: 'inline', marginRight: '4px' }} />
                      OCR 텍스트 추출 결과
                    </h5>
                    <button
                      onClick={() => copyToClipboard(processResult.ocr_text, 'ocr')}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: copiedOcr ? 'var(--success-500)' : 'var(--gray-100)',
                        color: copiedOcr ? 'white' : 'var(--gray-600)',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.2s ease'
                      }}
                      title="OCR 텍스트 복사"
                    >
                      {copiedOcr ? <Check size={12} /> : <Copy size={12} />}
                      {copiedOcr ? '복사됨' : '복사'}
                    </button>
                  </div>
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

              {/* 포스터 분석 결과 - 전체 처리와 기존 포스터 분석 모두 지원 */}
              {(processResult.poster_info || (processResult.success !== undefined && processResult.success && processResult.poster_info)) && renderPosterInfo(processResult.poster_info)}
              
              {/* 전체 처리에서 포스터 분석 실패 시 오류 메시지 */}
              {activeMode === 'process' && processResult.poster_analysis_success === false && (
                <div style={{
                  padding: 'var(--spacing-md)',
                  backgroundColor: 'var(--warning-50)',
                  borderRadius: '8px',
                  border: '1px solid var(--warning-200)',
                  color: 'var(--warning-700)'
                }}>
                  <h5 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600' }}>
                    ⚠️ 포스터 분석 실패
                  </h5>
                  <div style={{ fontSize: '13px' }}>
                    이미지 크기조정과 OCR은 성공했지만, 포스터 분석에서 오류가 발생했습니다.
                    {processResult.poster_error && (
                      <div style={{ marginTop: '4px', fontStyle: 'italic' }}>
                        오류: {processResult.poster_error}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 기존 포스터 분석 실패 메시지 (analyze, extract 모드용) */}
              {processResult.success !== undefined && !processResult.success && activeMode !== 'process' ? (
                <div className="error-message" style={{
                  padding: 'var(--spacing-md)',
                  backgroundColor: 'var(--error-50)',
                  borderRadius: '8px',
                  border: '1px solid var(--error-200)',
                  color: 'var(--error-700)'
                }}>
                  분석 실패: {processResult.error || '알 수 없는 오류가 발생했습니다.'}
                </div>
              ) : null}

              {/* 처리 정보 */}
              {(processResult.original_filename || processResult.width || processResult.height) && (
                <div style={{ 
                  padding: 'var(--spacing-sm)', 
                  backgroundColor: 'var(--primary-50)', 
                  borderRadius: 'var(--border-radius)',
                  fontSize: '13px',
                  color: 'var(--primary-600)'
                }}>
                  {processResult.original_filename && (
                    <div><strong>파일명:</strong> {processResult.original_filename}</div>
                  )}
                  {processResult.width && processResult.height && (
                    <div><strong>처리 후 크기:</strong> {processResult.width} x {processResult.height} px</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="info-section" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--primary-700)' }}>
            🔧 통합 이미지 분석 기능
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--primary-600)' }}>
            <li><strong>크기 조정만:</strong> 이미지를 지정된 너비로 자동 조정 (비율 유지, API 키 불필요)</li>
            <li><strong>OCR만:</strong> 이미지 내 텍스트 추출 (Upstage API)</li>
            <li><strong>전체 처리:</strong> 이미지 크기 조정 + OCR 텍스트 추출 + 포스터 분석 (모든 기능)</li>
            <li><strong>포스터 분석:</strong> 구조화된 정보만 추출 (제목, 날짜, 장소 등)</li>
            <li><strong>OCR + 포스터 분석:</strong> OCR 텍스트 + 구조화된 정보 모두 추출</li>
            <li>JPEG, PNG 형식 지원, 처리된 이미지 다운로드 가능</li>
            <li>API 키는 로컬스토리지에 안전하게 저장</li>
          </ul>
        </div>

        <div className="info-section" style={{ marginTop: 'var(--spacing-md)', padding: 'var(--spacing-md)', backgroundColor: 'var(--warning-50)', borderRadius: 'var(--border-radius)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', fontWeight: '600', color: 'var(--warning-700)' }}>
            💡 사용 팁
          </h4>
          <ul style={{ margin: '0', paddingLeft: 'var(--spacing-md)', fontSize: '13px', color: 'var(--warning-600)' }}>
            <li>Upstage AI 계정에서 API 키를 발급받아 OCR 및 분석 기능 사용</li>
            <li>크기 조정만 원한다면 API 키 없이도 사용 가능</li>
            <li>텍스트가 명확한 고화질 이미지일수록 OCR 정확도가 높습니다</li>
            <li>포스터 분석은 영화, 콘서트, 행사 포스터에 최적화되어 있습니다</li>
            <li>너무 작은 크기로 조정하면 텍스트 인식이 어려울 수 있습니다</li>
            <li>한글, 영문, 숫자 텍스트 인식을 지원합니다</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ImageAnalysisCard; 