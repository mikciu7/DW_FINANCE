"""
filing_service.py — pobiera tekstowe sekcje raportów 10-K/10-Q z EDGAR.
Uwaga: każde wywołanie robi request do SEC EDGAR (~3-10 sek, zużywa tokeny LLM).
"""
import re
import os
import sys

from edgar import Company, set_identity

set_identity("Mikolaj Ciuba ciubamikolaj22@gmail.com")

SECTIONS_10K = {
    "business": "business",
    "risks":    "risk_factors",
    "mda":      "management_discussion",
    "governance": "directors_officers_and_governance",
}

SECTION_ALIASES = {
    "risk_factors": "risks",
    "risk":         "risks",
    "md&a":         "mda",
    "management":   "mda",
    "management_discussion": "mda",
}

MAX_CHARS = 8_000


def _clean(text: str) -> str:
    words = text.split(" ")
    single_char = sum(1 for w in words if len(w) == 1)
    if len(words) > 20 and single_char / len(words) > 0.5:
        text = re.sub(r"(?<=[A-Za-z0-9,;:]) (?=[A-Za-z0-9,;:])", "", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("�", "'")
    return text.strip()


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_dot = max(cut.rfind(". "), cut.rfind(".\n"))
    if last_dot > max_chars * 0.6:
        cut = cut[:last_dot + 1]
    return cut + f"\n\n[...skrócono — pokazano {len(cut)} z {len(text)} znaków]"


def get_filing_text(
    ticker: str,
    section: str = "mda",
    form: str = "10-K",
    max_chars: int = MAX_CHARS,
) -> dict:
    """
    Pobiera tekst wybranej sekcji z najnowszego raportu 10-K lub 10-Q.

    section: 'mda' | 'business' | 'risks' | 'governance'
    form:    '10-K' | '10-Q'
    """
    ticker = ticker.upper()
    key = SECTION_ALIASES.get(section.lower(), section.lower())

    try:
        company = Company(ticker)
        filings = company.get_filings(form=form)
        filing_list = list(filings)
        if not filing_list:
            return {"error": f"Brak zgłoszeń {form} dla {ticker}"}

        filing = filing_list[0]
        period = str(getattr(filing, "period_of_report", ""))
        filed  = str(getattr(filing, "filing_date", ""))

        obj = filing.obj()

        attr = SECTIONS_10K.get(key, key)
        raw = getattr(obj, attr, None)

        if not raw:
            available = [k for k, a in SECTIONS_10K.items()
                         if getattr(obj, a, None)]
            return {
                "error": f"Sekcja '{section}' niedostępna w tym raporcie.",
                "available_sections": available,
                "period": period,
            }

        cleaned = _clean(str(raw))
        total_chars = len(cleaned)
        truncated = total_chars > max_chars
        text = _truncate(cleaned, max_chars)

        result = {
            "ticker":       ticker,
            "form":         form,
            "period":       period,
            "filed":        filed,
            "section":      section,
            "text":         text,
            "total_chars":  total_chars,
            "shown_chars":  min(max_chars, total_chars),
            "truncated":    truncated,
        }
        if truncated:
            remaining = total_chars - max_chars
            approx_tokens = remaining // 4
            result["truncation_note"] = (
                f"Tekst skrócony — pokazano {min(max_chars, total_chars):,} z {total_chars:,} znaków. "
                f"Pozostało ~{remaining:,} znaków (~{approx_tokens:,} tokenów). "
                f"Aby przeczytać więcej, poproś użytkownika o zgodę i wywołaj ponownie z max_chars={total_chars}."
            )
        return result

    except Exception as e:
        return {"error": str(e)}