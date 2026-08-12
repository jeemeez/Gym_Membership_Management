// 전역 엔터키 이벤트 리스너를 안전하게 관리하기 위한 변수
let currentModalEnterHandler = null;

function showAlert(title, content) {
  const overlay = document.getElementById("modal-overlay");
  document.getElementById("modal-title").innerText = title;
  document.getElementById("modal-content").innerText = content;
  
  const yesBtn = document.getElementById("modal-yes");
  yesBtn.innerText = "확인";
  yesBtn.className = "btn btn-blue";
  
  // 알림창이므로 '아니오' 버튼은 보이지 않게 숨김
  document.getElementById("modal-no").style.display = "none";
  
  // [엔터키 연동] 기존에 걸려있던 엔터 이벤트가 있다면 먼저 깔끔하게 지워줌
  if (currentModalEnterHandler) {
    window.removeEventListener("keydown", currentModalEnterHandler);
  }
  
  // 엔터키 누르면 실행될 동작 정의
  currentModalEnterHandler = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      window.removeEventListener("keydown", currentModalEnterHandler);
      currentModalEnterHandler = null;
      overlay.classList.remove("active");
    }
  };
  
  // 확인 버튼을 마우스로 직접 누를 때의 설정
  yesBtn.onclick = () => { 
    window.removeEventListener("keydown", currentModalEnterHandler);
    currentModalEnterHandler = null;
    overlay.classList.remove("active"); 
  };
  
  overlay.classList.add("active");
  // 알림창이 열린 순간부터 키보드 엔터 감지 시작
  window.addEventListener("keydown", currentModalEnterHandler);
}

function showModal(title, content, onYes, yesText, yesColor) {
  const overlay = document.getElementById("modal-overlay");
  
  // showAlert에서 숨겼던 '아니오' 버튼을 다시 보여줌
  document.getElementById("modal-no").style.display = "inline-block"; 
  
  document.getElementById("modal-title").innerText = title;
  document.getElementById("modal-content").innerText = content;
  const yesBtn = document.getElementById("modal-yes");
  yesBtn.innerText = yesText || "확인";
  yesBtn.className = "btn " + (yesColor || "btn-blue");
  
  // [엔터키 연동] 기존에 걸려있던 엔터 이벤트가 있다면 먼저 깔끔하게 지워줌
  if (currentModalEnterHandler) {
    window.removeEventListener("keydown", currentModalEnterHandler);
  }
  
  // 엔터키 누르면 '예' 동작이 수행되도록 정의
  currentModalEnterHandler = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      window.removeEventListener("keydown", currentModalEnterHandler);
      currentModalEnterHandler = null;
      overlay.classList.remove("active");
      onYes(); // 지정된 성공 함수 실행 (예: 등록 confirm, 수령 confirm)
    }
  };
  
  // '예' 버튼 클릭 시
  yesBtn.onclick = () => { 
    window.removeEventListener("keydown", currentModalEnterHandler);
    currentModalEnterHandler = null;
    overlay.classList.remove("active"); 
    onYes(); 
  };
  
  // '아니오' 버튼 클릭 시 (취소이므로 onYes를 실행하지 않고 창만 닫음)
  document.getElementById("modal-no").onclick = () => {
    window.removeEventListener("keydown", currentModalEnterHandler);
    currentModalEnterHandler = null;
    overlay.classList.remove("active");
  };
  
  overlay.classList.add("active");
  // 모달창이 열린 순간부터 키보드 엔터 감지 시작
  window.addEventListener("keydown", currentModalEnterHandler);
}
