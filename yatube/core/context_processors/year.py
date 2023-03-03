from datetime import datetime


def year(request):
    data = datetime.today()
    """Добавляет переменную с текущим годом."""
    return {
        "year": data.year,
    }
