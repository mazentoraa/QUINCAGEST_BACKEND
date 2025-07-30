from datetime import datetime, timedelta, date
from calendar import monthrange

def get_week_range(offset_weeks=0):
    # offset_weeks=0 for current week, -1 for last week... 
    today = datetime.today().date()
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset_weeks)
    end = start + timedelta(days=6)
    return start, end

from datetime import datetime, timedelta, date

def get_week_range(offset_weeks=0):
    today = datetime.today().date()
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset_weeks)
    end = start + timedelta(days=6)
    return start, end

def get_period_range(period):
    today = date.today()

    if period == "week":
        labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        def range_func(offset=0):
            start = today - timedelta(days=today.weekday()) - timedelta(weeks=offset)
            end = start + timedelta(days=6)
            return start, end
        return range_func, labels

    elif period == "month":
        labels = [f"Semaine {i+1}" for i in range(4)]
        def range_func(offset=0):
            year = today.year
            month = today.month - offset
            while month <= 0:
                month += 12
                year -= 1
            start = date(year, month, 1)
            last_day = monthrange(year, month)[1]
            end = date(year, month, last_day)
            return start, end
        return range_func, labels

    elif period == "quarter":
        labels = ["Mois 1", "Mois 2", "Mois 3"]
        def range_func(offset=0):
            current_quarter = (today.month - 1) // 3
            quarter_start_month = 3 * (current_quarter - offset) + 1
            year = today.year
            while quarter_start_month <= 0:
                quarter_start_month += 12
                year -= 1
            start = date(year, quarter_start_month, 1)
            end_month = quarter_start_month + 2
            last_day = monthrange(year, end_month)[1]
            end = date(year, end_month, last_day)
            return start, end
        return range_func, labels

    elif period == "year":
        labels = ["T1", "T2", "T3", "T4"]
        def range_func(offset=0):
            year = today.year - offset
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            return start, end
        return range_func, labels

    return get_period_range("week")