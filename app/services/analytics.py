from datetime import date

from fastapi import HTTPException


def get_month_date_range(year: int, month: int) -> tuple[date, date]:
    if not 1 <= year <= 9999:
        raise HTTPException(
            status_code=422,
            detail="Year must be between 1 and 9999",
        )

    if not 1 <= month <= 12:
        raise HTTPException(
            status_code=422,
            detail="Month must be between 1 and 12",
        )

    if year == 9999 and month == 12:
        raise HTTPException(
            status_code=422,
            detail="Year and month are outside the supported range",
        )

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return start_date, end_date