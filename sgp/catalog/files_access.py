"""Política de leitura dos arquivos dos cadastros (contrato rotas-ui.md, rota /arquivos/<id>/).

Certificado de análise de insumo: qualquer perfil (insumos valem para a empresa toda).
Planilha de importação: só os editores dos cadastros.
"""

from sgp.accounts.profiles import active_profiles

from .models import ImportBatch, Material
from .permissions import can_edit_catalog


def catalog_file_policy(user, stored) -> bool:
    if Material.objects.filter(certificate=stored).exists():
        return bool(active_profiles(user))
    if ImportBatch.objects.filter(source_file=stored).exists():
        return can_edit_catalog(user)
    return False
