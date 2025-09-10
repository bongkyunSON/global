// 테마 시스템 JavaScript
// 테마 전환 및 저장 기능

// 테마 정보 정의
const themes = {
    pink: {
        name: '핑크 테마',
        icon: '💗',
        description: '따뜻하고 부드러운 핑크색 계열의 기본 테마'
    },
    green: {
        name: '그린 테마',
        icon: '🌿',
        description: '싱그러운 연두색과 파스텔 그린으로 자연의 생명력을 표현'
    },
    blue: {
        name: '블루 테마',
        icon: '💙',
        description: '시원한 블루 톤으로 차분하고 안정감 있는 분위기를 연출'
    },
    brown: {
        name: '브라운 테마',
        icon: '🤎',
        description: '따뜻한 브라운과 황금색으로 고급스럽고 편안한 느낌을 제공'
    },
    blackwhite: {
        name: '블랙&화이트 테마',
        icon: '⚫',
        description: '모던하고 세련된 흑백 조합으로 깔끔하고 전문적인 분위기를 연출'
    }
};

// 현재 테마 저장
let currentTheme = 'pink';

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    // 저장된 테마 불러오기
    loadCurrentTheme();
    
    // 현재 테마 표시 업데이트
    updateCurrentThemeDisplay();
    
    // 활성 테마 카드 표시 업데이트
    updateActiveThemeCard();
});

// 저장된 테마 불러오기
function loadCurrentTheme() {
    // 로컬스토리지에서 테마 불러오기
    const savedTheme = localStorage.getItem('selectedTheme');
    if (savedTheme && themes[savedTheme]) {
        currentTheme = savedTheme;
        applyTheme(currentTheme);
    } else {
        // 기본 테마 (핑크) 적용
        currentTheme = 'pink';
        applyTheme('pink');
    }
}

// 테마 선택 함수
function selectTheme(themeName) {
    if (!themes[themeName]) {
        console.error('존재하지 않는 테마:', themeName);
        return;
    }
    
    console.log('테마 선택:', themeName);
    
    // 테마 적용
    currentTheme = themeName;
    applyTheme(themeName);
    
    // 로컬스토리지에 저장
    localStorage.setItem('selectedTheme', themeName);
    
    // UI 업데이트
    updateCurrentThemeDisplay();
    updateActiveThemeCard();
    
    // 적용 메시지 표시
    showApplyMessage();
}

// 테마 적용 함수
function applyTheme(themeName) {
    console.log('테마 적용 중:', themeName);
    
    // 핑크 테마(기본 테마)인 경우 data-theme 속성 제거
    if (themeName === 'pink') {
        document.body.removeAttribute('data-theme');
        document.documentElement.removeAttribute('data-theme');
    } else {
        // 다른 테마인 경우 data-theme 속성 설정
        document.body.setAttribute('data-theme', themeName);
        document.documentElement.setAttribute('data-theme', themeName);
    }
    
    console.log('테마 적용 완료:', themeName);
}

// 현재 테마 표시 업데이트
function updateCurrentThemeDisplay() {
    const currentThemeNameElement = document.getElementById('currentThemeName');
    if (currentThemeNameElement && themes[currentTheme]) {
        currentThemeNameElement.textContent = themes[currentTheme].name;
    }
}

// 활성 테마 카드 표시 업데이트
function updateActiveThemeCard() {
    // 모든 테마 카드에서 active 클래스 제거
    document.querySelectorAll('.theme-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // 현재 테마 카드에 active 클래스 추가
    const activeCard = document.querySelector(`[data-theme="${currentTheme}"]`);
    if (activeCard) {
        activeCard.classList.add('active');
    }
}

// 적용 메시지 표시
function showApplyMessage() {
    const messageElement = document.getElementById('applyMessage');
    if (messageElement) {
        messageElement.style.display = 'block';
        
        // 3초 후 메시지 숨기기
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 3000);
    }
}

// 돌아가기 함수
function goBack() {
    // 이전 페이지로 돌아가기
    if (document.referrer) {
        window.location.href = document.referrer;
    } else {
        // 참조 페이지가 없으면 메인 페이지로
        window.location.href = '/';
    }
}

// 전역 테마 함수 (다른 페이지에서도 사용 가능)
window.ThemeSystem = {
    // 현재 테마 가져오기
    getCurrentTheme: function() {
        return localStorage.getItem('selectedTheme') || 'pink';
    },
    
    // 테마 적용하기
    applyCurrentTheme: function() {
        const theme = this.getCurrentTheme();
        
        // 핑크 테마(기본 테마)인 경우 data-theme 속성 제거
        if (theme === 'pink') {
            document.body.removeAttribute('data-theme');
            document.documentElement.removeAttribute('data-theme');
        } else {
            // 다른 테마인 경우 data-theme 속성 설정
            document.body.setAttribute('data-theme', theme);
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        return theme;
    },
    
    // 테마 변경하기
    setTheme: function(themeName) {
        if (themes[themeName]) {
            localStorage.setItem('selectedTheme', themeName);
            this.applyCurrentTheme();
            return true;
        }
        return false;
    },
    
    // 모든 테마 목록 가져오기
    getAllThemes: function() {
        return themes;
    }
};

// 키보드 단축키
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + T로 테마 토글
    if ((e.ctrlKey || e.metaKey) && e.key === 't') {
        e.preventDefault();
        
        // 테마 순서대로 순환
        const themeKeys = Object.keys(themes);
        const currentIndex = themeKeys.indexOf(currentTheme);
        const nextIndex = (currentIndex + 1) % themeKeys.length;
        const nextTheme = themeKeys[nextIndex];
        
        selectTheme(nextTheme);
    }
});

console.log('테마 시스템 초기화 완료');
