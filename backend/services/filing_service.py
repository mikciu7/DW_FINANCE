"""
filing_service.py — pobiera tekst raportów 10-K/10-Q z EDGAR.
Strategia:
  1. Próbuje ustrukturyzowanych sekcji (TenK/TenQ obj) — działa dla nowszych raportów
  2. Fallback: surowy markdown dokumentu z ekstrakcją sekcji po nagłówkach
  3. Fallback ostateczny: pierwsze N znaków całego dokumentu
"""
import re
from edgar import Company, set_identity

set_identity("Mikolaj Ciuba ciubamikolaj22@gmail.com")

MAX_CHARS = 8_000

# Mapowanie sekcji → atrybuty obj() i wzorce nagłówków w surowym tekście
SECTION_CONFIG = {
    "mda": {
        "attrs":    ["management_discussion"],
        "patterns": [
            r"item\s*[27][\.\s]*\n+\s*#+\s*management",   # ITEM 2.\n\n## MANAGEMENT (10-Q/10-K)
            r"item\s*[27][\.\s]+management",               # ITEM 2. MANAGEMENT...
            r"management.{0,5}s discussion and analysis of financial",
        ],
        "end_patterns": [
            r"\nitem\s*[38][\.\s]",
            r"quantitative and qualitative disclosures about market risk",
        ],
        "label": "MD&A",
    },
    "business": {
        "attrs":    ["business"],
        "patterns": [
            r"item\s*1[\.\s]*\n+\s*#+\s*business",
            r"item\s*1[\.\s]+business\b",
        ],
        "end_patterns": [
            r"\nitem\s*1a[\.\s]",
            r"\nrisk factors",
        ],
        "label": "Business (Item 1)",
    },
    "risks": {
        "attrs":    ["risk_factors"],
        "patterns": [
            r"item\s*1a[\.\s]*\n+\s*#+\s*risk",
            r"item\s*1a[\.\s]+risk factor",
            r"\nrisk factors\n",
        ],
        "end_patterns": [
            r"\nitem\s*1b[\.\s]",
            r"\nitem\s*2[\.\s]",
        ],
        "label": "Risk Factors (Item 1A)",
    },
    "governance": {
        "attrs":    ["directors_officers_and_governance"],
        "patterns": [r"item\s*10[\.\s]"],
        "end_patterns": [r"\nitem\s*11[\.\s]", r"\nitem\s*15[\.\s]"],
        "label": "Governance (Item 10+)",
    },
}

ALIASES = {
    "risk_factors": "risks", "risk": "risks",
    "md&a": "mda", "management": "mda", "management_discussion": "mda",
}


def _clean(text: str) -> str:
    # Napraw rozstrzelony tekst (inline XBRL artifact)
    words = text.split(" ")
    single_char = sum(1 for w in words if len(w) == 1)
    if len(words) > 20 and single_char / len(words) > 0.5:
        text = re.sub(r"(?<=[A-Za-z0-9,;:]) (?=[A-Za-z0-9,;:])", "", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return text.strip()


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_dot = max(cut.rfind(". "), cut.rfind(".\n"))
    if last_dot > max_chars * 0.6:
        cut = cut[:last_dot + 1]
    return cut + f"\n\n[...skrócono — pokazano {len(cut)} z {len(text)} znaków]"


def _extract_section_from_text(full_text: str, cfg: dict) -> str | None:
    """Wytnij sekcję z surowego tekstu szukając nagłówków."""
    text_lower = full_text.lower()

    start_pos = None
    for pat in cfg["patterns"]:
        m = re.search(pat, text_lower, re.MULTILINE | re.IGNORECASE)
        if m:
            start_pos = m.start()
            break

    if start_pos is None:
        return None

    # Szukaj końca sekcji
    end_pos = len(full_text)
    search_from = start_pos + 100  # skip the header itself
    for pat in cfg["end_patterns"]:
        m = re.search(pat, text_lower[search_from:], re.MULTILINE | re.IGNORECASE)
        if m:
            candidate = search_from + m.start()
            if candidate < end_pos:
                end_pos = candidate

    extracted = full_text[start_pos:end_pos].strip()
    return extracted if len(extracted) > 200 else None


def get_filing_text(
    ticker: str,
    section: str = "mda",
    form: str = "10-K",
    max_chars: int = MAX_CHARS,
) -> dict:
    ticker = ticker.upper()
    key = ALIASES.get(section.lower(), section.lower())
    cfg = SECTION_CONFIG.get(key)

    if not cfg:
        return {"error": f"Nieznana sekcja '{section}'. Dostępne: mda, business, risks, governance"}

    try:
        company = Company(ticker)
        filings = company.get_filings(form=form)
        filing_list = list(filings)
        if not filing_list:
            return {"error": f"Brak zgłoszeń {form} dla {ticker}"}

        filing = filing_list[0]
        period = str(getattr(filing, "period_of_report", ""))
        filed  = str(getattr(filing, "filing_date", ""))

        raw_text = None

        # ── Strategia 1: ustrukturyzowane sekcje obj() ────────────────────────
        try:
            obj = filing.obj()
            for attr in cfg["attrs"]:
                val = getattr(obj, attr, None)
                if val:
                    raw_text = str(val)
                    break
        except Exception:
            pass

        # ── Strategia 2: markdown dokumentu + ekstrakcja po nagłówkach ────────
        if not raw_text:
            try:
                md = filing.markdown()
                if md:
                    raw_text = _extract_section_from_text(md, cfg)
            except Exception:
                pass

        # ── Strategia 3: surowy tekst dokumentu ───────────────────────────────
        if not raw_text:
            try:
                txt = str(filing.text) if hasattr(filing, "text") else None
                if txt:
                    raw_text = _extract_section_from_text(txt, cfg)
            except Exception:
                pass

        # ── Fallback: pierwsze N znaków całego dokumentu ──────────────────────
        if not raw_text:
            try:
                md = filing.markdown()
                raw_text = md[:max_chars * 3] if md else None
            except Exception:
                pass

        if not raw_text:
            return {
                "error": "Nie udało się pobrać treści raportu.",
                "ticker": ticker, "form": form, "period": period,
            }

        cleaned = _clean(raw_text)
        total_chars = len(cleaned)
        truncated = total_chars > max_chars
        text = _truncate(cleaned, max_chars)

        result = {
            "ticker":      ticker,
            "form":        form,
            "period":      period,
            "filed":       filed,
            "section":     cfg["label"],
            "text":        text,
            "total_chars": total_chars,
            "shown_chars": min(max_chars, total_chars),
            "truncated":   truncated,
        }
        if truncated:
            remaining = total_chars - max_chars
            result["truncation_note"] = (
                f"Tekst skrócony — pokazano {min(max_chars, total_chars):,} z {total_chars:,} znaków "
                f"(~{remaining // 4:,} tokenów pozostało). "
                f"Aby przeczytać więcej, poproś użytkownika i wywołaj ponownie z max_chars={total_chars}."
            )
        return result

    except Exception as e:
        return {"error": str(e)}