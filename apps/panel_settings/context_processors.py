"""
Context processor, добавляющий активную тему в контекст каждого шаблона,
чтобы base.html мог отрендерить переопределение CSS-переменных.
"""
from .models import Theme


def active_theme(request):
    theme = Theme.objects.filter(is_active=True).first()
    return {"active_theme": theme}
