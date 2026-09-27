from rest_framework import views, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.licensing.tiers import require_tier, LicenseTier, check_tier_access
from ..models import SystemBranding
from .serializers import SystemBrandingSerializer

class BrandingSettingsView(views.APIView):
    """
    Настройки брендинга (только для админов панели). Чтение доступно всем
    админам (чтобы показать текущий статус на тарифах ниже Corporate),
    но реально применить кастомный брендинг может только Corporate — см.
    @require_tier ниже и одноимённую проверку в GET.
    """
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAdminUser]

    def get(self, request):
        branding = SystemBranding.load()
        serializer = SystemBrandingSerializer(branding, context={"request": request})
        data = serializer.data

        # Если тариф не Corporate, скрываем и кастомный брендинг, и рекламный блок —
        # обе фичи Corporate-эксклюзивные по ТЗ.
        if not check_tier_access(LicenseTier.CORPORATE):
            data["app_name"] = "FluxCore"
            data["logo_url"] = None
            data["favicon_url"] = None
            data["custom_css"] = ""
            data["ad_enabled"] = False
            data["ad_title"] = ""
            data["ad_content"] = ""
            data["ad_link"] = ""

        return Response(data)

    @require_tier(LicenseTier.CORPORATE)
    def post(self, request):
        branding = SystemBranding.load()
        serializer = SystemBrandingSerializer(branding, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
