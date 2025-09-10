// 전역 변수
let galleries = [];
let currentIndex = 0;
let currentModalImageIndex = 0;
let currentImages = [];

// 숏츠 템플릿 설명 데이터
const templateDescriptions = {
    "① 기본 프리셋 (범용 숏츠 템플릿)": "다양한 주제에 두루 활용할 수 있는 기본형 템플릿. 간결한 구성으로 빠르게 작업할 때 유용합니다.\n색톤: 블랙 & 화이트 (중립적, 심플, 어떤 주제에도 적합)",
    "② 정책 인사이트 (정책·현황보고, 기자회견)": "공식 브리핑이나 주요 정책 현황 발표를 강조하는 템플릿. 발표자의 메시지를 명확히 전달하는데 적합합니다. \n색톤: 진중한 딥블루 계열 (공신력·신뢰감을 강조)",
    "③ 세미나 포럼 (심도있는 세미나·학술토론)": "연구 발표나 전문 토론을 강조하는 템플릿. 정책 분석, 학술 토론 등 깊이 있는 주제에 적합합니다. \n색톤: 청량한 블루 계열 (지식·연구·객관성을 강조)",
    "④ 이슈 브리핑 (뉴스·시사·현안)": "시의성 있는 이슈나 정책 현안을 빠르게 전달하는 템플릿. 뉴스 클립, 현안 브리핑 숏츠에 적합합니다. \n색톤: 네이비 + 시안 계열 (차분하면서도 신속성·공신력을 전달)",
    "⑤ 문화 홍보 (문화·소통·행사·청년)": "문화 교류, 소통과 협력을 주제로 한 콘텐츠에 적합한 템플릿. 교류 행사, 포럼, 협력 모임 홍보에 활용 가능합니다. \n색톤: 밝은 핑크·퍼플 계열 (문화적 활기를 전달, 따뜻하고 친근한 분위기)",
    "⑥ 팩트 체크 (검증·이슈·고발)": "사회적 쟁점이나 정책 현안을 사실에 근거해 검증하고, 문제점을 날카롭게 지적하는 콘텐츠에 적합한 템플릿. \n색톤: 블랙 + 네온블루 계열 (강렬하고 직설적, 이슈 콘텐츠에 적합)",
    "⑦ 이슈 고발 (숨겨진 진실·강력한 폭로)": "사회적 논란이나 정책 문제를 직설적이고 강렬하게 드러내는 콘텐츠에 적합한 템플릿. 경고성 메시지, 비판적 영상에 효과적입니다. \n색톤: 블랙 + 레드/오렌지 포인트 (위기감·긴장감·경각심 강조)",
    "⑧ 산업 리포트 (과학적 분석·경제정책 해설)": "산업·경제·금융 이슈를 데이터와 분석 중심으로 전달하는 템플릿. 정책 설명이나 경제 브리핑 숏츠에 적합합니다. \n색톤: 보라·네이비 계열 (미래지향·전문성·신뢰감을 강화)",
    "⑨ 현장 스토리 (환경·문화·관광안내)": "시민 생활과 밀접한 환경·문화·관광 소식을 현장 중심으로 전달하는 템플릿. 공공 안내나 홍보 콘텐츠 제작에 적합합니다. \n색톤: 화이트 + 그레이 계열 (중립적이고 깔끔, 공공안내/홍보이미지에 최적)",
    "⑩ 디지털 세션 (IT·가상화폐·4차 산업혁명)": "첨단 기술과 산업 변화를 다루는 콘텐츠에 적합한 템플릿. 블록체인, 가상화폐, AI 등 미래 산업 흐름을 설명하는 숏츠에 활용 가능합니다. \n색톤: 네온 퍼플 + 블루 계열 (미래지향, 첨단기술, 혁신성 강조)"
};

// 폴더명을 원하는 텍스트 형식으로 변환하는 함수
function convertFolderNameToDisplayTitle(folderName) {
    const folderMapping = {
        "01_basic_preset": "① 기본 프리셋 (범용 숏츠 템플릿)",
        "02_policy_insight": "② 정책 인사이트 (정책·현황보고, 기자회견)",
        "03_seminar_forum": "③ 세미나 포럼 (심도있는 세미나·학술토론)",
        "04_issue_briefing": "④ 이슈 브리핑 (뉴스·시사·현안)",
        "05_culture_promotion": "⑤ 문화 홍보 (문화·소통·행사·청년)",
        "06_fact_check": "⑥ 팩트 체크 (검증·이슈·고발)",
        "07_issue_report": "⑦ 이슈 고발 (숨겨진 진실·강력한 폭로)",
        "08_industry_report": "⑧ 산업 리포트 (과학적 분석·경제정책 해설)",
        "09_field_story": "⑨ 현장 스토리 (환경·문화·관광안내)",
        "10_digital_session": "⑩ 디지털 세션 (IT·가상화폐·4차 산업혁명)"
    };
    return folderMapping[folderName] || folderName;
}

