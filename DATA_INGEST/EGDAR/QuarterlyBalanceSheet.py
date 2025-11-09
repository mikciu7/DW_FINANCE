import os
from edgar import Company, set_identity
import pandas as pd
import re


class QuarterlyBalanceSheet():

    def __init__(self):
        """
        Inicjuje najważniejsze obiekty
        """
        
        set_identity("Mikolaj Ciuba ciubamikolaj22@gmail.com")
        self.current_quarter_report = None

        self.BALANCE_CATEGORIES = {
            "cash_and_cash_equivalents": [
                r"^us-gaap[:_]CashAndCashEquivalentsAtCarryingValue$",
                r"[:_]CashAndCashEquivalents(AtCarryingValue)?",   # fallback incl. extensions
            ],
            "accounts_receivable": [
                r"^us-gaap[:_]AccountsReceivable(Net)?Current$",
                r"[:_]AccountsReceivable.*Current",
            ],
            "inventory": [
                r"^us-gaap[:_]Inventory(Net)?$", r"[:_]Inventory",
            ],
            "ppe": [
                r"^us-gaap[:_]PropertyPlantAndEquipment(Net)?$", r"[:_]Property[ _]?Plant[ _]?And[ _]?Equipment",
            ],
            "goodwill": [
                r"^us-gaap[:_]Goodwill$", r"[:_]Goodwill",
            ],
            "intangible_assets": [
                r"^us-gaap[:_]IntangibleAssets.*$", r"[:_]IntangibleAssets",
            ],
            "other_current_assets": [
                r"^us-gaap[:_]OtherAssetsCurrent$", r"[:_]Other.*CurrentAssets",
            ],
            "total_current_assets": [
                r"^us-gaap[:_]AssetsCurrent$", r"[:_]Total.*CurrentAssets",
            ],
            "total_assets": [
                r"^us-gaap[:_]Assets$", r"[:_]TotalAssets$",
            ],
            "accounts_payable": [
                r"^us-gaap[:_]AccountsPayableCurrent$", r"[:_]AccountsPayable.*Current",
            ],
            "total_non_current_assets": [
                r"[:_]AssetsNoncurrent",
                r"Non.?Current.?Assets",
            ],
            "total_current_liabilities": [
                r"^us-gaap[:_]LiabilitiesCurrent$", r"[:_]Total.*CurrentLiabilit",
            ],
            "total_non_current_liabilities": [
                r"^us-gaap[:_]LiabilitiesNoncurrent$"
            ],
            "long_term_debt": [
                r"^us-gaap[:_]LongTermDebtNoncurrent$"
            ],
            "total_liabilities": [
                r"^us-gaap[:_]Liabilities$", r"[:_]TotalLiabilit(y|ies)$",
            ],
            "stockholders_equity": [
                r"^us-gaap[:_]StockholdersEquity.*$", r"[:_]Stockholders'?Equity|[:_]Shareholders'?Equity",
            ],
            "liabilities_and_equity": [
                r"^us-gaap[:_]LiabilitiesAndStockholdersEquity$", r"[:_]LiabilitiesAnd(Stockholders|Shareholders)Equity",
            ],
            "current_marketable_securities": [
                r"us-gaap[:_]MarketableSecuritiesCurrent",
                r"[:_]MarketableSecuritiesCurrent"
            ],
            "vendor_non_trade_receivables": [
                r"us-gaap[:_]NontradeReceivablesCurrent",
                r"[:_]NontradeReceivables.*Current",
                r"(?i)vendor.*non[- ]?trade.*receiv"
            ],
            "other_current_assets": [
                r"us-gaap[:_]OtherAssetsCurrent",
                r"[:_]OtherAssetsCurrent"
            ],
            "non_current_marketable_securities": [
                r"us-gaap[:_]MarketableSecuritiesNoncurrent",
                r"[:_]MarketableSecurities.*Noncurrent",
                r"(?i)non.*current.*marketable.*securit"
            ],
            "other_non_current_assets": [
                r"us-gaap[:_]OtherAssetsNoncurrent",
                r"[:_]OtherAssets.*Noncurrent"
            ],
            "other_current_liabilities": [
                r"us-gaap[:_]OtherLiabilitiesCurrent",
                r"[:_]OtherLiabilitiesCurrent"
            ],
            "deferred_revenue": [
                r"us-gaap[:_]ContractWithCustomerLiabilityCurrent",
                r"[:_]ContractWithCustomerLiability.*Current",
                r"(?i)deferred.*revenue|unearned.*revenue"
            ],
            "commercial_paper": [
                r"us-gaap[:_]CommercialPaper",
                r"[:_]CommercialPaper",
                r"(?i)commercial.*paper"
            ],
            "short_term_debt": [
                r"us-gaap[:_]LongTermDebtCurrent",
                r"[:_]LongTermDebt.*Current",
                r"(?i)short[- ]?term.*debt"
            ],
            "other_non_current_liabilities": [
                r"us-gaap[:_]OtherLiabilitiesNoncurrent",
                r"[:_]OLiabilitiesNoncurrent",
                r"(?i)other.*non.*current.*liabilit"
            ],
            "common_stock": [
                r"us-gaap[:_]CommonStocksIncludingAdditionalPaidInCapital",
                r"[:_]CommonStock",
                r"(?i)common.*stock|share.*capital"
            ],
            "retained_earnings": [
                r"us-gaap[:_]RetainedEarningsAccumulatedDeficit",
                r"[:_]RetainedEarnings",
                r"(?i)retained.*earnings|accumulated.*deficit"
            ],
            "total_stockholders_equity": [
                r"us-gaap[:_]StockholdersEquity",
                r"[:_]StockholdersEquity",
                r"(?i)total.*(?:stockholders|shareholders).*equity"
            ]
        }


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
    
    
    def get_quarterly_report(self, xbrl, scale=1e6):
    
        self.xbrl = xbrl
        stmt = self.xbrl.statements.balance_sheet()
        df = stmt.to_dataframe()
    
        tidy = self.tidy_statement_numeric(df)
    
        date_cols = self._date_cols(tidy)
        
        if scale:
            tidy[date_cols] = tidy[date_cols].apply(pd.to_numeric, errors="coerce") / scale

            
        self.current_quarter_report = tidy
        
        
        return self.tag_balance_sheet_categories(tidy)



    def tag_balance_sheet_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        
        out_col = "bs_category"
        categories = self.BALANCE_CATEGORIES
        
        out = df.copy()
        out[out_col] = None
    
        # Pre-compile patterns for speed
        compiled = {
            cat: [re.compile(pat) for pat in pats]
            for cat, pats in categories.items()
        }
    
        # Ensure we have searchable columns
        if "concept" not in out.columns:
            out["concept"] = ""
        if "label" not in out.columns:
            out["label"] = ""
    
        # Iterate categories (first match wins)
        for cat, patterns in compiled.items():
            # Build a boolean mask for rows not yet tagged
            untagged = out[out_col].isna()
    
            # Match any pattern against concept or label
            mask = pd.Series(False, index=out.index)
            for rx in patterns:
                mask |= (
                    out["concept"].fillna("").str.contains(rx, regex=True, na=False) |
                    out["label"].fillna("").str.contains(rx, regex=True, na=False)
                )
    
            # Assign category where mask true and still untagged
            to_set = untagged & mask
            if to_set.any():
                out.loc[to_set, out_col] = cat

        out = out.drop(columns=["concept", "dimension"])
        
        return out
    
        
        
            
                    
