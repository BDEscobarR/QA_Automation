import pandas as pd

df = pd.read_excel("Bateria_QA_BNET_General.xlsx")

for _, row in df.iterrows():
    if row["Automatizable"] == "SI":
        print(f"Crear test: {row['ID']}")