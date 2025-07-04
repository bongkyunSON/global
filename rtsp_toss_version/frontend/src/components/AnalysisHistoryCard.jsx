import React, { useState, useEffect } from 'react';
import { History, Calendar, FileText, Brain, Loader, RefreshCcw, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

const AnalysisHistoryCard = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [expandedItems, setExpandedItems] = useState(new Set());
  const [copiedItems, setCopiedItems] = useState(new Set());

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/analysis/history?analysis_type=${filterType}&limit=5`);
      const data = await response.json();
      
      if (data.success) {
        setHistory(data.data);
      } else {
        console.error('분석 히스토리 조회 실패:', data.error);
      }
    } catch (error) {
      console.error('분석 히스토리 조회 중 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [filterType]);

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const toggleExpanded = (index) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  const copyToClipboard = async (text, index) => {
    try {
      await navigator.clipboard.writeText(text);
      const newCopied = new Set(copiedItems);
      newCopied.add(index);
      setCopiedItems(newCopied);
      
      // 2초 후 복사 상태 초기화
      setTimeout(() => {
        const resetCopied = new Set(copiedItems);
        resetCopied.delete(index);
        setCopiedItems(resetCopied);
      }, 2000);
    } catch (err) {
      console.error('복사 실패:', err);
      // 대체 방법
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
  };

  const renderHistoryItem = (item, index) => {
    const isOCR = item.type === 'OCR';
    const Icon = isOCR ? FileText : Brain;
    const isExpanded = expandedItems.has(index);
    const isCopied = copiedItems.has(index);
    
    // 복사할 텍스트 준비
    let copyText = '';
    if (isOCR) {
      copyText = `${item.type} 결과 (${item.filename})\n날짜: ${formatDate(item.timestamp)}\n\n${item.ocr_text || '텍스트가 없습니다.'}`;
    } else {
      copyText = `${item.type} 결과 (${item.filename})\n날짜: ${formatDate(item.timestamp)}\n\n`;
      if (item.poster_info && typeof item.poster_info === 'object') {
        copyText += Object.entries(item.poster_info)
          .map(([key, value]) => {
            // 값이 객체인 경우 처리
            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
              return `${key}: ${Object.entries(value).map(([k, v]) => `${k}: ${v}`).join(', ')}`;
            }
            // 배열인 경우 처리
            else if (Array.isArray(value)) {
              return `${key}: ${value.join(', ')}`;
            }
            // 일반 문자열/숫자인 경우 처리
            else {
              return `${key}: ${value || '정보 없음'}`;
            }
          })
          .join('\n');
      } else {
        copyText += '분석 결과가 없습니다.';
      }
    }
    
    return (
      <div key={index} className="history-item" style={{
        padding: 'var(--spacing-md)',
        backgroundColor: 'var(--white)',
        border: '1px solid var(--gray-200)',
        borderRadius: '8px',
        marginBottom: 'var(--spacing-sm)',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <div className="history-header" style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: 'var(--spacing-sm)',
          gap: 'var(--spacing-sm)'
        }}>
          <Icon size={20} style={{ 
            color: isOCR ? 'var(--info-600)' : 'var(--primary-600)' 
          }} />
          <div style={{ flex: 1 }}>
            <div style={{ 
              fontWeight: '600', 
              color: 'var(--gray-900)',
              fontSize: '14px' 
            }}>
              {item.type} - {item.filename}
            </div>
            <div style={{ 
              fontSize: '12px', 
              color: 'var(--gray-500)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              marginTop: '2px'
            }}>
              <Calendar size={12} />
              {formatDate(item.timestamp)}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              onClick={() => copyToClipboard(copyText, index)}
              style={{
                padding: '4px 8px',
                backgroundColor: isCopied ? 'var(--success-500)' : 'var(--gray-100)',
                color: isCopied ? 'white' : 'var(--gray-600)',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s ease'
              }}
              title="클립보드에 복사"
            >
              {isCopied ? <Check size={12} /> : <Copy size={12} />}
              {isCopied ? '복사됨' : '복사'}
            </button>
            {!isOCR && (
              <button
                onClick={() => toggleExpanded(index)}
                style={{
                  padding: '4px 8px',
                  backgroundColor: 'var(--gray-100)',
                  color: 'var(--gray-600)',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                title={isExpanded ? '축소' : '전체보기'}
              >
                {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {isExpanded ? '축소' : '전체'}
              </button>
            )}
          </div>
        </div>

        <div className="history-content" style={{
          backgroundColor: 'var(--gray-50)',
          padding: 'var(--spacing-sm)',
          borderRadius: '6px',
          fontSize: '13px',
          lineHeight: '1.4'
        }}>
          {isOCR ? (
            <div>
              <strong style={{ color: 'var(--info-700)' }}>추출된 텍스트:</strong>
              <div style={{ 
                marginTop: '4px',
                maxHeight: isExpanded ? 'none' : '100px',
                overflow: isExpanded ? 'visible' : 'auto',
                whiteSpace: 'pre-wrap',
                color: 'var(--gray-700)'
              }}>
                {item.ocr_text || '텍스트가 없습니다.'}
              </div>
            </div>
          ) : (
            <div>
              <strong style={{ color: 'var(--primary-700)' }}>AI 분석 결과:</strong>
              <div style={{ marginTop: '4px' }}>
                {item.poster_info && typeof item.poster_info === 'object' ? (
                  <div style={{ color: 'var(--gray-700)' }}>
                    {Object.entries(item.poster_info).slice(0, isExpanded ? undefined : 3).map(([key, value]) => (
                      <div key={key} style={{ 
                        marginBottom: '8px',
                        padding: '8px',
                        backgroundColor: 'var(--white)',
                        borderRadius: '4px',
                        border: '1px solid var(--gray-200)'
                      }}>
                        <div style={{ 
                          fontWeight: '600', 
                          color: 'var(--primary-700)',
                          marginBottom: '2px',
                          fontSize: '12px'
                        }}>
                          {key}
                        </div>
                        <div style={{
                          color: 'var(--gray-700)',
                          wordBreak: 'break-word'
                        }}>
                          {(() => {
                            // 값이 객체인 경우 처리
                            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                              const objectText = Object.entries(value)
                                .map(([k, v]) => `${k}: ${v}`)
                                .join(', ');
                              return isExpanded 
                                ? objectText
                                : (objectText.length > 50 ? objectText.substring(0, 50) + '...' : objectText);
                            }
                            // 배열인 경우 처리
                            else if (Array.isArray(value)) {
                              const arrayText = value.join(', ');
                              return isExpanded 
                                ? arrayText
                                : (arrayText.length > 50 ? arrayText.substring(0, 50) + '...' : arrayText);
                            }
                            // 일반 문자열/숫자인 경우 처리
                            else {
                              const stringValue = String(value || '정보 없음');
                              return isExpanded 
                                ? stringValue
                                : (stringValue.length > 50 ? stringValue.substring(0, 50) + '...' : stringValue);
                            }
                          })()}
                        </div>
                      </div>
                    ))}
                    {!isExpanded && Object.keys(item.poster_info).length > 3 && (
                      <div style={{ 
                        color: 'var(--gray-500)', 
                        fontStyle: 'italic', 
                        textAlign: 'center',
                        padding: '8px',
                        backgroundColor: 'var(--gray-100)',
                        borderRadius: '4px',
                        marginTop: '4px'
                      }}>
                        ... 및 {Object.keys(item.poster_info).length - 3}개 항목 더 (전체 보기 클릭)
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ color: 'var(--gray-500)' }}>분석 결과가 없습니다.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <History className="card-icon" />
          <span>분석 히스토리</span>
        </div>
        <button
          onClick={fetchHistory}
          disabled={loading}
          className="btn btn-outline btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
          새로고침
        </button>
      </div>

      <div className="card-content">
        {/* 필터 버튼들 */}
        <div style={{ 
          marginBottom: 'var(--spacing-md)',
          display: 'flex',
          gap: 'var(--spacing-sm)',
          flexWrap: 'wrap'
        }}>
          {[
            { value: 'all', label: '전체' },
            { value: 'ocr', label: 'OCR만' },
            { value: 'ai', label: 'AI 분석만' }
          ].map(filter => (
            <button
              key={filter.value}
              onClick={() => setFilterType(filter.value)}
              className={`btn btn-sm ${filterType === filter.value ? 'btn-primary' : 'btn-outline'}`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            padding: 'var(--spacing-xl)',
            color: 'var(--gray-500)'
          }}>
            <Loader className="animate-spin" size={24} style={{ marginRight: 'var(--spacing-sm)' }} />
            분석 히스토리를 불러오는 중...
          </div>
        ) : history.length > 0 ? (
          <div>
            <div style={{ 
              marginBottom: 'var(--spacing-md)',
              fontSize: '14px',
              color: 'var(--gray-600)'
            }}>
              최근 {history.length}개의 분석 결과
            </div>
            {history.map(renderHistoryItem)}
          </div>
        ) : (
          <div style={{ 
            textAlign: 'center',
            padding: 'var(--spacing-xl)',
            color: 'var(--gray-500)'
          }}>
            <History size={48} style={{ 
              opacity: 0.3, 
              marginBottom: 'var(--spacing-md)' 
            }} />
            <div>저장된 분석 결과가 없습니다.</div>
            <div style={{ fontSize: '14px', marginTop: '4px' }}>
              AI 포스터 분석을 사용하면 결과가 자동으로 저장됩니다.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisHistoryCard; 