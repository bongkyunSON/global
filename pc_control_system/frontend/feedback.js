// 피드백 데이터 관리
let feedbackData = {
    feedbacks: [],
    period: 'week',
    count: 0
};

// 현재 선택된 기간
let currentPeriod = 'week';

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async function() {
    try {
        await loadFeedbacks('week');
        updateSummary();
        renderFeedbacks();
    } catch (error) {
        console.error('피드백 로드 실패:', error);
        showError('피드백 데이터를 불러오는데 실패했습니다.');
    }
});

// 돌아가기 함수
function goBack() {
    window.location.href = '/graph';
}

// 기간 변경 함수
async function changePeriod(period) {
    currentPeriod = period;
    
    // 버튼 활성화 상태 변경
    document.querySelectorAll('.period-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(period + 'Btn').classList.add('active');
    
    // 데이터 다시 로드
    await loadFeedbacks(period);
    updateSummary();
    renderFeedbacks();
}

// 피드백 데이터 로드
async function loadFeedbacks(period = 'week') {
    const loading = document.getElementById('loading');
    loading.style.display = 'flex';
    
    try {
        const response = await fetch(`/api/feedbacks?period=${period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        feedbackData = { ...feedbackData, ...data };
        
    } catch (error) {
        console.error('API 호출 실패:', error);
        // 데모 데이터로 대체
        feedbackData = {
            feedbacks: [
                {
                    timestamp: "2024-01-21T14:30:25+09:00",
                    feedback: "시스템이 너무 좋아요! 사용하기 편합니다.",
                    type: "suggestion",
                    type_name: "제안사항",
                    user: {
                        name: "김철수",
                        affiliation: "대학생",
                        contact: "010-1234-5678",
                        email: "kim@example.com"
                    }
                },
                {
                    timestamp: "2024-01-21T13:15:10+09:00",
                    feedback: "로그인 과정에서 약간의 지연이 있었습니다.",
                    type: "bug",
                    type_name: "버그 신고",
                    user: {
                        name: "이영희",
                        affiliation: "일반인",
                        contact: "010-9876-5432",
                        email: "lee@example.com"
                    }
                }
            ],
            period: period,
            count: 2
        };
    } finally {
        loading.style.display = 'none';
    }
}

// 요약 카드 업데이트
function updateSummary() {
    const countElement = document.getElementById('feedbackCount');
    const textElement = document.getElementById('periodText');
    
    countElement.textContent = feedbackData.count.toLocaleString();
    
    let periodText = '';
    switch(feedbackData.period) {
        case 'week':
            periodText = '최근 1주일 동안 들어온 피드백';
            break;
        case 'month':
            periodText = '최근 1개월 동안 들어온 피드백';
            break;
        case 'all':
            periodText = '전체 기간 동안 들어온 피드백';
            break;
        default:
            periodText = '피드백';
    }
    
    textElement.textContent = periodText;
}

// 피드백 목록 렌더링
function renderFeedbacks() {
    const feedbackGrid = document.getElementById('feedbackGrid');
    
    if (feedbackData.feedbacks && feedbackData.feedbacks.length > 0) {
        feedbackGrid.innerHTML = feedbackData.feedbacks.map(feedback => `
            <div class="feedback-card">
                <div class="feedback-header">
                    <div class="feedback-user">${feedback.user.name} (${feedback.user.affiliation})</div>
                    <div class="feedback-time">${formatDateTime(feedback.timestamp)}</div>
                </div>
                <div class="feedback-type">${feedback.type_name}</div>
                <div class="feedback-content">${feedback.feedback}</div>
                ${feedback.user.contact ? `<div style="margin-top: 10px; font-size: 0.9rem; color: #666;">📞 ${feedback.user.contact}</div>` : ''}
                ${feedback.user.email ? `<div style="margin-top: 5px; font-size: 0.9rem; color: #666;">📧 ${feedback.user.email}</div>` : ''}
            </div>
        `).join('');
    } else {
        feedbackGrid.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem; margin-bottom: 20px;">📝</div>
                <div>선택한 기간에 피드백이 없습니다.</div>
                <div style="margin-top: 10px; opacity: 0.7;">다른 기간을 선택해보세요.</div>
            </div>
        `;
    }
}

// 날짜 시간 포맷팅
function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 에러 표시
function showError(message) {
    const feedbackGrid = document.getElementById('feedbackGrid');
    feedbackGrid.innerHTML = `
        <div class="empty-state" style="color: #F24949;">
            <div style="font-size: 3rem; margin-bottom: 20px;">❌</div>
            <div>${message}</div>
            <button onclick="location.reload()" style="margin-top: 20px; padding: 12px 24px; background: #F24949; color: white; border: none; border-radius: 10px; cursor: pointer;">다시 시도</button>
        </div>
    `;
}

// 실시간 업데이트 (5분마다)
setInterval(async () => {
    try {
        await loadFeedbacks(currentPeriod);
        updateSummary();
        renderFeedbacks();
    } catch (error) {
        console.error('실시간 업데이트 실패:', error);
    }
}, 5 * 60 * 1000); // 5분
