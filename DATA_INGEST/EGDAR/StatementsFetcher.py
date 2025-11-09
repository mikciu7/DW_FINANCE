from QuarterlyIncomeStatement import QuarterlyIncomeStatement
from QuarterlyBalanceSheet import QuarterlyBalanceSheet
from QuarterlyCashFlow import QuarterlyCashFlow
import os
from edgar import Company, set_identity
import pandas as pd
import re
from datetime import datetime
import io
import contextlib
from HtmlParser import HtmlParser
from TextParser import TextParser


class StatementsFetcher():

    def __init__(self):
        self.q_income = QuarterlyIncomeStatement()
        self.q_balance = QuarterlyBalanceSheet()
        self.q_cashflow = QuarterlyCashFlow()
        set_identity("Mikolaj Ciuba ciubamikolaj22@gmail.com")
        self.xbrl = None
        self.text = None
        self.html = None

    def which_quarter(self, month):
        if 1 <= month <= 3:
            return 1
        elif 4 <= month <= 6:
            return 2
        elif 7 <= month <= 9:
            return 3
        elif month <= 12:
            return 4
        else:
            return None

    def get_quarter_from_filing(self, filing):
        """
        Bierze z daty miesiac i zwraca kwartal danego mu statementu
        """
        
        date_str = getattr(filing, "report_date", None) or getattr(filing, "period_of_report", None)

        if not date_str:
            return None
            
        try:
            d = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        except Exception:
            return None

        return self.which_quarter(d.month)


    def safe_year_from_report_date(self, filing):
        """
        Bezpiecznie wyciąga rok z filingu (np. '2024-06-29' -> 2024).
        Zwraca int albo None.
        """
        d = getattr(filing, "report_date", None) or getattr(filing, "period_of_report", None)
        if not d:
            return None
        s = str(d)
        if len(s) >= 4 and s[:4].isdigit():
            return int(s[:4])
        return None
        

    def load_filing_content(self, filing):
        for fmt in ("xbrl", "html", "text"):
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    content = getattr(filing, fmt)()
                if content:
                    setattr(self, fmt, content)
                    return fmt
            except Exception:
                pass
        return None
        
            
    def fetch_statements(self, start_year, start_month, end_year, end_month, ticker):
        
        start_quarter = self.which_quarter(start_month)
        end_quarter = self.which_quarter(end_month)
        year, quarter = start_year, start_quarter
        while (year < end_year) or (year == end_year and quarter <= end_quarter):
            
            label = f"{year}Q{quarter}"
            print(f"Pobieram {label}...")

            try:
                company = Company(ticker)
                filings = list(company.get_filings(form="10-Q"))
            except Exception as e:
                print(f"Błąd pobierania filings dla {ticker}: {e}")
                return None
    
            if not filings:
                print(f"Brak jakichkolwiek 10-Q dla {ticker}.")
                return None

            yr = int(year)
            q  = int(quarter)


            candidates = [f for f in filings if self.safe_year_from_report_date(f) == yr]

            if not candidates:
                print(f"Brak raportu 10-Q z roku {yr} dla {ticker}.")
                return None

        

            candidates = [f for f in candidates if self.get_quarter_from_filing(f) == quarter]


            print(candidates)
    
            if not candidates:
                print(f"Brak raportu 10-Q za Q{quarter} {year} dla {ticker}")
                return None

            filing = candidates[0]

            used_fmt = self.load_filing_content(filing)

            if not used_fmt:
                print("Nie udało się pobrać XBRL/HTML/TEXT dla wybranego filing.")
                return None
    
    
            if(used_fmt == "html"):
                print("HTML")
                html_parser = HtmlParser()
                income_df = html_parser.parse_html_stmt(self.html, "income")
                balance_df = html_parser.parse_html_stmt(self.html, "balance")
                cashflow_df = html_parser.parse_html_stmt(self.html, "cashflow")

                return [income_df, balance_df, cashflow_df]
    
            elif(used_fmt == "text"):
                print("TEXT")
                text_parser = TextParser()
                parsed = text_parser.parse_text(self.text, yr)
                print(parsed)
    
            else:
                print("XBRL")
                print(self.q_income.get_quarterly_report(self.xbrl))
                print(self.q_balance.get_quarterly_report(self.xbrl))
                print(self.q_cashflow.get_quarterly_report(self.xbrl))

            
            quarter += 1
            if quarter > 4:
                quarter = 1
                year += 1
                
         


                