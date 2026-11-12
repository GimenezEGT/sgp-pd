"""Selo PAdES do PDF oficial com o certificado da empresa (pyHanko; research R3).

O certificado (PKCS#12) e a senha vêm só de variáveis de ambiente. Sem certificado legível e
válido na data, o PDF oficial não é emitido (FR-013).
"""

import io
import logging
from datetime import UTC, datetime

from django.conf import settings
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers

FIELD_NAME = "SeloSGP"
REASON = "Documento oficial gerado pelo SGP-P&D"
LOCATION = "Intranet"
logger = logging.getLogger(__name__)


class SealError(Exception):
    """O selo não pôde ser aplicado; a mensagem é mostrada a quem pediu o documento."""


def load_signer():
    path = settings.DOCUMENT_SEAL_PKCS12
    if not path:
        raise SealError(
            "O certificado do selo não está configurado; o PDF oficial não pode ser emitido. "
            "Avise a TI."
        )
    password = (settings.DOCUMENT_SEAL_PASSWORD or "").encode()
    try:
        signer = signers.SimpleSigner.load_pkcs12(path, passphrase=password or None)
    except Exception:  # noqa: BLE001 - qualquer falha de leitura vira a mesma mensagem
        logger.exception("Falha ao ler o certificado do selo")
        signer = None
    if signer is None:
        raise SealError(
            "Não foi possível ler o certificado do selo; o PDF oficial não pode ser emitido. "
            "Avise a TI."
        )
    certificate = signer.signing_cert
    now = datetime.now(UTC)
    if not (certificate.not_valid_before <= now <= certificate.not_valid_after):
        raise SealError(
            "O certificado do selo está fora da validade; o PDF oficial não pode ser emitido. "
            "Avise a TI."
        )
    return signer


def seal(pdf: bytes) -> bytes:
    signer = load_signer()
    metadata = signers.PdfSignatureMetadata(
        field_name=FIELD_NAME,
        subfilter=fields.SigSeedSubFilter.PADES,
        md_algorithm="sha256",
        reason=REASON,
        location=LOCATION,
    )
    writer = IncrementalPdfFileWriter(io.BytesIO(pdf))
    output = io.BytesIO()
    signers.sign_pdf(writer, metadata, signer=signer, output=output)
    return output.getvalue()


def certificate_subject() -> str:
    """Titular do certificado configurado (exibido na consulta do código de verificação)."""
    return load_signer().signing_cert.subject.human_friendly


def validate(pdf: bytes, trust_roots: list) -> dict:
    """Valida o selo contra as raízes informadas (usado nos testes e na validação do sistema)."""
    from pyhanko.sign.validation import validate_pdf_signature
    from pyhanko_certvalidator import ValidationContext

    reader = PdfFileReader(io.BytesIO(pdf))
    signature = reader.embedded_signatures[0]
    status = validate_pdf_signature(signature, ValidationContext(trust_roots=trust_roots))
    return {"intact": status.intact, "valid": status.valid, "trusted": status.bottom_line}