// DOM 요소들
const loadingElement = document.getElementById('loading');
const galleryContent = document.getElementById('galleryContent');
const errorMessage = document.getElementById('errorMessage');
const downloadBtn = document.getElementById('downloadBtn');
const galleryTitle = document.getElementById('galleryTitle');
const galleryDescription = document.getElementById('galleryDescription');
const imagesGrid = document.getElementById('imagesGrid');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const currentInfo = document.getElementById('currentInfo');
const retryBtn = document.getElementById('retryBtn');

// 모달 관련 요소들
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const modalClose = document.getElementById('modalClose');
const modalPrev = document.getElementById('modalPrev');
const modalNext = document.getElementById('modalNext');

// 초기화
document.addEventListener('DOMContentLoaded', function() {
    loadGalleries();
    setupEventListeners();
});

// 이벤트 리스너 설정
function setupEventListeners() {
    prevBtn.addEventListener('click', showPreviousGallery);
    nextBtn.addEventListener('click', showNextGallery);
    retryBtn.addEventListener('click', loadGalleries);
    
    // 모바일 네비게이션 버튼
    const prevBtnMobile = document.getElementById('prevBtnMobile');
    const nextBtnMobile = document.getElementById('nextBtnMobile');
    if (prevBtnMobile) prevBtnMobile.addEventListener('click', showPreviousGallery);
    if (nextBtnMobile) nextBtnMobile.addEventListener('click', showNextGallery);
    
    // 모달 이벤트 리스너
    modalClose.addEventListener('click', closeModal);
    modalPrev.addEventListener('click', showPreviousModalImage);
    modalNext.addEventListener('click', showNextModalImage);
    
    // 다운로드 버튼 클릭 이벤트
    downloadBtn.addEventListener('click', () => {
        // 중복 클릭 방지
        if (downloadBtn.disabled) {
            console.log('다운로드가 이미 진행 중입니다.');
            return;
        }
        downloadCurrentTemplate();
    });
    
    // 모달 배경 클릭 시 닫기
    imageModal.addEventListener('click', function(e) {
        if (e.target === imageModal) {
            closeModal();
        }
    });
    
    // 키보드 이벤트
    document.addEventListener('keydown', handleKeyPress);
}

// 키보드 이벤트 처리
function handleKeyPress(e) {
    switch(e.key) {
        case 'ArrowLeft':
            if (imageModal.style.display === 'flex') {
                showPreviousModalImage();
            } else {
                showPreviousGallery(); // 이제 순환형으로 작동
            }
            break;
        case 'ArrowRight':
            if (imageModal.style.display === 'flex') {
                showNextModalImage();
            } else {
                showNextGallery(); // 이제 순환형으로 작동
            }
            break;
        case 'Escape':
            if (imageModal.style.display === 'flex') {
                closeModal();
            }
            break;
    }
}

// 갤러리 데이터 로드
async function loadGalleries() {
    try {
        showLoading();
        
        const response = await fetch('/api/shorts-images');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API 응답 데이터:', data); // 디버깅
        
        galleries = data.galleries || [];
        
        if (galleries.length === 0) {
            throw new Error('갤러리 데이터가 없습니다.');
        }
        
        // 첫 번째 갤러리의 이미지 URL들 확인
        if (galleries[0] && galleries[0].images) {
            console.log('첫 번째 갤러리 이미지들:', galleries[0].images);
        }
        
        currentIndex = 0;
        showCurrentGallery();
        hideLoading();
        
    } catch (error) {
        console.error('갤러리 로드 실패:', error);
        showError('갤러리를 불러오는 중 오류가 발생했습니다: ' + error.message);
    }
}

