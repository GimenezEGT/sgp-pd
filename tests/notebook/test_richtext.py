"""Texto formatado do caderno: lista branca no servidor (contrato conteudo-assinado.md)."""

import pytest

from sgp.notebook import richtext

pytestmark = pytest.mark.req("008:FR-001")


def test_formatacao_permitida_passa_sem_mudar():
    html = (
        "<p><strong>Tampão</strong> H<sub>2</sub>O a 10<sup>6</sup> UFC</p><ul><li>item</li></ul>"
    )
    assert richtext.sanitize(html) == html


def test_script_estilo_eventos_classes_e_links_sao_removidos():
    dirty = (
        '<p onclick="roubar()" style="color:red" class="x">texto</p>'
        "<script>alert(1)</script><style>p{}</style>"
        '<a href="http://externo.example/">site</a><!-- comentário -->'
        '<iframe src="http://externo.example/"></iframe>'
    )
    clean = richtext.sanitize(dirty)
    assert clean == "<p>texto</p>site"


def test_imagem_so_de_anexo_da_propria_entrada():
    html = (
        '<p><img src="/arquivos/7/" alt="foto"></p>'
        '<p><img src="/arquivos/8/" alt="outra entrada"></p>'
        '<p><img src="http://externo.example/x.png"></p>'
        '<p><img src="data:image/png;base64,AAAA"></p>'
    )
    clean = richtext.sanitize(html, image_ids={7})
    assert '<img src="/arquivos/7/" alt="foto">' in clean
    assert "/arquivos/8/" not in clean and "externo" not in clean and "data:" not in clean
    assert clean.count("<img") == 1
    assert richtext.image_ids(clean) == {7}


def test_tabela_com_mesclagem_valida():
    html = '<table><tbody><tr><td colspan="2">a</td><td rowspan="99">b</td></tr></tbody></table>'
    clean = richtext.sanitize(html)
    assert 'colspan="2"' in clean and "rowspan" not in clean


def test_texto_simples_vira_paragrafos_e_lista():
    clean = richtext.sanitize("Primeira linha\nsegunda linha\n\n- item 1\n- item 2")
    assert clean == "<p>Primeira linha<br>segunda linha</p><ul><li>item 1</li><li>item 2</li></ul>"
    assert richtext.sanitize("a < b e c > d") == "<p>a &lt; b e c &gt; d</p>"


def test_div_do_navegador_vira_paragrafo():
    assert (
        richtext.sanitize("<div>linha 1</div><div>linha 2</div>") == "<p>linha 1</p><p>linha 2</p>"
    )


def test_texto_puro_e_sem_acentos_para_a_busca():
    assert (
        richtext.plain_text("<p>Solução&nbsp;<b>ácida</b></p><p>pH 7</p>") == "Solução ácida pH 7"
    )
    assert richtext.fold("Solução Ácida") == "solucao acida"
    assert richtext.excerpt("<p>" + "a" * 300 + "</p>", 10).endswith(chr(0x2026))
