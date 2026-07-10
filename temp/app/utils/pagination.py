import math

def paginate(accounts, page, per_page):
    total_count = len(accounts)
    total_pages = math.ceil(total_count / per_page)

    if total_pages == 0:
        total_pages = 1

    start = (page - 1) * per_page
    end = start + per_page

    return (accounts[start:end], total_pages)