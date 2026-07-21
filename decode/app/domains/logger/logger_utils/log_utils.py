from flask import send_file
import pandas as pd
import io


# ===========================================================
# json(db)의 로그 리스트를 엑셀 파일로 변환해 메모리에 생성
# ===========================================================
def create_excel_file(cleaned_data, sheet_name):

    data_frame = pd.DataFrame(cleaned_data)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data_frame.to_excel(
            writer,
            index = False,
            sheet_name = sheet_name
        )

    output.seek(0)

    return output


# ===========================================================
# 만들어 놓은 엑셀 파일 로컬로 다운로드
# ===========================================================
def download_excel_file(output, file_name):

    return send_file(
        output,
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment = True,
        download_name = file_name
    )