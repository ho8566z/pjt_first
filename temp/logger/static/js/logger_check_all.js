// ===== 전체 선택 =====
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