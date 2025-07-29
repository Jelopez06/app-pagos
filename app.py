
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Cálculo de Pagos - Oishii")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if archivo is not None:
    df_raw = pd.read_excel(archivo, sheet_name="Asistencia")

    colnames = ["FECHA", "DÍA", "EMPLEADO", "ENTRADA", "SALIDA_ALM", "ENTRADA_ALM", "SALIDA_G", "HRS_EXTRA"]
    bloque1 = df_raw.iloc[:, 0:8].copy()
    bloque1.columns = colnames

    bloque2 = df_raw.iloc[:, 9:17].copy()
    bloque2.columns = colnames

    df_total = pd.concat([bloque1, bloque2], ignore_index=True)
    df_total["FECHA"] = df_total["FECHA"].ffill()
    df_total["DÍA"] = df_total["DÍA"].ffill()
    df_total["HRS_EXTRA"] = pd.to_numeric(df_total["HRS_EXTRA"], errors="coerce").fillna(0)

    def convertir_hora(x):
        try:
            return pd.to_datetime(str(x).strip(), format="%H:%M").time()
        except:
            try:
                return pd.to_datetime(str(x).strip()).time()
            except:
                return None

    for col in ["ENTRADA", "SALIDA_ALM", "ENTRADA_ALM", "SALIDA_G"]:
        df_total[col] = df_total[col].apply(convertir_hora)

    df = df_total.dropna(subset=["ENTRADA", "SALIDA_G"]).copy()

    def calcular_horas(row):
        try:
            fmt = "%H:%M:%S"
            entrada = datetime.strptime(row["ENTRADA"].strftime(fmt), fmt)
            salida = datetime.strptime(row["SALIDA_G"].strftime(fmt), fmt)

            if pd.notna(row["SALIDA_ALM"]) and pd.notna(row["ENTRADA_ALM"]):
                salida_alm = datetime.strptime(row["SALIDA_ALM"].strftime(fmt), fmt)
                entrada_alm = datetime.strptime(row["ENTRADA_ALM"].strftime(fmt), fmt)
                bloque1 = (salida_alm - entrada).total_seconds() / 3600
                bloque2 = (salida - entrada_alm).total_seconds() / 3600
                horas = bloque1 + bloque2
            else:
                horas = (salida - entrada).total_seconds() / 3600

            return round(horas + row["HRS_EXTRA"], 2)
        except:
            return 0

    df["HORAS_TRABAJADAS"] = df.apply(calcular_horas, axis=1)
    df["PAGO"] = df["HORAS_TRABAJADAS"] * 1500

    # Agrupar por empleado
    desglose = df.groupby("EMPLEADO")[["HORAS_TRABAJADAS", "PAGO"]].sum().sort_values(by="PAGO", ascending=False)

    # Renombrar columnas a mayúsculas
    desglose = desglose.rename(columns={
        "HORAS_TRABAJADAS": "HORAS TRABAJADAS",
        "PAGO": "PAGO"
    })

    # Formato de columnas
    desglose["HORAS TRABAJADAS"] = desglose["HORAS TRABAJADAS"].round(2)
    desglose["PAGO"] = desglose["PAGO"].apply(lambda x: f"₡{x:,.0f}".replace(",", "."))

    # Total general
    pago_total = df["PAGO"].sum()
    pago_total_formateado = f"₡{pago_total:,.0f}".replace(",", ".")

    st.subheader("Desglose por empleado")
    st.dataframe(desglose)

    st.subheader("Pago total general")
    st.metric("Total a pagar", pago_total_formateado)
