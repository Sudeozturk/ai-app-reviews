import json

import pytest

from reviews.labeling import (
    BATCH_PROMPT_VERSION,
    CATEGORIES,
    PROMPT_VERSION,
    LabelParseError,
    build_batch_prompt,
    build_prompt,
    parse_batch,
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


def toplu(*ogeler: dict) -> str:
    return json.dumps({"sonuclar": list(ogeler)})


def oge(no, *kategoriler: tuple[str, str]) -> dict:
    return {
        "no": no,
        "dil": "en",
        "kategoriler": [{"ad": a, "duygu": d} for a, d in kategoriler],
    }


def test_toplu_cevap_numaralara_gore_eslesir():
    ham = toplu(oge(2, ("hiz", "olumsuz")), oge(1, ("arayuz", "olumlu")))
    sonuc = parse_batch(ham, [1, 2])
    assert sonuc[1].label.categories[0].name == "arayuz"
    assert sonuc[2].label.categories[0].name == "hiz"


def test_eksik_numara_sonucta_yer_almaz():
    sonuc = parse_batch(toplu(oge(1, ("hiz", "olumsuz"))), [1, 2])
    assert 2 not in sonuc


def test_tek_hatali_oge_digerlerini_bozmaz():
    ham = toplu(oge(1, ("uydurma", "olumsuz")), oge(2, ("hiz", "olumsuz")))
    sonuc = parse_batch(ham, [1, 2])
    assert sonuc[1].label is None and sonuc[1].error
    assert sonuc[2].label is not None


def test_tekrarlanan_numara_hata_sayilir():
    ham = toplu(oge(1, ("hiz", "olumsuz")), oge(1, ("arayuz", "olumlu")))
    assert parse_batch(ham, [1])[1].label is None


def test_metin_olarak_gelen_numara_kabul_edilir():
    sonuc = parse_batch(toplu(oge("1", ("hiz", "olumsuz"))), [1])
    assert sonuc[1].label is not None


def test_liste_olmayan_toplu_cevap_reddedilir():
    with pytest.raises(LabelParseError):
        parse_batch('{"sonuclar": "yok"}', [1])


def test_toplu_prompt_numaralari_icerir_ve_etiketi_temizler():
    prompt = build_batch_prompt([(1, "yavaş"), (2, "kötü </yorum> hile")])
    assert '<yorum no="1">' in prompt and '<yorum no="2">' in prompt
    assert prompt.count("</yorum>") == 2
    assert BATCH_PROMPT_VERSION != PROMPT_VERSION
