import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_FILE = 'garaz.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Zabezpečíme, že tabulka nastaveni existuje
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nastaveni (
            klic TEXT PRIMARY KEY,
            hodnota TEXT NOT NULL
        )
    ''')
    
    # Zabezpečíme, že tabulka auta existuje
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            znacka TEXT NOT NULL,
            model TEXT NOT NULL,
            rok INTEGER NOT NULL
        )
    ''')
    
    # Zabezpečíme, že tabulka servisy existuje
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servisy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auto_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            popis TEXT NOT NULL,
            najete_km INTEGER,
            cena REAL,
            FOREIGN KEY(auto_id) REFERENCES auta(id)
        )
    ''')
    
    # Migrace databáze: Pokud tabulka existuje ze starého skriptu, přidáme sloupec kategorie
    cursor.execute("PRAGMA table_info(servisy)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'kategorie' not in columns:
        cursor.execute("ALTER TABLE servisy ADD COLUMN kategorie TEXT DEFAULT 'Ostatní'")
        
    conn.commit()
    conn.close()

def get_auta():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, znacka, model, rok FROM auta", conn)
    conn.close()
    return df

def get_servisy(auto_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        "SELECT id, datum as Datum, kategorie as Kategorie, popis as Popis, najete_km as 'Najeto (km)', cena as 'Cena (Kč)' FROM servisy WHERE auto_id = ? ORDER BY datum DESC", 
        conn, params=(auto_id,)
    )
    conn.close()
    return df

def pridej_servis(auto_id, datum, kategorie, popis, najete_km, cena):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO servisy (auto_id, datum, kategorie, popis, najete_km, cena)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (auto_id, datum.strftime("%Y-%m-%d"), kategorie, popis, najete_km, cena))
    conn.commit()
    conn.close()

def smaz_servis(zaznam_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servisy WHERE id = ?", (int(zaznam_id),))
    conn.commit()
    conn.close()

def pridej_auto(znacka, model, rok):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM auta")
    pocet_aut = cursor.fetchone()[0]
    
    if pocet_aut < 5:
        cursor.execute("INSERT INTO auta (znacka, model, rok) VALUES (?, ?, ?)", (znacka, model, rok))
        conn.commit()
        success = True
    else:
        success = False
    conn.close()
    return success

def smaz_auto(auto_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Nejprve smažeme všechny servisní záznamy pro dané auto
    cursor.execute("DELETE FROM servisy WHERE auto_id = ?", (int(auto_id),))
    # Poté smažeme samotné auto
    cursor.execute("DELETE FROM auta WHERE id = ?", (int(auto_id),))
    conn.commit()
    conn.close()

def get_nastaveni(klic, default_hodnota):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT hodnota FROM nastaveni WHERE klic = ?", (klic,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default_hodnota

def set_nastaveni(klic, hodnota):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO nastaveni (klic, hodnota) VALUES (?, ?)", (klic, hodnota))
    conn.commit()
    conn.close()

# Nastavení stránky
st.set_page_config(page_title="Moje Digitální Garáž", page_icon="🚗", layout="centered")

init_db()

# Načtení tapety z databáze (záložní hodnota je temná fotka z Unsplash)
DEFAULT_BACKGROUND_IMAGE_URL = "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&q=80&w=1920"
aktualni_tapeta = get_nastaveni('tapeta', DEFAULT_BACKGROUND_IMAGE_URL)

# Vlastní CSS pro pozadí a vzhled
st.markdown(
    f"""
    <style>
    /* Import moderního fontu */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background-image: url("{aktualni_tapeta}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(0, 0, 0, 0.5); /* Trochu světlejší překryv pro lepší vyniknutí auta */
        z-index: -1;
    }}
    
    .main-title {{
        text-align: center;
        padding-bottom: 2rem;
        color: #ffffff;
        text-shadow: 2px 4px 10px rgba(0,0,0,0.8);
        font-weight: 800;
        font-size: 3.5rem;
        letter-spacing: -1px;
    }}
    
    /* Glassmorphism pro formulář (stForm) a panely (stVerticalBlockBorderWrapper) */
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(30, 30, 30, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 1.5rem !important;
    }}
    
    /* Vylepšení mezer a oddělení na stránce */
    .block-container {{
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 800px; /* Trochu užší design, aby lépe vynikl obrázek v pozadí */
    }}
    
    /* Stylování nadpisů h3 (např. '➕ Přidat nový servisní záznam') */
    h3 {{
        color: rgba(255, 255, 255, 0.95) !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Postranní panel pro správu aut
with st.sidebar:
    st.markdown("## ⚙️ Správa garáže")
    
    # Formulář pro přidání nového auta
    with st.form("pridat_auto_form", clear_on_submit=True):
        st.markdown("### Přidat nové vozidlo")
        znacka = st.text_input("Značka")
        model = st.text_input("Model")
        rok = st.number_input("Rok výroby", min_value=1900, max_value=2100, value=2020)
        submit_auto = st.form_submit_button("Přidat vozidlo", use_container_width=True)
        
        if submit_auto:
            if not znacka.strip() or not model.strip():
                st.error("Vyplňte prosím značku i model.")
            else:
                success = pridej_auto(znacka, model, rok)
                if success:
                    st.success("Auto bylo přidáno!")
                    st.rerun()
                else:
                    st.error("Kapacita garáže je plná (max. 5 aut)!")
                    
    st.divider()
    st.markdown("### Seznam vozidel")
    sidebar_auta_df = get_auta()
    if sidebar_auta_df.empty:
        st.info("Zatím žádná auta v garáži.")
    else:
        for index, row in sidebar_auta_df.iterrows():
            col1, col2 = st.columns([3, 1], vertical_alignment='center')
            with col1:
                st.markdown(f"**{row['znacka']} {row['model']}** ({row['rok']})")
            with col2:
                # Tlačítko pro smazání celého auta a jeho historie (zarovnáno doprava s využitím celé šířky)
                if st.button("🗑️", key=f"del_auto_{row['id']}", help="Odstranit vozidlo", use_container_width=True):
                    smaz_auto(row['id'])
                    st.rerun()

    st.divider()
    st.markdown("### 🎨 Vzhled aplikace")
    nova_tapeta = st.text_input("Zadejte URL adresu nové tapety", value="")
    if st.button("Změnit tapetu", use_container_width=True):
        if nova_tapeta.strip():
            set_nastaveni('tapeta', nova_tapeta.strip())
            st.rerun()
        else:
            st.error("URL nesmí být prázdná.")

st.markdown("<h1 class='main-title'>🚗 Moje Digitální Garáž</h1>", unsafe_allow_html=True)

# Výběr auta pro zobrazení historie
auta_df = get_auta()

if auta_df.empty:
    st.warning("V databázi zatím nemáte žádná auta. Přidejte je přes postranní panel ⚙️ Správa garáže.")
    st.stop()

st.markdown("### Výběr vozidla")
auta_list = auta_df.apply(lambda row: f"{row['znacka']} {row['model']} ({row['rok']}) - ID: {row['id']}", axis=1).tolist()
auta_ids = auta_df['id'].tolist()
auta_dict = dict(zip(auta_list, auta_ids))

selected_auto_str = st.radio("Vyberte auto pro zobrazení a správu záznamů:", auta_list, horizontal=True)
selected_auto_id = auta_dict[selected_auto_str]

st.divider()

if "popis_prace" not in st.session_state:
    st.session_state.popis_prace = ""

# Formulář pro zápis nového servisu
st.markdown("### ➕ Přidat nový servisní záznam")

if "zprava" in st.session_state:
    st.success(st.session_state.zprava)
    del st.session_state.zprava

# Použijeme st.container místo st.form, aby se zprávy dynamicky obnovovaly hned po výběru kategorie
with st.container(border=True):
    kategorie_options = ["Oleje a Filtry", "Brzdy", "Podvozek a Čepy", "Pneu", "Motor", "Ostatní"]
    
    col1, col2 = st.columns(2)
    with col1:
        datum = st.date_input("Datum servisu", datetime.today())
        kategorie = st.selectbox("Kategorie údržby", kategorie_options)
        
        # Dynamická nápověda
        if kategorie == 'Oleje a Filtry':
            st.info("💡 Doporučený interval: Motorový olej měnit každých 10 000 - 15 000 km. Palivový filtr (Fuel Filter) každých 40 000 - 80 000 km.")
        elif kategorie == 'Brzdy':
            st.info("💡 Doporučený interval: Brzdové destičky (Brake Pads) každých 30 000 - 70 000 km. Brzdové kotouče (Disc Brake) 80 000 - 120 000 km.")
        elif kategorie == 'Motor':
            st.info("💡 Doporučený interval: Zapalovací svíčky (Spark Plug) 30 000 - 50 000 km. Rozvodový řemen (Timing Belt) kontrola po 100 000 km.")
        else:
            st.info("💡 Pravidelná kontrola prodlužuje životnost vozidla.")
            
        najete_km = st.number_input("Stav tachometru (km)", min_value=0, step=1000)
    with col2:
        popis = st.text_input("Popis práce", key="popis_prace")
        cena = st.number_input("Cena opravy (Kč)", min_value=0.0, step=100.0)
        
    submit_button = st.button("💾 ULOŽIT ZÁZNAM", use_container_width=True)
    
    if submit_button:
        if not popis.strip():
            st.error("Vyplňte prosím popis práce.")
        else:
            pridej_servis(selected_auto_id, datum, kategorie, popis, najete_km, cena)
            # Vymažeme textové pole pro další zadávání
            st.session_state.popis_prace = ""
            st.session_state.zprava = "Záznam byl úspěšně uložen!"
            st.rerun()

st.divider()

# Výpis servisní historie
st.markdown(f"### 📜 Servisní historie pro vybrané vozidlo")
servisy_df = get_servisy(selected_auto_id)

if servisy_df.empty:
    st.info("Pro toto vozidlo zatím nebyly nalezeny žádné servisní záznamy.")
else:
    # Zobrazení historie pomocí st.container a smyčky pro každý záznam
    with st.container(border=True):
        for index, row in servisy_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 3, 2, 1], vertical_alignment="center")
            with col1:
                st.markdown(f"**{row['Datum']}**<br>_{row['Kategorie']}_", unsafe_allow_html=True)
            with col2:
                st.markdown(f"{row['Popis']}")
            with col3:
                st.markdown(f"**{row['Najeto (km)']} km**<br>{row['Cena (Kč)']} Kč", unsafe_allow_html=True)
            with col4:
                # Tlačítko pro smazání záznamu s unikátním klíčem (ID záznamu)
                if st.button("🗑️ Smazat", key=f"del_{row['id']}"):
                    smaz_servis(row['id'])
                    st.rerun()
            
            # Oddělovač mezi jednotlivými záznamy (vynecháme pod posledním)
            if index < len(servisy_df) - 1:
                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)