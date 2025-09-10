// 다운로드 데이터 관리
let downloadData = {
    totalDownloads: 0,
    periodDownloads: 0,
    dailyData: [],
    monthlyData: [],
    templateData: {},
    downloads: [],
    period: 'week',
    periodName: '최근 7일'
};

// 현재 선택된 기간
let currentPeriod = 'week';

// 차트 인스턴스들
let dailyChart = null;
let templateChart = null;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', async function() {
    try {
        await loadDownloadStats('week');
        await loadDownloadList();
        updateStatCards();
        createCharts();
        renderDownloads();
    } catch (error) {
        console.error('다운로드 데이터 로드 실패:', error);
        showError('다운로드 데이터를 불러오는데 실패했습니다.');
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
    await loadDownloadStats(period);
    updateStatCards();
    createCharts();
}

// 다운로드 통계 데이터 로드
async function loadDownloadStats(period = 'week') {
    const loading = document.getElementById('loading');
    loading.style.display = 'flex';
    
    try {
        const response = await fetch(`/api/download-statistics?period=${period}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        downloadData = { ...downloadData, ...data };
        
    } catch (error) {
        console.error('다운로드 통계 API 호출 실패:', error);
        // 데모 데이터로 대체
        downloadData = {
            totalDownloads: 25,
            periodDownloads: 8,
            dailyData: [
                { date: '2024-01-15', count: 2 },
                { date: '2024-01-16', count: 1 },
                { date: '2024-01-17', count: 3 },
                { date: '2024-01-18', count: 0 },
                { date: '2024-01-19', count: 1 },
                { date: '2024-01-20', count: 1 },
                { date: '2024-01-21', count: 0 }
            ],
            templateData: {
                '1번 기본 프리셋': 8,
                '2번 정책 인사이트': 5,
                '3번 세미나 포럼': 4,
                '4번 이슈 브리핑': 3,
                '5번 문화 홍보': 2,
                '6번 펙트체크': 2,
                '7번 이슈 고발': 1
            },
            period: period,
            periodName: period === 'month' ? '최근 30일' : (period === 'year' ? '올해' : '최근 7일')
        };
    } finally {
        loading.style.display = 'none';
    }
}

// 다운로드 목록 로드
async function loadDownloadList() {
    try {
        const response = await fetch('/api/downloads');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        downloadData.downloads = data.downloads || [];
        
    } catch (error) {
        console.error('다운로드 목록 API 호출 실패:', error);
        // 데모 데이터로 대체
        downloadData.downloads = [
            {
                timestamp: "2024-01-21T14:30:25+09:00",
                template_number: 1,
                template_title: "1번 기본 프리셋",
                filename: "1_기본프리셋.zip"
            },
            {
                timestamp: "2024-01-21T13:15:10+09:00",
                template_number: 2,
                template_title: "2번 정책 인사이트",
                filename: "2_정책 인사이트.zip"
            },
            {
                timestamp: "2024-01-20T16:45:30+09:00",
                template_number: 3,
                template_title: "3번 세미나 포럼",
                filename: "3_세미나 포럼.zip"
            }
        ];
    }
}

// 통계 카드 업데이트
function updateStatCards() {
    document.getElementById('totalDownloads').textContent = (downloadData.totalDownloads || 0).toLocaleString();
    document.getElementById('periodDownloads').textContent = (downloadData.periodDownloads || 0).toLocaleString();
    
    // 기간 라벨 업데이트
    if (downloadData.period === 'year') {
        const currentYear = new Date().getFullYear();
        document.getElementById('periodLabel').textContent = `${currentYear}년 총 다운로드 수`;
    } else {
        document.getElementById('periodLabel').textContent = 
            downloadData.period === 'month' ? '최근 30일 다운로드 수' : '최근 7일 다운로드 수';
    }
    
    // 차트 제목 업데이트
    if (downloadData.period === 'year') {
        const currentYear = new Date().getFullYear();
        document.getElementById('dailyChartTitle').textContent = `${currentYear}년 월별 다운로드 현황`;
    } else {
        document.getElementById('dailyChartTitle').textContent = 
            `일별 다운로드 현황 (${downloadData.periodName || '최근 7일'})`;
    }
}

// 차트 생성
function createCharts() {
    if (downloadData.period === 'year') {
        createMonthlyChart();
    } else {
        createDailyChart();
    }
    createTemplateChart();
}

// 일별 다운로드 차트
function createDailyChart() {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChart) {
        dailyChart.destroy();
    }
    
    dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: downloadData.dailyData.map(d => {
                const date = new Date(d.date);
                return `${date.getMonth() + 1}/${date.getDate()}`;
            }),
            datasets: [{
                label: '일별 다운로드 수',
                data: downloadData.dailyData.map(d => d.count),
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
                        font: {
                            family: '중나좋체'
                        }
                    }
                }
            }
        }
    });
}

// 월별 다운로드 차트 (년도 탭용)
function createMonthlyChart() {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChart) {
        dailyChart.destroy();
    }
    
    const labels = downloadData.monthlyData.map(item => {
        const [year, month] = item.month.split('-');
        return `${parseInt(month)}월`;
    });
    const data = downloadData.monthlyData.map(item => item.count);
    
    dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '월별 다운로드 수',
                data: data,
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#10B981',
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

// 템플릿별 분포 차트
function createTemplateChart() {
    const ctx = document.getElementById('templateChart').getContext('2d');
    
    if (templateChart) {
        templateChart.destroy();
    }
    
    const colors = ['#F24949', '#F2BBBF', '#B7668D', '#10B981', '#667eea', '#764ba2', '#f59e0b', '#34d399', '#60a5fa', '#f472b6'];
    
    templateChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(downloadData.templateData),
            datasets: [{
                data: Object.values(downloadData.templateData),
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
                            size: 12
                        },
                        padding: 15
                    }
                }
            }
        }
    });
}

// 다운로드 목록 렌더링
function renderDownloads() {
    const downloadGrid = document.getElementById('downloadGrid');
    
    if (downloadData.downloads && downloadData.downloads.length > 0) {
        downloadGrid.innerHTML = downloadData.downloads.map(download => `
            <div class="download-card">
                <div class="download-header">
                    <div class="download-template">${download.template_title}</div>
                    <div class="download-time">${formatDateTime(download.timestamp)}</div>
                </div>
                <div class="download-filename">📁 ${download.filename}</div>
            </div>
        `).join('');
    } else {
        downloadGrid.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem; margin-bottom: 20px;">⬇️</div>
                <div>아직 다운로드가 없습니다.</div>
                <div style="margin-top: 10px; opacity: 0.7;">숏츠 템플릿을 다운로드해보세요.</div>
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
    const downloadGrid = document.getElementById('downloadGrid');
    downloadGrid.innerHTML = `
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
        await loadDownloadStats(currentPeriod);
        await loadDownloadList();
        updateStatCards();
        createCharts();
        renderDownloads();
    } catch (error) {
        console.error('실시간 업데이트 실패:', error);
    }
}, 5 * 60 * 1000); // 5분
