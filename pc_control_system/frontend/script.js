// 전역 변수
let isLoggedIn = false;
let currentUser = null;

// DOM 요소들
const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const statusMessage = document.getElementById('statusMessage');
const loading = document.getElementById('loading');
const loggedInStatus = document.getElementById('loggedInStatus');
const userInfo = document.getElementById('userInfo');
const loginView = document.getElementById('loginView');
const afterLoginView = document.getElementById('afterLoginView');
const afterLoginUserInfo = document.getElementById('afterLoginUserInfo');

// 우측 패널 높이를 좌측 고정 세션 높이에 맞추는 함수 (개선된 버전)
function syncRightPanelHeight(containerSelector, leftSelector, rightSelector) {
    const container = document.querySelector(containerSelector);
    const left = document.querySelector(leftSelector);
    const right = document.querySelector(rightSelector);
    
    if (!container || !left || !right) return;
    if (container.style.display === 'none') return; // 숨겨진 요소는 건너뛰기
    
    // CSS Grid에서 align-items: stretch가 작동하도록 초기화
    right.style.height = 'auto';
    right.style.minHeight = 'auto';
    
    // 레이아웃 재계산을 위해 짧은 딸레이
    requestAnimationFrame(() => {
        const leftHeight = left.getBoundingClientRect().height;
        if (leftHeight > 0) {
            right.style.minHeight = `${Math.ceil(leftHeight)}px`;
        }
    });
}

// 우측 패널 이미지 로드 후 다시 동기화 (개선된 버전)
function attachRecalcOnImages(containerSelector, leftSelector, rightSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    const images = container.querySelectorAll('img');
    let loadedImages = 0;
    const totalImages = images.length;
    
    if (totalImages === 0) {
        // 이미지가 없으면 즉시 동기화
        setTimeout(() => syncRightPanelHeight(containerSelector, leftSelector, rightSelector), 100);
        return;
    }
    
    images.forEach((img) => {
        if (img.complete) {
            loadedImages++;
            if (loadedImages === totalImages) {
                setTimeout(() => syncRightPanelHeight(containerSelector, leftSelector, rightSelector), 100);
            }
        } else {
            img.addEventListener('load', () => {
                loadedImages++;
                if (loadedImages === totalImages) {
                    setTimeout(() => syncRightPanelHeight(containerSelector, leftSelector, rightSelector), 100);
                }
            });
            img.addEventListener('error', () => {
                loadedImages++;
                if (loadedImages === totalImages) {
                    setTimeout(() => syncRightPanelHeight(containerSelector, leftSelector, rightSelector), 100);
                }
            });
        }
    });
}

// 로그인 폼 제출 이벤트
loginForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (isLoggedIn) {
        showMessage('이미 로그인되어 있습니다.', 'warning');
        return;
    }
    
    const name = document.getElementById('name').value.trim();
    const affiliation = document.getElementById('affiliation').value.trim();
    const contact = document.getElementById('contact').value.trim();
    const email = document.getElementById('email').value.trim();
    
    if (!name || !affiliation) {
        showMessage('이름과 소속을 입력해주세요.', 'error');
        return;
    }
    
    await login(name, affiliation, contact, email);
});

// 로그인 함수
async function login(name, affiliation, contact, email) {
    showLoading(true);
    setButtonsEnabled(false);
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                affiliation: affiliation,
                contact: contact,
                email: email,
                pc_number: PC_NUMBER
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 로그인 성공
            isLoggedIn = true;
            currentUser = { name, affiliation, contact, email };

            showMessage(data.message, data.status === 'success' ? 'success' : 'warning');

            // 시스템 잠금 해제 및 화면 전환 (기존 로그인 화면은 유지)
            unlockSystem();
            switchToAfterLoginView();
            document.title = `로그인 완료 - ${currentUser.name} (${PC_NUMBER}번 PC)`;
        } else {
            showMessage(data.detail || '로그인에 실패했습니다.', 'error');
        }
        
    } catch (error) {
        console.error('로그인 에러:', error);
        showMessage('네트워크 오류가 발생했습니다. 다시 시도해주세요.', 'error');
    } finally {
        showLoading(false);
        setButtonsEnabled(true);
    }
}

