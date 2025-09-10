// 통계 데이터 관리
let statsData = {
    totalUsers: 0,
    todayUsers: 0,
    periodUsers: 0,
    avgDailyUsers: 0,
    totalFeedbacks: 0,
    totalCalls: 0,
    totalDownloads: 0,
    dailyData: [],
    monthlyData: [],
    callData: [],
    downloadData: [],
    affiliationData: {},
    period: 'week',
    periodName: '최근 7일'
};

// 현재 선택된 기간
let currentPeriod = 'week';

// 차트 인스턴스들
let dailyChart = null;
let affiliationChart = null;
let monthlyChart = null;
let callChart = null;
let downloadChart = null;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async function() {
    try {
        await loadStatistics('week');
        updateStatCards();
        createCharts();
    } catch (error) {
        console.error('통계 로드 실패:', error);
        showError('통계 데이터를 불러오는데 실패했습니다.');
    }
});

// 기간 변경 함수
async function changePeriod(period) {
    currentPeriod = period;
    
    // 버튼 활성화 상태 변경
    document.querySelectorAll('.period-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(period + 'Btn').classList.add('active');
    
    // 데이터 다시 로드
    await loadStatistics(period);
    updateStatCards();
    createCharts();
}

// 돌아가기 함수
function goBack() {
    window.location.href = '/';
}

// 피드백 페이지로 이동
function goToFeedbackPage(event) {
    const url = '/graph/feedback';
    if (event && (event.ctrlKey || event.metaKey)) {
        // Ctrl/Cmd 키가 눌린 경우 새 탭으로 열기
        window.open(url, '_blank');
    } else {
        // 일반 클릭은 현재 탭에서 이동
        window.location.href = url;
    }
}

// 다운로드 통계 페이지로 이동
function goToDownloadPage(event) {
    const url = '/graph/download';
    if (event && (event.ctrlKey || event.metaKey)) {
        // Ctrl/Cmd 키가 눌린 경우 새 탭으로 열기
        window.open(url, '_blank');
    } else {
        // 일반 클릭은 현재 탭에서 이동
        window.location.href = url;
    }
}

// 통계 데이터 로드
async function loadStatistics(period = 'week') {
    const loading = document.getElementById('loading');
    loading.style.display = 'flex';
    
    try {
        const response = await fetch(`/api/statistics?period=${period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        statsData = { ...statsData, ...data };
        
    } catch (error) {
        console.error('API 호출 실패:', error);
        // 데모 데이터로 대체
        statsData = {
            totalUsers: 156,
            todayUsers: 23,
            periodUsers: 87,
            avgDailyUsers: 12,
            totalFeedbacks: 34,
            totalCalls: 18,
            totalDownloads: 25,
            callData: [
                { date: '2024-01-15', count: 3 },
                { date: '2024-01-16', count: 1 },
                { date: '2024-01-17', count: 2 },
                { date: '2024-01-18', count: 4 },
                { date: '2024-01-19', count: 2 },
                { date: '2024-01-20', count: 3 },
                { date: '2024-01-21', count: 3 }
            ],
            downloadData: [
                { date: '2024-01-15', count: 2 },
                { date: '2024-01-16', count: 1 },
                { date: '2024-01-17', count: 3 },
                { date: '2024-01-18', count: 0 },
                { date: '2024-01-19', count: 1 },
                { date: '2024-01-20', count: 2 },
                { date: '2024-01-21', count: 1 }
            ],
            dailyData: [
                { date: '2024-01-15', count: 15 },
                { date: '2024-01-16', count: 8 },
                { date: '2024-01-17', count: 12 },
                { date: '2024-01-18', count: 18 },
                { date: '2024-01-19', count: 10 },
                { date: '2024-01-20', count: 14 },
                { date: '2024-01-21', count: 23 }
            ],
            affiliationData: {
                '대학생': 45,
                '일반인': 38,
                '기업체': 25,
                '공무원': 18,
                '기타': 30
            },
            monthlyData: [
                { month: '2025-01', count: 0 },
                { month: '2025-02', count: 0 },
                { month: '2025-03', count: 0 },
                { month: '2025-04', count: 0 },
                { month: '2025-05', count: 0 },
                { month: '2025-06', count: 0 },
                { month: '2025-07', count: 0 },
                { month: '2025-08', count: 1 },
                { month: '2025-09', count: 0 },
                { month: '2025-10', count: 0 },
                { month: '2025-11', count: 0 },
                { month: '2025-12', count: 0 }
            ]
        };
    } finally {
        loading.style.display = 'none';
    }
}

// 통계 카드 업데이트
function updateStatCards() {
    document.getElementById('totalUsers').textContent = statsData.totalUsers.toLocaleString();
    document.getElementById('todayUsers').textContent = statsData.todayUsers.toLocaleString();
    document.getElementById('periodUsers').textContent = statsData.periodUsers.toLocaleString();
    document.getElementById('avgDailyUsers').textContent = statsData.avgDailyUsers.toLocaleString();
    document.getElementById('totalFeedbacks').textContent = statsData.totalFeedbacks.toLocaleString();
    document.getElementById('totalCalls').textContent = statsData.totalCalls.toLocaleString();
    if (document.getElementById('totalDownloads')) {
        document.getElementById('totalDownloads').textContent = (statsData.totalDownloads || 0).toLocaleString();
    }
    
    // 기간 라벨 업데이트
    if (statsData.period === 'year') {
        const currentYear = new Date().getFullYear();
        document.getElementById('periodLabel').textContent = `${currentYear}년 총 로그인 수`;
    } else {
        document.getElementById('periodLabel').textContent = 
            statsData.period === 'month' ? '최근 30일 로그인 수' : '최근 7일 로그인 수';
    }
    
    // 차트 제목 업데이트
    if (statsData.period === 'year') {
        const currentYear = new Date().getFullYear();
        document.getElementById('dailyChartTitle').textContent = `${currentYear}년 월별 로그인 현황`;
    } else {
        document.getElementById('dailyChartTitle').textContent = 
            `일별 로그인 현황 (${statsData.periodName || '최근 7일'})`;
    }
}

// 차트 생성
function createCharts() {
    if (statsData.period === 'year') {
        createMonthlyChart();
    } else {
        createDailyChart();
    }
    createAffiliationChart();
    createCallChart();
    createDownloadChart();
}

// 일별 로그인 차트
function createDailyChart() {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChart) {
        dailyChart.destroy();
    }
    
    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: statsData.dailyData.map(d => {
                const date = new Date(d.date);
                return `${date.getMonth() + 1}/${date.getDate()}`;
            }),
            datasets: [{
                label: '일별 로그인 수',
                data: statsData.dailyData.map(d => d.count),
                borderColor: '#F24949',
                backgroundColor: 'rgba(242, 73, 73, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#F24949',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: '중나좋체',
                            size: 14
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        font: {
                            family: '중나좋체'
                        }
                    }
                },
                x: {
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            }
        }
    });
}

// 월별 로그인 차트 (년도 탭용)
function createMonthlyChart() {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    // 기존 차트가 있으면 삭제
    if (dailyChart) {
        dailyChart.destroy();
    }
    
    // 디버깅: 월별 데이터 확인
    console.log('월별 데이터:', statsData.monthlyData);
    
    if (!statsData.monthlyData || statsData.monthlyData.length === 0) {
        console.error('월별 데이터가 없습니다!');
        return;
    }
    
    const labels = statsData.monthlyData.map(item => {
        const [year, month] = item.month.split('-');
        return `${parseInt(month)}월`;
    });
    const data = statsData.monthlyData.map(item => item.count);
    
    console.log('차트 라벨:', labels);
    console.log('차트 데이터:', data);
    
    dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '월별 로그인 수',
                data: data,
                backgroundColor: 'rgba(242, 73, 73, 0.6)',
                borderColor: '#F24949',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        font: {
                            family: '중나좋체'
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            }
        }
    });
}

// 소속별 분포 차트
function createAffiliationChart() {
    const ctx = document.getElementById('affiliationChart').getContext('2d');
    
    if (affiliationChart) {
        affiliationChart.destroy();
    }
    
    const colors = ['#F24949', '#F2BBBF', '#B7668D', '#10B981', '#667eea', '#764ba2', '#f59e0b', '#34d399', '#60a5fa', '#f472b6'];
    
    affiliationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(statsData.affiliationData),
            datasets: [{
                data: Object.values(statsData.affiliationData),
                backgroundColor: colors,
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            family: '중나좋체',
                            size: 14
                        },
                        padding: 20
                    }
                }
            }
        }
    });
}


// 에러 표시
function showError(message) {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <div style="text-align: center; padding: 50px;">
            <div style="font-size: 3rem; margin-bottom: 20px;">⚠️</div>
            <h2 style="color: #F24949; margin-bottom: 15px;">${message}</h2>
            <button onclick="location.reload()" style="padding: 12px 24px; background: #F24949; color: white; border: none; border-radius: 10px; cursor: pointer;">다시 시도</button>
        </div>
    `;
}



// 호출 모달 표시
async function showCallModal() {
    const modal = document.getElementById('callModal');
    const callList = document.getElementById('callList');
    
    modal.style.display = 'block';
    callList.innerHTML = '<div style="text-align: center; color: #666;">로딩 중...</div>';
    
    try {
        const response = await fetch('/api/calls');
        const data = await response.json();
        
        if (data.calls && data.calls.length > 0) {
            callList.innerHTML = data.calls.map(call => `
                <div class="item-card">
                    <div class="item-header">
                        <div class="item-user">${call.name} (${call.affiliation})</div>
                        <div class="item-time">${formatDateTime(call.timestamp)}</div>
                    </div>
                    <div class="item-type">${call.type === 'member' ? '회원 호출' : '비회원 호출'}</div>
                    <div class="item-content">PC ${call.pc_number}번: ${call.message}</div>
                </div>
            `).join('');
        } else {
            callList.innerHTML = '<div style="text-align: center; color: #666;">아직 호출이 없습니다.</div>';
        }
    } catch (error) {
        console.error('호출 로드 실패:', error);
        callList.innerHTML = '<div style="text-align: center; color: #F24949;">호출 목록을 불러오는데 실패했습니다.</div>';
    }
}

// 모달 닫기
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// 모달 외부 클릭시 닫기
window.onclick = function(event) {
    const callModal = document.getElementById('callModal');
    if (event.target === callModal) {
        callModal.style.display = 'none';
    }
}

// 호출 현황 차트
function createCallChart() {
    const ctx = document.getElementById('callChart').getContext('2d');
    
    if (callChart) {
        callChart.destroy();
    }
    
    let labels, data;
    
    // 차트 제목 업데이트
    const chartTitle = document.getElementById('callChartTitle');
    if (statsData.period === 'year') {
        chartTitle.textContent = '월별 호출 현황';
        // 호출 월별 데이터 사용
        labels = statsData.callMonthlyData ? statsData.callMonthlyData.map(item => {
            const [year, month] = item.month.split('-');
            return `${parseInt(month)}월`;
        }) : [];
        data = statsData.callMonthlyData ? statsData.callMonthlyData.map(item => item.count) : [];
    } else {
        chartTitle.textContent = `호출 현황 (${statsData.periodName || '최근 7일'})`;
        // 일별 데이터 사용
        labels = statsData.callData.map(item => {
            const date = new Date(item.date);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        });
        data = statsData.callData.map(item => item.count);
    }
    
    callChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: statsData.period === 'year' ? '월별 호출 수' : '일별 호출 수',
                data: data,
                backgroundColor: 'rgba(16, 185, 129, 0.6)',
                borderColor: '#10B981',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        font: {
                            family: '중나좋체'
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            }
        }
    });
}

