import json

import pytest

from reviews.labeling import (
    CATEGORIES,
    PROMPT_VERSION,
    LabelParseError,
    build_prompt,
    parse_label,
)


def cevap(*kategoriler: tuple[str, str], dil: str = "en") -> str:
    return json.dumps({"dil": dil, "kategoriler": [{"ad": a, "duygu": d} for a, d in kategoriler]})


def test_gecerli_cevap_ayristirilir():
    sonuc = parse_label(cevap(("hiz", "olumsuz"), ("cevap_kalitesi", "olumlu")))
    assert sonuc.language == "en"
    assert [(c.name, c.sentiment) for c in sonuc.categories] == [
        ("hiz", "olumsuz"),
        ("cevap_kalitesi", "olumlu"),
    ]


def test_kod_blogu_icindeki_json_ayristirilir():
    ham = "```json\n" + cevap(("arayuz", "notr"), dil="tr") + "\n```"
    assert parse_label(ham).categories[0].name == "arayuz"


@pytest.mark.parametrize(
    "ham",
    [
        "bu json degil",
        cevap(),
        cevap(("uydurma_kategori", "olumsuz")),
        cevap(("hiz", "kizgin")),
        cevap(
            ("hiz", "olumsuz"),
            ("arayuz", "olumsuz"),
            ("gorsel_uretimi", "olumsuz"),
            ("hesap_ve_destek", "olumsuz"),
        ),
        cevap(("diger", "olumsuz"), ("hiz", "olumsuz")),
        cevap(("hiz", "olumsuz"), ("hiz", "olumlu")),
    ],
)
def test_kurallara_uymayan_cevap_reddedilir(ham):
    with pytest.raises(LabelParseError):
        parse_label(ham)


def test_dil_yoksa_bilinmiyor_olur():
    ham = json.dumps({"kategoriler": [{"ad": "siniflandirilamaz", "duygu": "olumlu"}]})
    assert parse_label(ham).language == "bilinmiyor"


def test_prompt_yorumu_ve_tum_kategorileri_icerir():
    prompt = build_prompt("uygulama çok yavaş {süslü parantez}")
    assert "uygulama çok yavaş {süslü parantez}" in prompt
    for ad in CATEGORIES:
        assert ad in prompt


def test_prompt_surumu_12_karakter():
    assert len(PROMPT_VERSION) == 12