// 로그아웃 함수
async function logout() {
    if (!isLoggedIn || !currentUser) {
        showMessage('로그인된 상태가 아닙니다.', 'error');
        return;
    }
    
    
    showLoading(true);
    setButtonsEnabled(false);

    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: currentUser.name,
                affiliation: currentUser.affiliation,
                contact: currentUser.contact || '',
                email: currentUser.email || '',
                pc_number: PC_NUMBER
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('로그아웃이 완료되었습니다.', 'success');
        } else {
            showMessage(data.detail || '로그아웃에 실패했습니다.', 'error');
        }

    } catch (error) {
        console.error('로그아웃 에러:', error);
        showMessage('네트워크 오류가 발생했습니다. 다시 시도해주세요.', 'error');
    } finally {
        // API 호출 결과와 상관없이 UI는 초기화
        isLoggedIn = false;
        currentUser = null;
        resetUI();
        lockSystem();
        document.title = `로그인 - ${PC_NUMBER}번 PC`;
        
        showLoading(false);
        setButtonsEnabled(true);
    }
    
    
}

// 로그인 상태 UI 표시
function showLoggedInState(name, affiliation, contact, email) {
    loggedInStatus.style.display = 'block';
    const contactText = contact ? ` - ${contact}` : '';
    const emailText = email ? ` - ${email}` : '';
    userInfo.textContent = `${name} (${affiliation})${contactText}${emailText} - ${PC_NUMBER}번 PC 사용중`;

    // 상단 카드에서도 로그인 완료 표시되도록 유지
    if (afterLoginUserInfo) {
        afterLoginUserInfo.textContent = `${name} (${affiliation}) - ${PC_NUMBER}번 PC 사용중`;
    }

    document.title = `로그인 완료 - ${currentUser ? currentUser.name : ''} (${PC_NUMBER}번 PC)`;
}

// UI 초기화
function resetUI() {
    loggedInStatus.style.display = 'none';
    loginForm.style.display = 'block';
    document.getElementById('name').value = '';
    document.getElementById('affiliation').value = '';
    document.getElementById('contact').value = '';
    document.getElementById('email').value = '';

    // 화면 복귀
    if (loginView && afterLoginView) {
        loginView.style.display = 'grid';
        afterLoginView.style.display = 'none';
    }
}

// 로그인 화면에서 호출 버튼 클릭 시 처리
function handleCallFromLogin() {
    console.log("로그인 화면에서 호출 버튼 클릭"); // 디버깅용
    
    if (!isLoggedIn || !currentUser) {
        // 로그인하지 않은 상태에서 비회원 호출
        if (confirm("호출하시겠습니까?")) {
            sendGuestCallRequest();
        }
        return;
    }
    
    // 로그인된 상태라면 일반 호출 기능 실행
    showCallDialog();
}

// 호출 대화상자 표시
function showCallDialog() {
    console.log("호출 버튼이 클릭되었습니다."); // 디버깅용
    
    if (!currentUser) {
        alert("로그인된 상태가 아닙니다.");
        return;
    }
    
    if (confirm("호출하시겠습니까?")) {
        console.log("호출 요청을 전송합니다"); // 디버깅용
        sendCallRequest("호출요청");
    } else {
        console.log("호출이 취소되었습니다."); // 디버깅용
    }
}

