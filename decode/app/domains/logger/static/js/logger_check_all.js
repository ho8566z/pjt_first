// ===========================================================
// 전체 선택 -체크 박스
// ===========================================================
const checkAll = document.getElementById("check_all");

if (checkAll) {

    checkAll.addEventListener("change", function () {

        document.querySelectorAll(".log_check").forEach(function (checkbox) {

            if (!checkbox.disabled) {
                checkbox.checked = checkAll.checked;
            }
        });
    });
}


// ===========================================================
// 번호 다시 매기기
// ===========================================================
function refreshRowNumber() {

    const rows = document.querySelectorAll(".log_table tbody tr");

    rows.forEach(function(row, index) {
        row.cells[1].textContent = index + 1;
    });
}