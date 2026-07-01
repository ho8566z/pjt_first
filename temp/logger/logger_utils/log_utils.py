from flask import send_file
import pandas as pd
import io


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


def download_excel_file(output, file_name):

    return send_file(
        output,
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment = True,
        download_name = file_name
    )
