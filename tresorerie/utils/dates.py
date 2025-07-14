from datetime import datetime, timedelta, date

def get_week_range(offset_weeks=0):
    # offset_weeks=0 for current week, -1 for last week... 
    today = datetime.today().date()
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset_weeks)
    end = start + timedelta(days=6)
    return start, end

def get_period_range(period):
    today = date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday())
        labels = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        return start, start + timedelta(days=6), labels
    elif period == "month":
        start = today.replace(day=1)
        labels = [f"Semaine {i+1}" for i in range(4)]
        return start, start + timedelta(days=30), labels
    elif period == "quarter":
        start_month = 3 * ((today.month - 1) // 3) + 1
        start = date(today.year, start_month, 1)
        labels = ["Mois 1", "Mois 2", "Mois 3"]
        return start, start + timedelta(days=89), labels
    elif period == "year":
        start = date(today.year, 1, 1)
        labels = ["T1", "T2", "T3", "T4"]
        return start, date(today.year, 12, 31), labels
    else:
        return get_period_range("week")

