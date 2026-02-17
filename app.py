import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from io import BytesIO

# Import your existing modules
from data_processor import DataProcessor
from categorizer import ExpenseCategorizer
from financial_health import FinancialHealthAnalyzer
from credit_scorer import CreditScorer

from visualizer import (
    create_pie_chart, 
    create_bar_chart, 
    create_trend_chart,
    create_monthly_comparison,
    create_category_distribution,
    create_daily_spending_heatmap,
    create_transaction_volume_chart
)

# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="FinScore - M-PESA Credit Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        background: linear-gradient(90deg, #43B02A 0%, #2E7D32 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #43B02A;
    }
    
    /* Score card */
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .score-number {
        font-size: 4rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    /* Decision badges */
    .badge-approve {
        background: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .badge-decline {
        background: #f44336;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .badge-conditional {
        background: #ff9800;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    /* Feature cards */
    .feature-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #43B02A;
    }
    
    /* Section headers */
    .section-header {
        color: #2E7D32;
        font-size: 1.5rem;
        font-weight: bold;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #43B02A;
    }
    
    /* Info boxes */
    .info-box {
        background: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #43B02A;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== SIDEBAR =====
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/mpesa.png", width=80)
    st.markdown("## FinScore Analyzer")
    st.markdown("---")
    
    # App mode selection
    mode = st.radio(
        "Navigation",
        ["📊 Dashboard", "📈 Deep Analysis", "🏦 Loan Calculator", "⚙️ Settings"]
    )
    
    st.markdown("---")
    
    # Quick tips
    with st.expander("💡 Quick Tips"):
        st.markdown("""
        - Upload CSV or PDF statements
        - Get instant credit score
        - Understand your financial health
        - Predict loan eligibility
        """)
    
    # About section
    st.markdown("---")
    st.markdown("### About")
    st.markdown("**FinScore** analyzes M-PESA transactions to provide credit scores for the unbanked.")
    st.markdown("v1.0.0")

# ===== MAIN HEADER =====
st.markdown("""
<div class="main-header">
    <h1>💰 FinScore - M-PESA Credit Analyzer</h1>
    <p>AI-powered financial insights and instant credit scoring from your M-PESA transactions</p>
</div>
""", unsafe_allow_html=True)

# ===== FILE UPLOAD SECTION =====
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    uploaded_file = st.file_uploader(
        "📤 **Upload your M-PESA statement**",
        type=['csv', 'pdf'],
        help="Upload CSV or PDF format M-Pesa statements (Max 200MB)"
    )

# ===== MAIN CONTENT =====
if uploaded_file is not None:
    # Process the file
    with st.spinner("🔄 Processing your statement... Please wait."):
        processor = DataProcessor()
        
        if uploaded_file.type == "application/pdf":
            df = processor.process_pdf(uploaded_file)
        else:
            df = processor.process_csv(uploaded_file)
        
        # Store in session state
        st.session_state.processed_data = df
        
        # Get basic metrics
        total_transactions = len(df)
        total_income = df[df['Amount'] > 0]['Amount'].sum() if 'Amount' in df.columns else 0
        total_expenses = df[df['Amount'] < 0]['Amount'].abs().sum() if 'Amount' in df.columns else 0
        net_cashflow = total_income - total_expenses
    
    # Success message
    st.success(f"✅ Successfully processed {total_transactions} transactions!")
    
    # ===== METRICS ROW =====
    st.markdown('<div class="section-header">📊 Financial Overview</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📝 Transactions</h3>
            <h2>{total_transactions}</h2>
            <p style="color: #666;">Total count</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Income</h3>
            <h2 style="color: #4CAF50;">KES {total_income:,.0f}</h2>
            <p style="color: #666;">Total received</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💸 Expenses</h3>
            <h2 style="color: #f44336;">KES {total_expenses:,.0f}</h2>
            <p style="color: #666;">Total spent</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        flow_color = "green" if net_cashflow >= 0 else "red"
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Net Flow</h3>
            <h2 style="color: {flow_color};">KES {net_cashflow:,.0f}</h2>
            <p style="color: #666;">{('Positive' if net_cashflow >= 0 else 'Negative')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== CREDIT SCORE SECTION =====
    st.markdown('<div class="section-header">🏦 Credit Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔍 ANALYZE MY CREDIT WORTHINESS", use_container_width=True):
            with st.spinner("🧠 Analyzing transaction patterns..."):
                try:
                    scorer = CreditScorer(st.session_state.processed_data)
                    result = scorer.analyze()
                    st.session_state.credit_result = result
                except Exception as e:
                    st.error(f"Analysis error: {str(e)}")
    
    with col2:
        if st.button("🔄 RESET ANALYSIS", use_container_width=True):
            if 'credit_result' in st.session_state:
                del st.session_state.credit_result
            st.rerun()
    
    # Display credit results if available
    if 'credit_result' in st.session_state:
        result = st.session_state.credit_result
        score = result['score']
        decision = result['recommendation']
        
        # Score and Decision Row
        col1, col2 = st.columns(2)
        
        with col1:
            # Determine score color
            if score >= 70:
                score_color = "#4CAF50"
            elif score >= 50:
                score_color = "#FF9800"
            else:
                score_color = "#f44336"
            
            st.markdown(f"""
            <div class="score-card" style="background: linear-gradient(135deg, {score_color} 0%, #333 100%);">
                <h3>Your Credit Score</h3>
                <div class="score-number">{score}/100</div>
                <p>Based on your transaction history</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Determine badge class
            if 'APPROVE' in decision['decision']:
                badge_class = "badge-approve"
                badge_text = "✅ APPROVED"
            elif 'CONDITIONAL' in decision['decision']:
                badge_class = "badge-conditional"
                badge_text = "⚠️ CONDITIONAL"
            else:
                badge_class = "badge-decline"
                badge_text = "❌ DECLINED"
            
            st.markdown(f"""
            <div class="score-card" style="background: linear-gradient(135deg, #2196F3 0%, #0D47A1 100%);">
                <h3>Loan Decision</h3>
                <div class="score-number" style="font-size: 2.5rem;">{decision['amount']}</div>
                <p>at {decision['interest']}</p>
                <div class="{badge_class}" style="display: inline-block; margin-top: 1rem;">{badge_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Message
        st.markdown(f"""
        <div class="info-box">
            <strong>📌 Analysis Summary:</strong> {decision['message']}
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed Factors
        with st.expander("🔍 View Detailed Analysis Factors", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ⚖️ Risk Factors")
                risk_factors = [r for r in result['reasons'] if 'risk' in r.lower() or 'low' in r.lower() or 'irregular' in r.lower()]
                if risk_factors:
                    for factor in risk_factors:
                        st.markdown(f"""
                        <div class="feature-card">
                            ⚠️ {factor}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("No significant risk factors detected.")
            
            with col2:
                st.markdown("#### ✅ Positive Factors")
                positive_factors = [r for r in result['reasons'] if 'healthy' in r.lower() or 'regular' in r.lower()]
                if positive_factors:
                    for factor in positive_factors:
                        st.markdown(f"""
                        <div class="feature-card" style="border-left-color: #4CAF50;">
                            ✓ {factor}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("No positive factors identified.")
            
            # Technical Features
            st.markdown("#### 📊 Technical Metrics")
            features_df = pd.DataFrame([
                {"Metric": k.replace('_', ' ').title(), "Value": f"{v:.2f}" if isinstance(v, float) else str(v)}
                for k, v in result['features'].items()
            ])
            st.dataframe(features_df, use_container_width=True, hide_index=True)

else:
    # Welcome screen when no file uploaded
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <img src="https://img.icons8.com/color/96/000000/mpesa.png" width="120">
        <h2>Welcome to FinScore Analyzer</h2>
        <p style="color: #666; font-size: 1.2rem; max-width: 600px; margin: 2rem auto;">
            Upload your M-PESA statement to get instant insights into your financial health,
            credit score, and loan eligibility.
        </p>
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; max-width: 800px; margin: 2rem auto;">
            <h4>📋 What you'll get:</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
                <div>📊 Financial Dashboard</div>
                <div>🏦 Credit Score (0-100)</div>
                <div>💰 Loan Recommendations</div>
                <div>📈 Spending Analysis</div>
                <div>🔮 Future Predictions</div>
                <div>📉 Risk Factors</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===== FOOTER =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>FinScore Analyzer v1.0 | Powered by Machine Learning | Not real financial advice</p>
    <p style="font-size: 0.9rem;">© 2026 - Your M-PESA Credit Scoring Solution</p>
</div>
""", unsafe_allow_html=True)