// ===== 선택 읽음 처리 =====
const btnSelected = document.getElementById("btn_selected");

if (btnSelected) {

    btnSelected.addEventListener("click", async function () {

        const ids = [];

        document.querySelectorAll(".log_check:checked").forEach(function (checkbox) {
            ids.push(checkbox.value);
        });

        if (ids.length === 0) {
            alert("선택된 이벤트가 없습니다.");
            return;
        }

        const response = await fetch("/event_log/checked_event_log", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                ids: ids,
                viewer_id: "user1"
            })
        });

        if (response.ok) {
            location.reload();
        } else {
            alert("읽음 처리에 실패했습니다.");
        }

    });

}