// 다운로드 현황 차트
function createDownloadChart() {
    const ctx = document.getElementById('downloadChart').getContext('2d');
    
    if (downloadChart) {
        downloadChart.destroy();
    }
    
    let labels, data;
    
    // 차트 제목 업데이트
    const chartTitle = document.getElementById('downloadChartTitle');
    if (statsData.period === 'year') {
        chartTitle.textContent = '월별 다운로드 현황';
        // 다운로드 월별 데이터 사용
        labels = statsData.downloadMonthlyData ? statsData.downloadMonthlyData.map(item => {
            const [year, month] = item.month.split('-');
            return `${parseInt(month)}월`;
        }) : [];
        data = statsData.downloadMonthlyData ? statsData.downloadMonthlyData.map(item => item.count) : [];
    } else {
        chartTitle.textContent = `다운로드 현황 (${statsData.periodName || '최근 7일'})`;
        // 일별 데이터 사용
        labels = statsData.downloadData.map(item => {
            const date = new Date(item.date);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        });
        data = statsData.downloadData.map(item => item.count);
    }
    
    downloadChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: statsData.period === 'year' ? '월별 다운로드 수' : '일별 다운로드 수',
                data: data,
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: '#667eea',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        font: {
                            family: '중나좋체'
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            }
        }
    });
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

// 실시간 업데이트 (5분마다)
setInterval(async () => {
    try {
        await loadStatistics(currentPeriod);
        updateStatCards();
        createCharts();
    } catch (error) {
        console.error('실시간 업데이트 실패:', error);
    }
}, 5 * 60 * 1000); // 5분
