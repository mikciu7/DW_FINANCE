import os
from edgar import Company, set_identity
import pandas as pd
import re


class QuarterlyCashFlow():

    def __init__(self):
        """
        Inicjuje najważniejsze obiekty
        """
        
        set_identity("Mikolaj Ciuba ciubamikolaj22@gmail.com")
        self.current_quarter_report = None

        self.CASHFLOW_CATEGORIES = {
          "net_income": ["us-gaap[:_]NetIncomeLoss"],
          "depreciation_and_amortization": ["us-gaap[:_]DepreciationDepletionAndAmortization"],
          "share_based_compensation": ["us-gaap[:_]ShareBasedCompensation"],
          "other_non_cash_items": ["us-gaap[:_]OtherNoncashIncomeExpense"],
          "change_in_accounts_receivable": ["us-gaap[:_]IncreaseDecreaseInAccountsReceivable"],
          "change_in_other_receivables": ["us-gaap[:_]IncreaseDecreaseInOtherReceivables"],
          "change_in_inventories": ["us-gaap[:_]IncreaseDecreaseInInventories"],
          "change_in_other_operating_assets": ["us-gaap[:_]IncreaseDecreaseInOtherOperatingAssets"],
          "change_in_accounts_payable": ["us-gaap[:_]IncreaseDecreaseInAccountsPayable"],
          "change_in_other_operating_liabilities": ["us-gaap[:_]IncreaseDecreaseInOtherOperatingLiabilities"],
          "net_cash_from_operating_activities": [
            "us-gaap[:_]NetCashProvidedByUsedInOperatingActivities",
            "us-gaap[:_]NetCashProvidedByUsedInOperatingActivitiesContinuingOperationsAbstract"
          ],
        
          "purchase_of_marketable_securities": ["us-gaap[:_]PaymentsToAcquireAvailableForSaleSecuritiesDebt"],
          "maturities_of_securities": ["us-gaap[:_]ProceedsFromMaturitiesPrepaymentsAndCallsOfAvailableForSaleSecurities"],
          "sale_of_securities": ["us-gaap[:_]ProceedsFromSaleOfAvailableForSaleSecuritiesDebt"],
          "capital_expenditures": ["us-gaap[:_]PaymentsToAcquirePropertyPlantAndEquipment"],
          "other_investing_cash_flows": ["us-gaap[:_]PaymentsForProceedsFromOtherInvestingActivities"],
          "net_cash_from_investing_activities": [
            "us-gaap[:_]NetCashProvidedByUsedInInvestingActivities",
            "us-gaap[:_]NetCashProvidedByUsedInInvestingActivitiesContinuingOperationsAbstract"
          ],
        
          "dividends_paid": ["us-gaap[:_]PaymentsOfDividends"],
          "share_repurchases": ["us-gaap[:_]PaymentsForRepurchaseOfCommonStock"],
          "long_term_debt_issued": ["us-gaap[:_]ProceedsFromIssuanceOfLongTermDebt"],
          "long_term_debt_repaid": ["us-gaap[:_]RepaymentsOfLongTermDebt"],
          "commercial_paper_activity": ["us-gaap[:_]ProceedsFromRepaymentsOfCommercialPaper"],
          "share_based_tax_withholding": ["us-gaap[:_]PaymentsRelatedToTaxWithholdingForShareBasedCompensation"],
          "other_financing_cash_flows": ["us-gaap[:_]ProceedsFromPaymentsForOtherFinancingActivities"],
          "net_cash_from_financing_activities": [
            "us-gaap[:_]NetCashProvidedByUsedInFinancingActivities",
            "us-gaap[:_]NetCashProvidedByUsedInFinancingActivitiesContinuingOperationsAbstract"
          ],
        
          "net_change_in_cash": [
            "us-gaap[:_]CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect"
          ],
          "ending_cash_balance": [
            "us-gaap[:_]CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
          ],
          "income_taxes_paid": ["us-gaap[:_]IncomeTaxesPaidNet"],
          "acquisitions_and_intangibles": [
            "msft[:_]AcquisitionsNetOfCashAcquiredAndPurchasesOfIntangibleAndOtherAssets",
            "(?i)acquisition.*intangible.*other.*assets"
          ],
          "deferred_income_taxes": [
            "us-gaap[:_]DeferredIncomeTaxExpenseBenefit",
            "(?i)deferred.*income.*tax"
          ],
          "depreciation_amortization_and_other": [
            "msft[:_]DepreciationAmortizationAndOther",
            "(?i)depreciation.*amortization.*other"
          ],
          "effect_of_exchange_rate_on_cash": [
            "us-gaap[:_]EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations",
            "(?i)effect.*exchange.*rate.*cash"
          ],
          "change_in_income_taxes_payable": [
            "us-gaap[:_]IncreaseDecreaseInAccruedIncomeTaxesPayable",
            "(?i)increase.*decrease.*income.*tax.*payable"
          ],
          "gain_loss_on_investments_and_derivatives": [
            "msft[:_]GainLossOnInvestmentsAndDerivativeInstruments",
            "(?i)gain.*loss.*investment.*derivative"
          ],
          "change_in_other_current_assets": [
            "us-gaap[:_]IncreaseDecreaseInOtherCurrentAssets",
            "(?i)increase.*decrease.*other.*current.*asset"
          ],
          "change_in_other_current_liabilities": [
            "us-gaap[:_]IncreaseDecreaseInOtherCurrentLiabilities",
            "(?i)increase.*decrease.*other.*current.*liabilit"
          ],
          "change_in_other_noncurrent_assets": [
            "us-gaap[:_]IncreaseDecreaseInOtherNoncurrentAssets",
            "(?i)increase.*decrease.*other.*non.?current.*asset"
          ],
          "change_in_other_noncurrent_liabilities": [
            "us-gaap[:_]IncreaseDecreaseInOtherNoncurrentLiabilities",
            "(?i)increase.*decrease.*other.*non.?current.*liabilit"
          ],
          "proceeds_from_common_stock_issuance": [
            "us-gaap[:_]ProceedsFromIssuanceOfCommonStock",
            "(?i)proceed.*issuance.*common.*stock"
          ],
          "purchases_of_investments": [
            "us-gaap[:_]PaymentsToAcquireInvestments",
            "(?i)payment.*acquire.*investment"
          ],
          "repayments_of_long_term_debt": [
            "us-gaap[:_]RepaymentsOfDebtMaturingInMoreThanThreeMonths",
            "(?i)repay.*debt.*more.*than.*three.*months"
          ],
          "short_term_debt_activity": [
            "us-gaap[:_]ProceedsFromRepaymentsOfShortTermDebtMaturingInThreeMonthsOrLess",
            "(?i)short.*term.*debt.*three.*months"
          ],
          "proceeds_from_investments": [
            "msft[:_]ProceedsFromInvestments",
            "(?i)proceed.*investment"
          ],
          "change_in_contract_liability": [
            "us-gaap[:_]IncreaseDecreaseInContractWithCustomerLiability",
            "(?i)increase.*decrease.*contract.*liabilit"
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
    
    
    def get_latest_quarterly_report(self, ticker, scale=1e6):
        """
        Uniwersalna funkcja która bierze 
        """
        
        company = Company(ticker)
    
        filing = company.get_filings(form="10-Q").latest()
    
        self.xbrl = filing.xbrl()
        stmt = self.xbrl.statements.cashflow_statement()
        df = stmt.to_dataframe()
    
        tidy = self.tidy_statement_numeric(df)
    
        date_cols = self._date_cols(tidy)
        
        if scale:
            tidy[date_cols] = tidy[date_cols].apply(pd.to_numeric, errors="coerce") / scale

            
        self.current_quarter_report = tidy
        
        
        return self.tag_balance_sheet_categories(tidy)



    def tag_balance_sheet_categories(self, df: pd.DataFrame):
        
        out_col = "cf_category"
        categories = self.CASHFLOW_CATEGORIES
        
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

        
        
       # return out[out["cf_category"].isna()]["concept"].to_list()


        out = out.drop(columns=["concept", "dimension"])
        return out
        
        
            
                    