// 호출 요청 전송
async function sendCallRequest(message) {
    console.log("sendCallRequest 함수 시작, currentUser:", currentUser); // 디버깅용
    
    if (!currentUser) {
        alert('로그인된 상태가 아닙니다.');
        return;
    }
    
    // currentUser 객체에 contact나 email이 없는 경우 빈 문자열로 처리
    if (!currentUser.contact) {
        currentUser.contact = '';
    }
    if (!currentUser.email) {
        currentUser.email = '';
    }
    
    const requestData = {
        name: currentUser.name,
        affiliation: currentUser.affiliation,
        contact: currentUser.contact,
        email: currentUser.email,
        pc_number: PC_NUMBER,
        message: message
    };
    
    console.log("호출 요청 데이터:", requestData); // 디버깅용
    
    try {
        console.log("API 호출 시작..."); // 디버깅용
        
        const response = await fetch('/api/call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log("API 응답 상태:", response.status); // 디버깅용
        
        const data = await response.json();
        console.log("API 응답 데이터:", data); // 디버깅용
        
        if (response.ok) {
            alert(`✅ ${data.message}`);
            console.log("호출 성공!"); // 디버깅용
        } else {
            alert(`❌ ${data.detail || '호출 전송에 실패했습니다.'}`);
            console.error("호출 실패:", data); // 디버깅용
        }
        
    } catch (error) {
        console.error('호출 에러:', error);
        alert('❌ 네트워크 오류가 발생했습니다. 다시 시도해주세요.');
    }
}

// 비회원 호출 요청 전송 
async function sendGuestCallRequest() {
    console.log("비회원 호출 요청 시작"); // 디버깅용
    
    const requestData = {
        pc_number: PC_NUMBER,
        message: "비회원 호출"
    };
    
    console.log("비회원 호출 요청 데이터:", requestData); // 디버깅용
    
    try {
        console.log("비회원 API 호출 시작..."); // 디버깅용
        
        const response = await fetch('/api/guest-call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log("비회원 API 응답 상태:", response.status); // 디버깅용
        
        const data = await response.json();
        console.log("비회원 API 응답 데이터:", data); // 디버깅용
        
        if (response.ok) {
            alert(`✅ ${data.message}`);
            console.log("비회원 호출 성공!"); // 디버깅용
        } else {
            alert(`❌ ${data.detail || '호출 전송에 실패했습니다.'}`);
            console.error("비회원 호출 실패:", data); // 디버깅용
        }
        
    } catch (error) {
        console.error('비회원 호출 에러:', error);
        alert('❌ 네트워크 오류가 발생했습니다. 다시 시도해주세요.');
    }
}

// 메시지 표시
function showMessage(message, type) {
    statusMessage.innerHTML = `<div class="${type}">${message}</div>`;
    
    // 3초 후 메시지 제거
    setTimeout(() => {
        statusMessage.innerHTML = '';
    }, 3000);
}

// 로딩 상태 표시/숨김
function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}

// 버튼 활성화/비활성화
function setButtonsEnabled(enabled) {
    loginBtn.disabled = !enabled;
    const callBtnMain = document.getElementById('callBtnMain');
    if (callBtnMain) {
        callBtnMain.disabled = !enabled;
    }
}

// 시스템 키 차단 (보안 기능)
function blockSystemKeys() {
    document.addEventListener('keydown', function(e) {
                    // 로그인되지 않은 상태에서만 키 차단
            if (!isLoggedIn) {
                // 로그인 폼 입력 필드에서는 Tab 키 허용
                const isInLoginForm = e.target && (
                    e.target.id === 'name' || 
                    e.target.id === 'affiliation' || 
                    e.target.id === 'contact' ||
                    e.target.id === 'email' ||
                    e.target.tagName === 'INPUT'
                );
            
            // Tab 키이면서 로그인 폼 내부라면 허용
            if (e.keyCode === 9 && isInLoginForm) {
                return true; // Tab 키 허용
            }
            
            // Alt + Tab, Alt + F4, Ctrl + Alt + Del, Windows 키 등 차단
            if (
                e.altKey || 
                e.ctrlKey && e.shiftKey ||
                e.keyCode === 91 || // Windows key
                e.keyCode === 93 || // Menu key
                e.keyCode === 9 ||  // Tab (폼 외부에서)
                e.keyCode === 27 || // Esc
                e.keyCode === 122   // F11
            ) {
                e.preventDefault();
                e.stopPropagation();
                showMessage('로그인 후 사용 가능합니다.', 'warning');
                return false;
            }
        }
    });
    
    // F12 (개발자도구) 완전 차단
    document.addEventListener('keydown', function(e) {
        if (e.keyCode === 123) { // F12
            e.preventDefault();
            e.stopPropagation();
            showMessage('개발자 도구는 사용할 수 없습니다.', 'error');
            return false;
        }
    });
}

// 시스템 잠금 해제
function unlockSystem() {
    console.log('시스템 잠금이 해제되었습니다.');
    // 여기에 추가적인 잠금 해제 로직을 구현할 수 있습니다.
}

// 시스템 잠금
function lockSystem() {
    console.log('시스템이 잠금되었습니다.');
    showMessage('로그인이 필요합니다.', 'warning');
    // 여기에 추가적인 잠금 로직을 구현할 수 있습니다.
}

// 페이지 새로고침/닫기 방지
window.addEventListener('beforeunload', function(e) {
    if (isLoggedIn) {
        const message = '로그아웃하지 않고 페이지를 나가시겠습니까?';
        e.returnValue = message;
        return message;
    }
});

// 브라우저 뒒로가기 방지
history.pushState(null, null, location.href);
window.addEventListener('popstate', function() {
    history.pushState(null, null, location.href);
    showMessage('뒤로가기는 사용할 수 없습니다.', 'warning');
});

// 웹페이지 닫기 함수
function closeWebPage() {
    // 이전의 전체 대체 방식은 제거하고, 새로운 afterLoginView를 사용
    switchToAfterLoginView();
    document.title = `로그인 완료 - ${currentUser ? currentUser.name : ''} (${PC_NUMBER}번 PC)`;
}

// 로그아웃 옵션 표시
function showLogoutOptions() {
    if (confirm("정말 로그아웃하시겠습니까?")) {
        // 로그아웃 처리
        logout();
    }
}

// 만족도 조사 이동 화면 표시 (사용안함 - 즉시 이동으로 변경)
// function showSurveyRedirectScreen() { ... }

// 백그라운드에서 로그아웃 API 호출
async function performLogoutAPI() {
    // 전역 변수를 로컬 변수로 복사 (상태가 이미 변경되었을 수 있음)
    const userToLogout = currentUser;
    
    if (!userToLogout) {
        console.log('로그인 정보가 없어 API 호출을 건너뛰니다.');
        return;
    }
    
    // contact나 email이 없는 경우 빈 문자열로 처리
    const contact = userToLogout.contact || '';
    const email = userToLogout.email || '';
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: userToLogout.name,
                affiliation: userToLogout.affiliation,
                contact: contact,
                email: email,
                pc_number: PC_NUMBER
            })
        });
        
        const data = await response.json();
        console.log('로그아웃 API 결과:', data);
        
    } catch (error) {
        console.error('로그아웃 API 에러:', error);
    }
}