// 현재 갤러리 표시
function showCurrentGallery() {
    if (galleries.length === 0) return;
    
    const gallery = galleries[currentIndex];
    const displayTitle = convertFolderNameToDisplayTitle(gallery.title);
    galleryTitle.textContent = displayTitle;
    
    // 템플릿 설명 표시
    const description = templateDescriptions[displayTitle] || "템플릿 설명을 불러올 수 없습니다.";
    galleryDescription.textContent = description;
    
    // 이미지 그리드 생성 - 간단하고 확실한 방법
    imagesGrid.innerHTML = '';
    
    // 이미지들을 정확한 순서로 정렬: 상단(왼쪽) → 기본(가운데) → 하단(오른쪽)
    const sortedImages = [...gallery.images].sort((a, b) => {
        // 정확한 패턴 매칭 (언더스코어 기준)
        const getOrder = (filename) => {
            const normalizedFilename = filename.normalize('NFC');
            if (normalizedFilename.includes('_top')) return 0; // 왼쪽
            if (normalizedFilename.includes('_main')) return 1; // 가운데  
            if (normalizedFilename.includes('_bottom')) return 2; // 오른쪽
            return 3;
        };
        
        return getOrder(a.filename) - getOrder(b.filename);
    });
    

    
    // 정렬된 이미지로 currentImages 업데이트
    currentImages = sortedImages;
    
    sortedImages.forEach((image, index) => {
        const imageItem = createImageItem(image, index);
        imagesGrid.appendChild(imageItem);
    });
    
    // 네비게이션 상태 업데이트
    updateNavigationState();
    
    // 갤러리 내용 표시
    galleryContent.style.display = 'block';
    
    // 인접 이미지 미리로드
    loadAdjacentImages();
}

// 이미지 아이템 생성
function createImageItem(image, index) {
    const imageItem = document.createElement('div');
    
    // 이미지 타입에 따른 클래스 설정 - 간단하고 확실한 방법
    let positionClass = '';
    const filename = image.filename.normalize('NFC');
    
    // 정확한 패턴 매칭 (언더스코어 기준)
    if (filename.includes('_main')) {
        positionClass = 'center';
    } else if (filename.includes('_top')) {
        positionClass = 'left';
    } else if (filename.includes('_bottom')) {
        positionClass = 'right';
    }
    

    
    imageItem.className = `image-item ${positionClass}`;
    imageItem.addEventListener('click', () => openModal(index));
    
    const img = document.createElement('img');
    img.alt = image.filename;
    
    // 이미지 깜박거림 방지
    img.style.opacity = '0';
    img.style.transition = 'opacity 0.3s ease';
    img.style.width = '100%';
    img.style.height = 'auto';
    img.style.minHeight = '200px'; // 최소 높이 확보
    img.style.backgroundColor = '#f5f5f5'; // 로딩 중 배경색
    
    // 이미지 로드 완료 후 표시
    img.addEventListener('load', function() {
        this.style.opacity = '1';
    });
    
    // 이미지 로드 에러 처리
    img.addEventListener('error', function() {
        console.error('이미지 로드 실패:', image.url);
        
        // 간단한 플레이스홀더 생성 (SVG)
        const placeholder = 'data:image/svg+xml,' + encodeURIComponent(`
            <svg width="300" height="200" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#f0f0f0"/>
                <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-family="Arial" font-size="14" fill="#666">
                    이미지를 불러올 수 없습니다
                </text>
            </svg>
        `);
        
        this.src = placeholder;
        this.alt = '이미지를 불러올 수 없습니다';
        this.style.opacity = '1';
    });
    
    // src는 마지막에 설정
    img.src = image.url;
    
    const caption = document.createElement('div');
    caption.className = 'image-caption';
    
    const title = document.createElement('h3');
    title.textContent = getImageDisplayName(image.filename);
    
    const description = document.createElement('p');
    description.textContent = getImageDescription(image.filename);
    
    caption.appendChild(title);
    caption.appendChild(description);
    
    imageItem.appendChild(img);
    imageItem.appendChild(caption);
    
    return imageItem;
}

// 이미지 표시 이름 생성 - 정확한 패턴 매칭
function getImageDisplayName(filename) {
    const normalizedFilename = filename.normalize('NFC');
    if (normalizedFilename.includes('_main')) return '기본 템플릿';
    if (normalizedFilename.includes('_top')) return '상단 버전';
    if (normalizedFilename.includes('_bottom')) return '하단 버전';
    return filename.replace(/\.(jpg|jpeg|png|gif)$/i, '');
}

