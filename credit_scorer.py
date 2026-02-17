"""
Credit Scoring Model for M-PESA Transactions
Turns transaction patterns into loan decisions
"""

import pandas as pd
import numpy as np
from datetime import datetime

class CreditScorer:
    def __init__(self, df):
        """
        Initialize with transaction dataframe
        df should have columns: Date, Amount, Balance, TransactionType
        """
        self.df = df.copy()
        self.score = 50  # Start neutral
        self.features = {}
        self.reasons = []
        
    def prepare_data(self):
        """Convert dates and prepare the dataframe"""
        # Convert Date column to datetime
        if 'Date' in self.df.columns:
            self.df['Date'] = pd.to_datetime(self.df['Date'])
        
        # Extract hour from time if available
        if 'Time' in self.df.columns:
            self.df['Hour'] = pd.to_datetime(self.df['Time'], format='%H:%M').dt.hour
        else:
            self.df['Hour'] = 12  # Default if no time
            
        # Clean amount (remove KSh, commas)
        if 'Amount' in self.df.columns:
            self.df['Amount'] = self.df['Amount'].astype(str).str.replace('[KSh,\s]', '', regex=True)
            self.df['Amount'] = pd.to_numeric(self.df['Amount'], errors='coerce')
            
        # Clean balance
        if 'Balance' in self.df.columns:
            self.df['Balance'] = self.df['Balance'].astype(str).str.replace('[KSh,\s]', '', regex=True)
            self.df['Balance'] = pd.to_numeric(self.df['Balance'], errors='coerce')
            
        # Identify transaction types
        if 'TransactionType' not in self.df.columns:
            # Try to infer from description
            self.df['TransactionType'] = 'Unknown'
            if 'Description' in self.df.columns:
                desc = self.df['Description'].str.lower()
                self.df.loc[desc.str.contains('airtime', na=False), 'TransactionType'] = 'Airtime'
                self.df.loc[desc.str.contains('send|sent|transfer', na=False), 'TransactionType'] = 'Send'
                self.df.loc[desc.str.contains('withdraw|cash', na=False), 'TransactionType'] = 'Withdraw'
                self.df.loc[desc.str.contains('pay|payment|till', na=False), 'TransactionType'] = 'Payment'
                self.df.loc[desc.str.contains('salary|income|deposit', na=False), 'TransactionType'] = 'Income'
                
    def calculate_features(self):
        """Extract all predictive features from transaction data"""
        
        # 1. Average Daily Balance
        daily_balance = self.df.groupby(self.df['Date'].dt.date)['Balance'].last()
        self.features['avg_daily_balance'] = daily_balance.mean()
        
        # 2. Income Regularity (std deviation between income transactions)
        income_txns = self.df[self.df['TransactionType'] == 'Income']
        if len(income_txns) > 1:
            income_dates = income_txns['Date'].sort_values()
            day_diffs = income_dates.diff().dt.days.dropna()
            self.features['income_regularity'] = day_diffs.std()
        else:
            self.features['income_regularity'] = 999  # Very irregular if no income pattern
            
        # 3. Night Transaction Ratio
        night_txns = self.df[self.df['Hour'].between(22, 5) | self.df['Hour'].between(0, 5)]
        self.features['night_ratio'] = len(night_txns) / max(len(self.df), 1)
        
        # 4. Airtime Ratio (stability indicator)
        airtime_txns = self.df[self.df['TransactionType'] == 'Airtime']
        self.features['airtime_ratio'] = len(airtime_txns) / max(len(self.df), 1)
        
        # 5. Rounded Amount Ratio (gambling indicator)
        self.df['is_rounded'] = self.df['Amount'] % 100 == 0
        self.features['rounded_ratio'] = self.df['is_rounded'].mean()
        
        # 6. Transaction Frequency
        date_range = (self.df['Date'].max() - self.df['Date'].min()).days
        self.features['txns_per_day'] = len(self.df) / max(date_range, 1)
        
        # 7. Low Balance Frequency
        low_balance = self.df[self.df['Balance'] < 500]
        self.features['low_balance_ratio'] = len(low_balance) / max(len(self.df), 1)
        
        return self.features
    
    def calculate_score(self):
        """Convert features to a credit score (0-100)"""
        score = 50  # Base score
        
        # Feature 1: Average Daily Balance (up to +20)
        avg_bal = self.features.get('avg_daily_balance', 0)
        if avg_bal > 50000:
            score += 20
        elif avg_bal > 20000:
            score += 15
        elif avg_bal > 10000:
            score += 10
        elif avg_bal > 5000:
            score += 5
        elif avg_bal > 1000:
            score += 2
            
        # Feature 2: Income Regularity (lower std = better, up to +20)
        income_std = self.features.get('income_regularity', 999)
        if income_std < 3:  # Less than 3 days variation
            score += 20
            self.reasons.append("Very regular income pattern")
        elif income_std < 7:  # Weekly pattern
            score += 15
            self.reasons.append("Regular income pattern")
        elif income_std < 15:
            score += 5
            self.reasons.append("Somewhat regular income")
        else:
            score -= 10
            self.reasons.append("Irregular income - risk factor")
            
        # Feature 3: Night Transactions (penalty up to -20)
        night_ratio = self.features.get('night_ratio', 0)
        if night_ratio > 0.3:  # More than 30% at night
            score -= 20
            self.reasons.append("High night activity - potential risk")
        elif night_ratio > 0.15:
            score -= 10
            self.reasons.append("Moderate night activity")
        elif night_ratio > 0.05:
            score -= 5
            
        # Feature 4: Airtime Purchases (stability, up to +10)
        airtime_ratio = self.features.get('airtime_ratio', 0)
        if airtime_ratio > 0.1:
            score += 10
            self.reasons.append("Regular airtime purchases - stable behavior")
        elif airtime_ratio > 0.05:
            score += 5
            
        # Feature 5: Rounded Amounts (gambling risk, penalty up to -15)
        rounded_ratio = self.features.get('rounded_ratio', 0)
        if rounded_ratio > 0.4:
            score -= 15
            self.reasons.append("Many rounded amounts - possible gambling")
        elif rounded_ratio > 0.2:
            score -= 10
            self.reasons.append("Some rounded amounts")
            
        # Feature 6: Low Balance Frequency (penalty up to -15)
        low_ratio = self.features.get('low_balance_ratio', 0)
        if low_ratio > 0.3:
            score -= 15
            self.reasons.append("Frequently low balance - cash flow issues")
        elif low_ratio > 0.15:
            score -= 8
            
        # Feature 7: Transaction Frequency (too many or too few)
        txn_freq = self.features.get('txns_per_day', 2)
        if 3 <= txn_freq <= 8:
            score += 10  # Goldilocks zone
            self.reasons.append("Healthy transaction activity")
        elif txn_freq > 15:
            score -= 10
            self.reasons.append("Very high transaction volume - business?")
        elif txn_freq < 0.5:
            score -= 5
            self.reasons.append("Low account activity")
            
        # Ensure score is between 0-100
        self.score = max(0, min(100, round(score, 1)))
        return self.score
    
    def get_loan_recommendation(self):
        """Convert score to loan decision"""
        if self.score >= 80:
            return {
                'decision': '✅ APPROVE',
                'amount': 'KES 50,000',
                'interest': '8%',
                'message': 'Excellent credit behavior. Low risk borrower.',
                'color': 'green'
            }
        elif self.score >= 65:
            return {
                'decision': '✅ APPROVE',
                'amount': 'KES 25,000',
                'interest': '12%',
                'message': 'Good credit behavior. Moderate risk.',
                'color': 'lightgreen'
            }
        elif self.score >= 50:
            return {
                'decision': '⚠️ APPROVE',
                'amount': 'KES 10,000',
                'interest': '15%',
                'message': 'Fair credit behavior. Higher interest rate.',
                'color': 'orange'
            }
        elif self.score >= 35:
            return {
                'decision': '⚠️ CONDITIONAL',
                'amount': 'KES 3,000',
                'interest': '20%',
                'message': 'High risk. Small loan only.',
                'color': 'red'
            }
        else:
            return {
                'decision': '❌ DECLINE',
                'amount': 'KES 0',
                'interest': 'N/A',
                'message': 'Unable to offer loan at this time.',
                'color': 'darkred'
            }
    
    def analyze(self):
        """Run full analysis"""
        self.prepare_data()
        self.calculate_features()
        score = self.calculate_score()
        recommendation = self.get_loan_recommendation()
        
        return {
            'score': score,
            'recommendation': recommendation,
            'features': self.features,
            'reasons': self.reasons
        }