import re
import pandas as pd
from typing import Dict, Optional
import os
from io import StringIO

import warnings
from io import StringIO
import pandas as pd
import re
from typing import Dict

class HtmlParser():

    def __init__(self):
        self.INCOME_KW  = ["net sales", "gross margin", "operating income", "net income", "earnings per common share"]
        self.BALANCE_KW = ["total assets", "total liabilities", "liabilities and shareholders equity", "current assets", "accounts payable"]
        self.CASHFLOW_KW= ["cash flows", "operating activities", "investing activities", "financing activities", "net cash"]
    
    def norm(self, s):
        s = str(s)
        s = re.sub(r"\s+", " ", s.strip().lower())
        s = re.sub(r"[^\w\s]", "", s)
        return s

    def any_contains(self, df: pd.DataFrame, needles) -> int:
        txt = " ".join(df.astype(str).fillna("").values.ravel())
        txt = self.norm(txt)
        return sum(1 for k in needles if k in txt)

    def classify_statements(self, tables) -> Dict[str, pd.DataFrame]:
        best = {"income": (0, None), "balance": (0, None), "cashflow": (0, None)}
        for t in tables:
            sc_inc = self.any_contains(t, self.INCOME_KW)
            sc_bal = self.any_contains(t, self.BALANCE_KW)
            sc_cf  = self.any_contains(t, self.CASHFLOW_KW)
            if sc_inc > best["income"][0]:   best["income"]   = (sc_inc, t)
            if sc_bal > best["balance"][0]:  best["balance"]  = (sc_bal, t)
            if sc_cf  > best["cashflow"][0]: best["cashflow"] = (sc_cf, t)
        return {k: v for k, (_, v) in best.items()}
        

    def drop_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ustawia pierwszy wiersz jako nagłówek, nazywa pierwszą kolumnę 'Label',
        usuwa duplikaty i puste kolumny.
        """
        if df is None or df.empty:
            return df
        
        new_cols = df.iloc[0].fillna("").astype(str).str.strip().tolist()
        df = df[1:].reset_index(drop=True)
        df.columns = new_cols
        
        if len(df.columns) > 0:
            df.columns = [("Label" if i == 0 else c) for i, c in enumerate(df.columns)]
        
        df = df.dropna(axis=1, how="all")
    
        df = df.T.drop_duplicates().T
        
        return df

    
    def parse_html_stmt(self, html, stmt):
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)  # **ZMIANA 1: wycisz FutureWarning applymap/map**
            tables = pd.read_html(StringIO(html))

        clean = []
        for t in tables:
            t = t.replace(r'^\s*(\$|—|–|-|\(|\))?\s*$', pd.NA, regex=True)

            # **ZMIANA 2: użyj DataFrame.map jeśli jest, wstecznie fall-back do applymap**
            mapper = getattr(t, "map", None)
            if callable(mapper):
                t = t.map(lambda x: x.strip() if isinstance(x, str) else x)
            else:
                t = t.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            t = t.dropna(how="all")  # wiersze całe puste

            header_rows = 2
            if len(t) > header_rows:
                empty_cols = t.iloc[header_rows:].isna().all()
            else:
                empty_cols = t.isna().all()
            t = t.loc[:, ~empty_cols]  # usuń całe puste kolumny (po nagłówkach)

            # usuń wiersze, gdzie wszystkie kolumny POZA pierwszą są puste (<NA>)
            if t.shape[1] > 1:
                nonfirst = t.iloc[:, 1:]
                t = t.loc[~nonfirst.isna().all(axis=1)]
                
            print(t)
            t = self.drop_duplicate_columns(t) 
            
            clean.append(t)

        stmts = self.classify_statements(clean)
        out = stmts.get(stmt)
        
        if out is None:
            return pd.DataFrame()
        if not isinstance(out, pd.DataFrame):
            out = pd.DataFrame(out)
        return out.reset_index(drop=True)