// 완료 화면에서 로그아웃 실행 (사용안함 - 기본 logout 함수 사용)
async function performLogout() {
    // 기본 로그아웃 함수 호출
    await logout();
}

// 페이지 최소화 (실제 브라우저 최소화 시도)
function minimizePage() {
    try {
        // 방법 1: 브라우저 창 최소화 시도
        if (window.moveTo) {
            window.moveTo(-2000, -2000); // 화면 밖으로 이동
        }
        
        // 방법 2: 포커스 잃기
        if (window.blur) {
            window.blur();
        }
        
        // 방법 3: 안내 메시지
        setTimeout(() => {
            alert("💡 브라우저를 수동으로 최소화하세요!\n\n방법:\n• Alt+Tab을 눌러 다른 프로그램으로 전환\n• 작업표시줄의 다른 프로그램 클릭\n• 브라우저 창의 최소화 버튼(_) 클릭\n\n사용 종료시에는 이 탭으로 돌아와서 '사용 종료' 버튼을 누르세요.");
        }, 100);
        
    } catch (e) {
        alert("💡 브라우저를 수동으로 최소화하세요!\n\n방법:\n• Alt+Tab을 눌러 다른 프로그램으로 전환\n• 작업표시줄의 다른 프로그램 클릭\n• 브라우저 창의 최소화 버튼(_) 클릭");
    }
}

