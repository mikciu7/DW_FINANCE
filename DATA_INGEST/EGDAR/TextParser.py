from io import StringIO
import re
import pandas as pd
from bs4 import BeautifulSoup
import os
import pandas as pd
import html


class TextParser():

    def __init__(self):
        self._num_re = re.compile(r"""
            ^\s*
            (?P<label>.*?)
            \s+\$?\s*(?P<v1>[\(\)\d,.\-]+)            # pierwsza liczba
            (?:\s+\$?\s*(?P<v2>[\(\)\d,.\-]+))?       # opcjonalnie druga
            \s*$
        """, re.VERBOSE)

        self._MONTH_RE = re.compile(
            r'\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|'
            r'jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|'
            r'dec(?:ember)?)\b', re.I
        )
        
    def _to_number(self, s: str):
        if s is None: 
            return None
        s = s.strip()
        if not s: 
            return None
        # nawiasy jako minus
        neg = s.startswith("(") and s.endswith(")")
        s = s.strip("()").replace(",", "")
        # czasem są kropki jako leading dot w EPS: ".34"
        try:
            val = float(s)
        except ValueError:
            return None
        return -val if neg else val

    
    def clean_statement_headers(self, df, year: int):
        df = df.copy()
        df["Label"] = df["Label"].astype(str).str.strip()
    
        # 1) wyrzuć wiersze z miesiącami (np. "December 31")
        mask_month = df["Label"].str.contains(self._MONTH_RE, na=False)
    
        # 2) wyrzuć „nagłówki liczbowe” (same liczby/roczniki) i linie z samymi kreskami
        mask_numeric_like = df["Label"].str.match(r'^\s*[-–—]*\d+([.,]\d+)?\s*[-–—]*$', na=False)
        mask_year_inline = df["Label"].str.contains(r'\b(?:19|20)\d{2}\b', na=False)
        mask_dashes       = df["Label"].str.match(r'^\s*[-–—]+\s*$', na=False)
    
        to_drop = mask_month | mask_numeric_like | mask_year_inline | mask_dashes
        df = df[~to_drop]
    
        num_cols = [c for c in df.columns if c != "Label"]
        if num_cols:
            df = df.dropna(subset=num_cols, how="all")
    
        rename = {}
        if "A" in df.columns: rename["A"] = str(year)
        if "B" in df.columns: rename["B"] = str(year - 1)
        df = df.rename(columns=rename)
    
        return df.reset_index(drop=True)


    def parse_text(self, text, year):
        
        tables_raw = re.findall(r"<TABLE.*?>.*?</TABLE>", text, flags=re.I|re.S)
        dfs = [self.parse_legacy_table(t, year) for t in tables_raw]

        return dfs

    
    def parse_legacy_table(self, table_html: str, year:int) -> pd.DataFrame:
        
        raw = html.unescape(re.sub(r"<[^>]+>", "", table_html))
        lines = [ln.strip() for ln in raw.splitlines()]
        
        rows = []
        for ln in lines:
            if not ln or set(ln) == {"-"}:
                continue
            m = self._num_re.match(ln)
            if m:
                label = m.group("label").strip().rstrip(":")
                v1 = self._to_number(m.group("v1"))
                v2 = self._to_number(m.group("v2"))
                rows.append((label, v1, v2))
            else:
                # linia nagłówka sekcji (np. "Costs and expenses:")
                if ln.endswith(":"):
                    rows.append((ln.rstrip(":"), None, None))
    
        
        
        if not rows:            
            return pd.DataFrame(columns=["Label"])
    
        cols = ["Label"] + (["Col A", "Col B"][:len(rows[0]) - 1])
    
        df = pd.DataFrame(rows, columns=["Label", "A", "B"])

        keep = ["Label"]
        for c in ["A", "B"]:
            if not df[c].isna().all():
                keep.append(c)
        df = df[keep]
        df = self.clean_statement_headers(df, year)
        return df