import React, { useState, useEffect } from 'react';
import { FileText, Upload, Eye, Key, Trash2, Brain, BookOpen, Loader } from 'lucide-react';
import { usePosterAnalyze, usePosterExtractWithOcr } from '../hooks/useApi';

// Error Boundary 클래스 컴포넌트
class PosterAnalysisErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('PosterAnalysisCard 에러:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <FileText size={20} />
              포스터 분석 (AI 정보 추출)
            </h3>
          </div>
          <div className="card-content">
            <div className="error-message" style={{
              padding: 'var(--spacing-lg)',
              backgroundColor: 'var(--error-50)',
              borderRadius: '8px',
              border: '1px solid var(--error-200)',
              color: 'var(--error-700)',
              textAlign: 'center'
            }}>
              <h4>⚠️ 오류가 발생했습니다</h4>
              <p>포스터 분석 기능에서 예상치 못한 오류가 발생했습니다.</p>
              <p>페이지를 새로고침하거나 다른 이미지로 시도해보세요.</p>
              <button 
                className="btn btn-primary" 
                onClick={() => window.location.reload()}
                style={{ marginTop: 'var(--spacing-md)' }}
              >
                페이지 새로고침
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const PosterAnalysisCard = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [savedApiKeys, setSavedApiKeys] = useState([]);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [analysisMode, setAnalysisMode] = useState('analyze'); // 'analyze' 또는 'extract'
  
  const { loading: loadingAnalyze, execute: analyzePoster } = usePosterAnalyze();
  const { loading: loadingExtract, execute: extractPosterWithOcr } = usePosterExtractWithOcr();

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
      setAnalysisResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      alert('분석할 포스터 이미지를 선택해주세요.');
      return;
    }

    if (!apiKey.trim()) {
      alert('API 키를 입력해주세요.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('api_key', apiKey.trim());

    try {
      let result;
      if (analysisMode === 'analyze') {
        result = await analyzePoster(formData);
      } else {
        result = await extractPosterWithOcr(formData);
      }
      
      // 결과 데이터 안전성 검사 및 정리
      if (result && typeof result === 'object') {
        // OCR 텍스트가 너무 길면 제한
        if (result.ocr_text && typeof result.ocr_text === 'string' && result.ocr_text.length > 5000) {
          result.ocr_text = result.ocr_text.substring(0, 5000) + '\n\n... (텍스트가 너무 길어 일부만 표시됩니다)';
        }
        
        // poster_info 객체의 각 값들도 길이 제한
        if (result.poster_info && typeof result.poster_info === 'object') {
          const cleanedPosterInfo = {};
          Object.entries(result.poster_info).forEach(([key, value]) => {
            if (typeof value === 'string' && value.length > 1000) {
              cleanedPosterInfo[key] = value.substring(0, 1000) + '...';
            } else if (Array.isArray(value)) {
              cleanedPosterInfo[key] = value.slice(0, 10); // 배열도 최대 10개까지만
            } else if (typeof value === 'object' && value !== null) {
              // 객체를 문자열로 변환하여 React 렌더링 에러 방지
              try {
                const entries = Object.entries(value);
                if (entries.length === 0) {
                  cleanedPosterInfo[key] = '빈 객체';
                } else {
                  const formatted = entries.map(([k, v]) => `${k}: ${String(v)}`).join(', ');
                  cleanedPosterInfo[key] = formatted.length > 1000 ? formatted.substring(0, 1000) + '...' : formatted;
                }
              } catch (err) {
                cleanedPosterInfo[key] = '[객체 형태 데이터]';
              }
            } else {
              cleanedPosterInfo[key] = value;
            }
          });
          result.poster_info = cleanedPosterInfo;
        }
      }
      
      setAnalysisResult(result);
    } catch (error) {
      console.error('포스터 분석 에러:', error);
      setAnalysisResult({
        success: false,
        error: `분석 실패: ${error.message || '알 수 없는 오류'}`
      });
    }
  };

  const renderPosterInfo = (posterInfo) => {
    try {
      if (!posterInfo || typeof posterInfo !== 'object') {
        return <div style={{ color: 'var(--gray-500)' }}>포스터 정보를 추출할 수 없습니다.</div>;
      }

      const entries = Object.entries(posterInfo);
      if (entries.length === 0) {
        return <div style={{ color: 'var(--gray-500)' }}>추출된 포스터 정보가 없습니다.</div>;
      }

      return (
        <div className="poster-info">
          <h4 style={{ marginBottom: 'var(--spacing-md)', color: 'var(--primary-600)' }}>
            📋 추출된 포스터 정보
          </h4>
          <div className="info-grid" style={{ 
            display: 'grid', 
            gap: 'var(--spacing-sm)',
            fontSize: '14px'
          }}>
            {entries.slice(0, 20).map(([key, value], index) => {
              try {
                // 값이 너무 길면 잘라내기
                let displayValue = '정보 없음';
                
                                 if (value !== null && value !== undefined) {
                   if (typeof value === 'string') {
                     displayValue = value.length > 500 ? value.substring(0, 500) + '...' : value;
                   } else if (Array.isArray(value)) {
                     const joinedValue = value.slice(0, 10).join(', ');
                     displayValue = joinedValue.length > 500 ? joinedValue.substring(0, 500) + '...' : joinedValue;
                   } else if (typeof value === 'object') {
                     try {
                       // 객체를 보기 좋게 포맷팅
                       const entries = Object.entries(value);
                       if (entries.length === 0) {
                         displayValue = '빈 객체';
                       } else {
                         displayValue = entries.map(([k, v]) => `${k}: ${String(v)}`).join(', ');
                         if (displayValue.length > 500) {
                           displayValue = displayValue.substring(0, 500) + '...';
                         }
                       }
                     } catch (err) {
                       displayValue = '[객체 형태 데이터]';
                     }
                   } else {
                     displayValue = String(value).substring(0, 500);
                   }
                 }
                
                return (
                  <div key={`${key}-${index}`} className="info-item" style={{
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
                      {String(key).substring(0, 100)}
                    </div>
                    <div style={{ 
                      color: 'var(--gray-600)',
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word'
                    }}>
                      {displayValue}
                    </div>
                  </div>
                );
              } catch (itemError) {
                console.error(`포스터 정보 항목 렌더링 에러 (${key}):`, itemError);
                return (
                  <div key={`error-${index}`} style={{
                    padding: 'var(--spacing-sm)',
                    backgroundColor: 'var(--error-50)',
                    borderRadius: '6px',
                    border: '1px solid var(--error-200)',
                    color: 'var(--error-700)'
                  }}>
                    {key}: 렌더링 오류
                  </div>
                );
              }
            })}
          </div>
        </div>
      );
    } catch (error) {
      console.error('renderPosterInfo 전체 에러:', error);
      return (
        <div style={{
          padding: 'var(--spacing-md)',
          backgroundColor: 'var(--error-50)',
          borderRadius: '8px',
          border: '1px solid var(--error-200)',
          color: 'var(--error-700)'
        }}>
          포스터 정보 렌더링 중 오류가 발생했습니다: {error.message}
        </div>
      );
    }
  };

  const isLoading = loadingAnalyze || loadingExtract;

  return (
    <PosterAnalysisErrorBoundary>
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <FileText size={20} />
            포스터 분석 (AI 정보 추출)
          </h3>
        </div>
        
        <div className="card-content">
          {/* API 키 설정 섹션 */}
          <div className="form-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <label className="form-label">
              <Key size={16} style={{ display: 'inline', marginRight: '4px' }} />
              API 키 (Gemini)
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
              <div style={{ display: 'flex', gap: 'var(--spacing-xs)', marginTop: 'var(--spacing-xs)' }}>
                <input
                  type="text"
                  className="input"
                  placeholder="새 API 키 입력..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  style={{ flex: 1 }}
                />
                <button 
                  className="btn btn-primary"
                  onClick={saveApiKey}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  저장
                </button>
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
                style={{ marginTop: 'var(--spacing-xs)' }}
              >
                <Key size={16} />
                새 API 키 추가
              </button>
            )}
          </div>

          {/* 분석 모드 선택 */}
          <div className="form-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <label className="form-label">분석 모드</label>
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                cursor: 'pointer',
                padding: 'var(--spacing-sm)',
                borderRadius: '6px',
                border: '1px solid var(--gray-300)',
                backgroundColor: analysisMode === 'analyze' ? 'var(--primary-50)' : 'white'
              }}>
                <input
                  type="radio"
                  value="analyze"
                  checked={analysisMode === 'analyze'}
                  onChange={(e) => setAnalysisMode(e.target.value)}
                />
                <Brain size={16} />
                구조화된 정보만 추출
              </label>
              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                cursor: 'pointer',
                padding: 'var(--spacing-sm)',
                borderRadius: '6px',
                border: '1px solid var(--gray-300)',
                backgroundColor: analysisMode === 'extract' ? 'var(--primary-50)' : 'white'
              }}>
                <input
                  type="radio"
                  value="extract"
                  checked={analysisMode === 'extract'}
                  onChange={(e) => setAnalysisMode(e.target.value)}
                />
                <BookOpen size={16} />
                OCR 텍스트 + 구조화된 정보
              </label>
            </div>
          </div>

          {/* 파일 업로드 */}
          <div className="form-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <label className="form-label">포스터 이미지</label>
            <div className="file-upload-container">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="file-input"
                id="poster-file"
              />
              <label htmlFor="poster-file" className="file-upload-label">
                <Upload size={20} />
                {selectedFile ? selectedFile.name : '포스터 이미지 선택'}
              </label>
            </div>
            {selectedFile && (
              <div className="file-info">
                <span>파일 크기: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            )}
          </div>

          {/* 분석 버튼 */}
          <div className="button-group" style={{ marginBottom: 'var(--spacing-lg)' }}>
            <button
              className="btn btn-primary"
              onClick={handleAnalyze}
              disabled={isLoading || !selectedFile || !apiKey.trim()}
            >
              {isLoading ? (
                <>
                  <Loader className="animate-spin" size={16} />
                  {analysisMode === 'analyze' ? '분석 중...' : '추출 중...'}
                </>
              ) : (
                <>
                  {analysisMode === 'analyze' ? <Brain size={16} /> : <BookOpen size={16} />}
                  {analysisMode === 'analyze' ? '포스터 분석' : 'OCR + 분석'}
                </>
              )}
            </button>
          </div>

                  {/* 결과 표시 */}
        {analysisResult && (
          <div className="result-section">
            {analysisResult.success ? (
              <div>
                {/* OCR 텍스트가 있으면 표시 */}
                {analysisResult.ocr_text && (
                  <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <h4 style={{ 
                      marginBottom: 'var(--spacing-md)', 
                      color: 'var(--primary-600)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <Eye size={16} />
                      추출된 텍스트 ({String(analysisResult.ocr_text || '').length.toLocaleString()}자)
                    </h4>
                    <div className="ocr-result" style={{
                      padding: 'var(--spacing-md)',
                      backgroundColor: 'var(--gray-50)',
                      borderRadius: '8px',
                      border: '1px solid var(--gray-200)',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      maxHeight: '300px',
                      overflowY: 'auto',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {(() => {
                        try {
                          const text = String(analysisResult.ocr_text || '');
                          return text.length > 3000 
                            ? text.substring(0, 3000) + '\n\n... (전체 텍스트가 너무 길어 일부만 표시)'
                            : text;
                        } catch (error) {
                          console.error('OCR 텍스트 표시 에러:', error);
                          return '텍스트를 표시할 수 없습니다.';
                        }
                      })()}
                    </div>
                  </div>
                )}

                {/* 포스터 정보 표시 */}
                {analysisResult.poster_info && (
                  <div>
                    {(() => {
                      try {
                        return renderPosterInfo(analysisResult.poster_info);
                      } catch (error) {
                        console.error('포스터 정보 렌더링 에러:', error);
                        return (
                          <div className="error-message" style={{
                            padding: 'var(--spacing-md)',
                            backgroundColor: 'var(--warning-50)',
                            borderRadius: '8px',
                            border: '1px solid var(--warning-200)',
                            color: 'var(--warning-700)'
                          }}>
                            포스터 정보를 표시하는 중 오류가 발생했습니다. 데이터가 너무 크거나 형식이 잘못되었을 수 있습니다.
                            <br />
                            <small>에러 정보: {error.message}</small>
                          </div>
                        );
                      }
                    })()}
                  </div>
                )}
              </div>
            ) : (
              <div className="error-message" style={{
                padding: 'var(--spacing-md)',
                backgroundColor: 'var(--error-50)',
                borderRadius: '8px',
                border: '1px solid var(--error-200)',
                color: 'var(--error-700)'
              }}>
                분석 실패: {analysisResult.error || '알 수 없는 오류가 발생했습니다.'}
              </div>
            )}
          </div>
        )}
        </div>
      </div>
    </PosterAnalysisErrorBoundary>
  );
};

// Error Boundary로 감싸진 메인 컴포넌트 export
const WrappedPosterAnalysisCard = () => (
  <PosterAnalysisErrorBoundary>
    <PosterAnalysisCard />
  </PosterAnalysisErrorBoundary>
);

export default WrappedPosterAnalysisCard; 