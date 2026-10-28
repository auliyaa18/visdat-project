import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_DB_URL") or st.secrets.get("SUPABASE_DB_URL")

st.set_page_config(
    page_title="Coffee Shop Analytics Hub", page_icon="☕", layout="wide"
)

# --- KONEKSI DATABASE MULTI-DBMS ---
@st.cache_data
def get_local_products():
  base_dir = os.path.dirname(os.path.abspath(__file__))
  sqlite_path = os.path.join(base_dir, "database", "coffee_local.db")
  conn = sqlite3.connect(sqlite_path)
  df = pd.read_sql("SELECT * FROM coffee_menu", conn)
  conn.close()
  return df


@st.cache_data
def get_cloud_transactions():
  engine = create_engine(SUPABASE_URL)
  df = pd.read_sql("SELECT * FROM coffee_transactions", engine)
  return df


try:
  products_df = get_local_products()
  transactions_df = get_cloud_transactions()
except Exception as e:
  st.error(f"Gagal terhubung ke Database: {e}")
  st.stop()

# --- DATA PIPELINE (JOIN DATA) ---
merged_df = pd.merge(transactions_df, products_df, on="product_id", how="inner")
merged_df["total_sales"] = merged_df["quantity"] * merged_df["price"]

# --- HEADER UTAMA ---
st.title("☕ Coffee Shop Analytics Hub")
st.markdown(
    "Sistem Analisis Penjualan Multi-DBMS Terpadu (SQLite lokal & Supabase"
    " PostgreSQL)"
)

# --- PANEL FILTER DI ATAS (BUKAN DI SIDEBAR) ---
with st.expander("🛠️ Panel Filter & Kontrol Data Interaktif", expanded=True):
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    all_locations = merged_df["store_location"].unique().tolist()
    selected_locations = st.multiselect(
        "Pilih Cabang Toko:", all_locations, default=all_locations
    )
  with col_f2:
    all_payments = merged_df["payment_method"].unique().tolist()
    selected_payments = st.multiselect(
        "Pilih Metode Pembayaran:", all_payments, default=all_payments
    )

# Terapkan Filter
filtered_df = merged_df[
    (merged_df["store_location"].isin(selected_locations))
    & (merged_df["payment_method"].isin(selected_payments))
]

st.divider()

# --- STRUKTUR UTAMA MENGGUNAKAN TABS ---
tab1, tab2, tab3 = st.tabs(
    ["📊 Ringkasan Eksekutif", "☕ Analisis Menu Kopi", "💳 Pembayaran & Detail"]
)

with tab1:
  st.subheader("Performa Utama Toko")

  # Metrik ditata rapi dalam grid kolom
  m1, m2, m3 = st.columns(3)
  with m1:
    st.metric("💰 Total Pendapatan", f"Rp {filtered_df['total_sales'].sum():,.0f}")
  with m2:
    st.metric("📦 Volume Terjual", f"{filtered_df['quantity'].sum()} Cup")
  with m3:
    st.metric("🧾 Total Transaksi", f"{filtered_df['transaction_id'].count()}")

  st.markdown("### 🏢 Pendapatan Berdasarkan Cabang Toko")
  branch_sales = (
      filtered_df.groupby("store_location")["total_sales"]
      .sum()
      .reset_index()
  )
  fig_branch = px.bar(
      branch_sales,
      x="store_location",
      y="total_sales",
      color="store_location",
      text_auto="Rp.2s",
  )
  st.plotly_chart(fig_branch, use_container_width=True)

with tab2:
  st.subheader("Peringkat Menu Kopi Terlaris")
  # Menggunakan grafik batang horizontal agar bentuk visualnya berbeda total
  menu_sales = (
      filtered_df.groupby("coffee_name")["total_sales"]
      .sum()
      .reset_index()
      .sort_values("total_sales", ascending=True)
  )
  fig_menu = px.bar(
      menu_sales,
      x="total_sales",
      y="coffee_name",
      orientation="h",
      color="coffee_name",
      text_auto="Rp.2s",
  )
  st.plotly_chart(fig_menu, use_container_width=True)

with tab3:
  col_t1, col_t2 = st.columns([1, 1.5])
  with col_t1:
    st.subheader("Metode Pembayaran")
    payment_counts = (
        filtered_df.groupby("payment_method")["transaction_id"]
        .count()
        .reset_index()
    )
    fig_pay = px.pie(
        payment_counts,
        names="payment_method",
        values="transaction_id",
        hole=0.5,
    )
    st.plotly_chart(fig_pay, use_container_width=True)

  with col_t2:
    st.subheader("Data Transaksi Terfilter")
    st.dataframe(
        filtered_df[[
            "transaction_id",
            "coffee_name",
            "store_location",
            "payment_method",
            "quantity",
            "total_sales",
        ]],
        use_container_width=True,
    )

# --- FOOTER ---
st.markdown("---")
st.caption(
    "Coffee Shop Analytics Hub • Dibangun dengan Arsitektur Multi-DBMS"
)