// 초기 상태에서 시스템 잠금
document.addEventListener('DOMContentLoaded', function() {
    lockSystem();
    
    // 초기 렌더 시에도 좌측 로그인 카드 높이에 우측 가이드 패널을 맞춤
    // 여러 단계로 나눌어서 안정성 향상
    setTimeout(() => {
        syncRightPanelHeight('#loginView', '#loginView .container', '#loginView .guide-panel');
        attachRecalcOnImages('#loginView', '#loginView .container', '#loginView .guide-panel');
    }, 100);
    
    setTimeout(() => {
        syncRightPanelHeight('#loginView', '#loginView .container', '#loginView .guide-panel');
    }, 500);
    
    // 리사이즈 시 재계산 (디바운스 추가)
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            syncRightPanelHeight('#loginView', '#loginView .container', '#loginView .guide-panel');
            syncRightPanelHeight('#afterLoginView', '#afterLoginView .after-card', '#afterLoginView .guide-panel');
        }, 150);
    });
}); 

// 로그인 후 전환용 헬퍼 (개선된 버전)
function switchToAfterLoginView() {
    // 로그인 상태 텍스트 업데이트
    if (currentUser && afterLoginUserInfo) {
        const contactText = currentUser.contact ? ` - ${currentUser.contact}` : '';
        const emailText = currentUser.email ? ` - ${currentUser.email}` : '';
        afterLoginUserInfo.textContent = `${currentUser.name} (${currentUser.affiliation})${contactText}${emailText} - ${PC_NUMBER}번 PC 사용중`;
    }
    
    if (loginView && afterLoginView) {
        loginView.style.display = 'none';
        afterLoginView.style.display = 'block';
    }

    // 좌측 고정 카드 높이에 맞춰 우측 안내 패널 높이 동기화
    // 여러 단계로 나눌어서 안정성 향상
    setTimeout(() => {
        syncRightPanelHeight('#afterLoginView', '#afterLoginView .after-card', '#afterLoginView .guide-panel');
        attachRecalcOnImages('#afterLoginView', '#afterLoginView .after-card', '#afterLoginView .guide-panel');
    }, 100);
    
    setTimeout(() => {
        syncRightPanelHeight('#afterLoginView', '#afterLoginView .after-card', '#afterLoginView .guide-panel');
    }, 500);
    
    // 피드백 폼 이벤트 리스너 추가
    setupFeedbackForm();
}

// 피드백 폼 설정
function setupFeedbackForm() {
    const feedbackForm = document.getElementById('feedbackForm');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', handleFeedbackSubmit);
    }
}

// 피드백 전송 처리
async function handleFeedbackSubmit(e) {
    e.preventDefault();
    
    const feedbackText = document.getElementById('feedbackText').value;
    const feedbackType = document.getElementById('feedbackType').value;
    const submitBtn = document.getElementById('feedbackSubmitBtn');
    
    if (!feedbackText.trim()) {
        alert('피드백 내용을 입력해주세요.');
        return;
    }
    
    // 버튼 비활성화 및 로딩 상태
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '📤 전송 중...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                feedback: feedbackText,
                type: feedbackType,
                user: currentUser,
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            // 성공 메시지 표시
            alert('✅ 피드백이 성공적으로 전송되었습니다!\n소중한 의견 감사합니다.');
            
            // 폼 초기화
            document.getElementById('feedbackText').value = '';
            document.getElementById('feedbackType').value = 'suggestion';
        } else {
            throw new Error('피드백 전송에 실패했습니다.');
        }
    } catch (error) {
        console.error('피드백 전송 오류:', error);
        alert('❌ 피드백 전송 중 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.');
    } finally {
        // 버튼 원래 상태로 복원
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}