// 이미지 설명 생성 - 정확한 패턴 매칭
function getImageDescription(filename) {
    const normalizedFilename = filename.normalize('NFC');
    if (normalizedFilename.includes('_main')) return '기본 레이아웃 템플릿';
    if (normalizedFilename.includes('_top')) return '상단 텍스트 강조 버전';
    if (normalizedFilename.includes('_bottom')) return '하단 텍스트 강조 버전';
    return '숏츠 템플릿 이미지';
}

// 이전 갤러리 표시 (순환형)
function showPreviousGallery() {
    if (galleries.length === 0) return;
    
    if (currentIndex > 0) {
        currentIndex--;
    } else {
        // 첫 번째(1번)에서 이전으로 가면 마지막(10번)으로
        currentIndex = galleries.length - 1;
    }
    showCurrentGallery();
}

// 다음 갤러리 표시 (순환형)
function showNextGallery() {
    if (galleries.length === 0) return;
    
    if (currentIndex < galleries.length - 1) {
        currentIndex++;
    } else {
        // 마지막(10번)에서 다음으로 가면 첫 번째(1번)으로
        currentIndex = 0;
    }
    showCurrentGallery();
}

// 네비게이션 상태 업데이트 (순환형이므로 버튼 비활성화 없음)
function updateNavigationState() {
    // 순환형 네비게이션이므로 모든 버튼 활성화
    prevBtn.disabled = false;
    nextBtn.disabled = false;
    
    // 모바일 버튼도 활성화
    const prevBtnMobile = document.getElementById('prevBtnMobile');
    const nextBtnMobile = document.getElementById('nextBtnMobile');
    if (prevBtnMobile) prevBtnMobile.disabled = false;
    if (nextBtnMobile) nextBtnMobile.disabled = false;
    
    currentInfo.textContent = `${currentIndex + 1} / ${galleries.length}`;
}

// 모달 열기
function openModal(imageIndex) {
    if (currentImages.length === 0) return;
    
    currentModalImageIndex = imageIndex;
    showModalImage();
    imageModal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
}

// 모달 닫기
function closeModal() {
    imageModal.style.display = 'none';
    document.body.style.overflow = 'auto'; // 배경 스크롤 복원
}

// 모달 이미지 표시
function showModalImage() {
    if (currentImages.length === 0) return;
    
    const image = currentImages[currentModalImageIndex];
    modalImage.src = image.url;
    modalImage.alt = image.filename;
    
    // 모달 네비게이션 버튼 상태 업데이트
    modalPrev.style.display = currentModalImageIndex > 0 ? 'flex' : 'none';
    modalNext.style.display = currentModalImageIndex < currentImages.length - 1 ? 'flex' : 'none';
}

// 이전 모달 이미지
function showPreviousModalImage() {
    if (currentModalImageIndex > 0) {
        currentModalImageIndex--;
        showModalImage();
    }
}

// 다음 모달 이미지
function showNextModalImage() {
    if (currentModalImageIndex < currentImages.length - 1) {
        currentModalImageIndex++;
        showModalImage();
    }
}

// 로딩 표시
function showLoading() {
    loadingElement.style.display = 'flex';
    galleryContent.style.display = 'none';
    errorMessage.style.display = 'none';
}

// 로딩 숨김
function hideLoading() {
    loadingElement.style.display = 'none';
}

// 에러 표시
function showError(message) {
    loadingElement.style.display = 'none';
    galleryContent.style.display = 'none';
    errorMessage.style.display = 'block';
    document.getElementById('errorText').textContent = message;
}

// 터치/스와이프 지원 (모바일)
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
});

document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = touchEndX - touchStartX;
    
    if (Math.abs(swipeDistance) > swipeThreshold) {
        if (imageModal.style.display === 'flex') {
            // 모달이 열려있을 때
            if (swipeDistance > 0) {
                showPreviousModalImage();
            } else {
                showNextModalImage();
            }
        } else {
            // 갤러리 네비게이션 (이제 순환형으로 작동)
            if (swipeDistance > 0) {
                showPreviousGallery(); // 순환형: 1번→10번
            } else {
                showNextGallery(); // 순환형: 10번→1번
            }
        }
    }
}

// 페이지 가시성 변경 시 처리 (성능 최적화)
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // 페이지가 숨겨졌을 때 (탭 전환 등)
        closeModal();
    }
});

