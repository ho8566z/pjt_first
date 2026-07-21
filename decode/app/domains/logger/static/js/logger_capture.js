// ===========================================================
// 이벤트 ID를 클릭했을 때 서버에서 이미지를 받아와 모달(팝업창)에 표시하고, 
// 닫기 버튼을 누르면 모달을 닫는 기능
// ===========================================================
document.querySelectorAll(".capture_btn").forEach(btn => {

    btn.addEventListener("click", async function(e){

        e.preventDefault();

        const eventId = this.dataset.eventId;

        const response = await fetch(`/event_log/detail/${eventId}`);

        const data = await response.json();

        if(data.result !== "success"){
            alert(data.message);
            return;
        }

        document.getElementById("captureImage").src = data.image;

        document.getElementById("captureModal").style.display = "flex";
    });
});


document.getElementById("closeModal").onclick = function(){

    document.getElementById("captureModal").style.display="none";
}


// ===========================================================
// 배경 클릭시 닫기
// ===========================================================
window.onclick = function(e){

    const modal = document.getElementById("captureModal");

    if(e.target === modal){

        modal.style.display = "none";

    }

}