"""Selo PAdES com pyHanko e certificado autoassinado de teste; valida e testa adulteração."""

import datetime
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko_certvalidator import ValidationContext


def make_cert():
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Teste SGP-P&D"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Selo de teste do SGP-P&D"),
        ]
    )
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(True, True, False, False, False, True, False, False, False), critical=True
        )
        .sign(key, hashes.SHA256())
    )
    p12 = pkcs12.serialize_key_and_certificates(
        b"selo", key, cert, None, serialization.BestAvailableEncryption(b"senha-de-teste")
    )
    open("selo-teste.p12", "wb").write(p12)
    open("selo-teste.pem", "wb").write(cert.public_bytes(serialization.Encoding.PEM))


def seal(src, dst):
    signer = signers.SimpleSigner.load_pkcs12("selo-teste.p12", passphrase=b"senha-de-teste")
    meta = signers.PdfSignatureMetadata(
        field_name="SeloSGP",
        subfilter=fields.SigSeedSubFilter.PADES,
        reason="Documento oficial gerado pelo SGP-P&D",
        location="Intranet",
    )
    with open(src, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)
        with open(dst, "wb") as outf:
            signers.sign_pdf(writer, meta, signer=signer, output=outf)


def validate(path):
    from pyhanko.keys import load_cert_from_pemder

    vc = ValidationContext(trust_roots=[load_cert_from_pemder("selo-teste.pem")])
    with open(path, "rb") as f:
        reader = PdfFileReader(f)
        sig = reader.embedded_signatures[0]
        status = validate_pdf_signature(sig, vc)
        return status.intact, status.valid, status.bottom_line


def main():
    make_cert()
    for src in sys.argv[1:]:
        dst = src.replace(".pdf", "-selado.pdf")
        seal(src, dst)
        print(dst, "selado; (íntegro, válido, conclusão) =", validate(dst))
        data = bytearray(open(dst, "rb").read())
        pos = len(data) // 3
        data[pos] = (data[pos] + 1) % 256
        bad = dst.replace(".pdf", "-adulterado.pdf")
        open(bad, "wb").write(bytes(data))
        try:
            print(bad, "(íntegro, válido, conclusão) =", validate(bad))
        except Exception as exc:  # noqa: BLE001
            print(bad, "falha na validação:", type(exc).__name__, exc)


if __name__ == "__main__":
    main()