// 윈도우 리사이즈 처리
window.addEventListener('resize', function() {
    // 모달이 열려있을 때 리사이즈되면 모달 위치 재조정
    if (imageModal.style.display === 'flex') {
        showModalImage();
    }
});

// 이미지 미리로드 (성능 최적화)
function preloadImages() {
    const nextIndex = currentIndex + 1;
    const prevIndex = currentIndex - 1;
    
    // 다음 갤러리 이미지 미리로드
    if (nextIndex < galleries.length) {
        galleries[nextIndex].images.forEach(image => {
            const img = new Image();
            img.src = image.url;
        });
    }
    
    // 이전 갤러리 이미지 미리로드
    if (prevIndex >= 0) {
        galleries[prevIndex].images.forEach(image => {
            const img = new Image();
            img.src = image.url;
        });
    }
}

// 인접 이미지 미리로드 (갤러리 변경 시 호출)
function loadAdjacentImages() {
    // 인접 이미지 미리로드
    setTimeout(preloadImages, 1000);
}

// 현재 템플릿 다운로드
async function downloadCurrentTemplate() {
    // 다운로드 버튼 상태 관리를 위한 변수
    const originalText = downloadBtn.innerHTML;
    let safetyTimer = null;
    
    try {
        if (galleries.length === 0) {
            alert('다운로드할 템플릿이 없습니다.');
            return;
        }
        
        // 현재 갤러리의 템플릿 번호 추출 (1번~10번)
        const currentGallery = galleries[currentIndex];
        const folderName = currentGallery.folder;
        
        console.log('현재 갤러리:', currentGallery);
        console.log('폴더명:', folderName);
        
        // 폴더명에서 번호 추출 (예: "1번 기본 프리셋" -> 1)
        const templateNumber = parseInt(folderName.split('번')[0]);
        
        console.log('추출된 템플릿 번호:', templateNumber);
        
        if (isNaN(templateNumber) || templateNumber < 1 || templateNumber > 10) {
            alert('올바르지 않은 템플릿 번호입니다.');
            return;
        }
        
        // 다운로드 버튼 상태 변경
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = `
            <svg class="download-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
            다운로드 중...
        `;
        
        // 안전장치: 30초 후 자동으로 버튼 상태 복원
        safetyTimer = setTimeout(() => {
            console.log('타임아웃으로 인한 버튼 상태 복원');
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = originalText;
        }, 30000);
        
        console.log(`API 호출: /api/download-template/${templateNumber}`);
        
        // API 호출하여 파일 다운로드
        const response = await fetch(`/api/download-template/${templateNumber}`);
        
        console.log('API 응답 상태:', response.status, response.statusText);
        
        if (!response.ok) {
            let errorMessage = '다운로드에 실패했습니다.';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                console.warn('에러 데이터 파싱 실패:', e);
            }
            throw new Error(errorMessage);
        }
        
        // 파일 다운로드 처리
        const blob = await response.blob();
        console.log('Blob 크기:', blob.size);
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // 파일명 설정 (응답 헤더에서 가져오기)
        const contentDisposition = response.headers.get('content-disposition');
        let filename = `${templateNumber}_템플릿.zip`;
        
        console.log('Content-Disposition 헤더:', contentDisposition);
        
        if (contentDisposition) {
            // UTF-8 인코딩된 파일명 처리
            const utf8Match = contentDisposition.match(/filename\*=UTF-8''(.+)/);
            if (utf8Match) {
                try {
                    filename = decodeURIComponent(utf8Match[1]);
                    console.log('UTF-8 파일명:', filename);
                } catch (e) {
                    console.warn('파일명 디코딩 실패:', e);
                }
            } else {
                // 일반 파일명 처리
                const filenameMatch = contentDisposition.match(/filename=(.+)/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                    console.log('일반 파일명:', filename);
                }
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('다운로드 완료:', filename);
        
        // 성공 메시지
        alert(`${currentGallery.title} 템플릿이 성공적으로 다운로드되었습니다!`);
        
    } catch (error) {
        console.error('다운로드 오류:', error);
        alert(`다운로드 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        // 안전장치 타이머 정리
        if (safetyTimer) {
            clearTimeout(safetyTimer);
        }
        
        // 다운로드 버튼 상태 복원 (항상 실행됨)
        console.log('버튼 상태 복원');
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = originalText;
    }
}
