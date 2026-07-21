// ===========================================================
// logger_alarm.js
// 이벤트 로그 실시간 알림(SSE)
// ===========================================================

// ===========================================================
// 각각의 html에서 '로그 알림'을 받기 위한 방법 -> 각각 html에 script를 넣기
// <script src="{{ url_for('event_log.static', filename='js/logger_alarm.js') }}"></script>
// ===========================================================

// ===========================================================
// 1. 전역 변수
// ===========================================================

// SSE 연결
window.eventSource = window.eventSource || null;

// 알림음
const audio = new Audio("/static/audio/ding.wav");

// 마지막으로 받은 로그 ID
let lastLogId = null;


// ===========================================================
// 2. 페이지 최초 로드
// ===========================================================
window.addEventListener("load", function () {

    const firstEventId = document.querySelector(".event_id");

    if (firstEventId) {
        lastLogId = firstEventId.innerText.trim();
    }
    if(!window.eventSource){
        connectSSE();
    }
});


// ===========================================================
// 3. SSE 연결
// ===========================================================
function connectSSE() {

    // 이미 SSE 연결이 존재하면 생성하지 않음
    if(window.eventSource) {
        console.log("이미 SSE 연결 존재");
        return;
    }

    // SSE 연결 생성
    window.eventSource =
        new EventSource(
            "/event_log/stream_log"
        );

    // SSE 데이터 수신
    window.eventSource.onmessage = async function (event) {

        // 알림음
        audio.play().catch(function (err) {
            console.log(
                "알림음 재생 실패",
                err
            );
        });

        // Toast
        showToast(
            "새 로그가 발생했습니다."
        );

        // 마지막 로그 확인
        if(lastLogId === null) {
            return;
        }

        // 새 로그 요청
        const response =
            await fetch(
                `/event_log/new?after=${lastLogId}`
            );

        if(!response.ok) {
            return;
        }

        const logs = await response.json();

        // 화면 추가
        logs.forEach(function(log) {

            addLogRow(log);

            increaseBadge();
        });

        // 마지막 ID 갱신
        if(logs.length > 0) {
            lastLogId =
                logs[logs.length - 1].ID;
        }
    };
    
    // SSE 오류 처리
    window.eventSource.onerror = function(error) {
        console.log(
            "SSE 연결 오류",
            error
        );
        window.eventSource.close();

        window.eventSource = null;
    };
}


// ===========================================================
// 4. 로그 행 추가
// ===========================================================
function addLogRow(log) {

    const tbody = document.getElementById("event_log_body");

    if (!tbody) {
        return;
    }

    // 이미 존재하면 추가하지 않음
    if (document.querySelector(`input[value="${log.ID}"]`)) {
        return;
    }

    const tr = document.createElement("tr");

    tr.classList.add("new_log");

    tr.innerHTML = `
        <td>
            <input class="log_check" type="checkbox" value="${log.ID}">
        </td>

        <td></td>

        <td class="event_id">${log.ID}</td>
        <td>${log.REG_DATE}</td>
        <td>${log.latitude}</td>
        <td>${log.longitude}</td>
        <td>${log.TARGET_ID}</td>

        <td>
            <span class="unchecked">읽지않음</span>
        </td>
    `;

    tbody.prepend(tr);

    refreshRowNumber();

    setTimeout(function () {
        tr.classList.remove("new_log");
    }, 3000);
}


// ===========================================================
// 5. Toast 출력
// ===========================================================
function showToast(text) {

    const container =  document.getElementById("toast_container");

    if (!container) {
        return;
    }

    const div = document.createElement("div");

    div.className = "toast";

    div.innerText = text;

    container.appendChild(div);

    setTimeout(function () {
        div.remove();
    }, 3000);
}


// ===========================================================
// 6. Badge 증가
// ===========================================================
function increaseBadge() {

    const badge = document.getElementById("log_badge");

    if (!badge) {
        return;
    }

    badge.innerText = Number(badge.innerText) + 1;
}


// ===========================================================
// 7. 페이지 종료 시 SSE 연결 종료
// ===========================================================
window.addEventListener("beforeunload", function () {

    if (window.eventSource) {
        window.eventSource.close();

        window.eventSource = null;
    }
});