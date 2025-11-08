import os
from edgar import Company, set_identity
import pandas as pd
import re


class QuarterlyIncomeStatement():

    def __init__(self):
        """
        Inicjuje najważniejsze obiekty

        current_quarter_report -> oczyszczony dataframe zawierający dane liczbowe
        totals -> Najważniejsze zsumowane kategorie
        distros -> Rozłożenie głównych kategorii na jakieś części (trudne do zkluczowania)
        
        """
        
        set_identity("Mikolaj Ciuba ciubamikolaj22@gmail.com")
        self.current_quarter_report = None
        self.totals = None
        self.distros = None


    @staticmethod
    def _date_cols(df):
        return [c for c in df.columns if re.match(r"\d{4}-\d{2}-\d{2}", str(c))]

        
    def tidy_statement_numeric(self, df):
        """
        Funkcja wyrzuca wiersze gdzie wartości w kolumnach z datami nie są liczbowe ( Dane strukturalne formatu xbrl)
        Zmiejsza liczbę wierszy i kolumn do tych potrzebnych
        """
        df = df.copy()
    
        date_cols = self._date_cols(df)
    
        has_value = df[date_cols].apply(pd.to_numeric, errors="coerce").notna().any(axis=1)
        out = df.loc[has_value].copy()
    
        if "preferred_sign" in out.columns:
            for c in date_cols:
                out[c] = pd.to_numeric(out[c], errors="coerce")
            neg = out["preferred_sign"] == -1
            out.loc[neg, date_cols] = -out.loc[neg, date_cols]
    
        keep_cols = ["concept", "label"]
        if "dimension" in out.columns:
            keep_cols.append("dimension")
        if "balance" in out.columns:
            keep_cols.append("balance")
    
        tidy = out[keep_cols + date_cols].sort_values("label").reset_index(drop=True)
        return tidy
    
    
    def get_latest_quarterly_report(self, ticker, scale=1e6):
        """
        Funkcja zwracająca przekształocną tabelę wyjściową raportu kwartałowego
        """
        
        company = Company(ticker)
    
        filing = company.get_filings(form="10-Q").latest()
    
        self.xbrl = filing.xbrl()
        stmt = self.xbrl.statements.income_statement()
        df = stmt.to_dataframe()
    
        tidy = self.tidy_statement_numeric(df)
    
        date_cols = self._date_cols(tidy)
        
        if scale:
            tidy[date_cols] = tidy[date_cols].apply(pd.to_numeric, errors="coerce") / scale

            
        self.current_quarter_report = tidy
        
        if "dimension" in tidy.columns:
            self.totals = tidy[~tidy["dimension"]].reset_index(drop=True)
            self.distros = tidy[ tidy["dimension"]].reset_index(drop=True)
        else:
            self.totals = tidy.copy()
            self.distros = pd.DataFrame()

        
        return self.combine_totals_and_distros()

    

    def combine_totals_and_distros(self) -> pd.DataFrame:
        """
        Funkcja tworząca kolumnę INCOME_STATEMENT_STEP grupującą dystrybucję jakiejś głównej kategorii z tą kategorią ze statementu
        np. grupowanie informacji Revenue z dystrybucją tej wartości względem krajów i sprzedanych produktów
        """
        
        if self.totals is None or self.distros is None:
            raise ValueError("Load a report first (get_latest_quarterly_report).")
    
        date_cols = [c for c in self.totals.columns if re.match(r"\d{4}-\d{2}-\d{2}", str(c))]
        base_cols = ["label"]
        if "dimension" in self.totals.columns: base_cols.append("dimension")
        if "balance" in self.totals.columns: base_cols.append("balance")
        keep_cols = ["INCOME_STATEMENT_STEP", *base_cols, *date_cols]
    
        out_parts = []
    
        totals = self.totals.copy()
        totals["INCOME_STATEMENT_STEP"] = totals["label"]
    
        for concept in totals["concept"].drop_duplicates():
            tot_rows = totals[totals["concept"] == concept].copy()
            out_parts.append(tot_rows[keep_cols])
    
            d = self.distros[self.distros["concept"] == concept].copy()
            if not d.empty:
                d["INCOME_STATEMENT_STEP"] = tot_rows["INCOME_STATEMENT_STEP"].iloc[0]
    
                out_parts.append(d[keep_cols])
    
        if not out_parts:
            return pd.DataFrame(columns=keep_cols)
    
        return pd.concat(out_parts, ignore_index=True)

    
        
                
