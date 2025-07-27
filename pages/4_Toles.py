import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
from fpdf import FPDF
import os

# À faire une seule fois au début
#font_bold = ImageFont.truetype("arial.ttf", 14)
#font = ImageFont.truetype("arial.ttf", 12)

st.set_page_config(page_title="Commande de Tôles", layout="wide")

# --- Stockage temporaire ---
if "toles" not in st.session_state:
    st.session_state["toles"] = []

# --- Infos générales ---
st.title("Commande de Tôles")

col1, col2 = st.columns(2)
with col1:
    fournisseur = st.text_input("Fournisseur")
with col2:
    reference_chantier = st.text_input("Référence chantier")

st.markdown("---")

# --- Ajout d'une tôle ---
st.header("Ajouter une tôle")

col1, col2, col3 = st.columns(3)
with col1:
    metal = st.selectbox("Type de métal", ["Aluminium", "Acier", "Inox"])
    epaisseur = st.selectbox("Épaisseur (mm)", ["15/10ème", "20/10ème", "30/10ème"])
    forme = st.selectbox("Forme", ["Cornière", "Profil Z", "Seuil", "Tôle en U"])
with col2:
    coloris = st.text_input("Coloris")
    laquage = st.selectbox("Côté laquage", ["Extérieur", "Intérieur"])
    finition = st.selectbox("Finition", ["Satiné", "Brillant", "Mat", "Texturé", "Autre"])
with col3:
    quantite = st.number_input("Quantité", min_value=1, step=1)
    longueur = st.number_input("Longueur (mm)", min_value=10, step=10)
    note = st.text_input("Note")

note_finition = ""
if finition == "Autre":
    note_finition = st.text_input("Précisez la finition")

# --- Dimensions ---
dimensions = {}
if forme in ["Cornière", "Cornière"]:
    dimensions["A"] = st.number_input("A (mm)", min_value=10, value=50)
    dimensions["B"] = st.number_input("B (mm)", min_value=10, value=70)
elif forme == "Profil Z":
    dimensions["A"] = st.number_input("A (mm)", min_value=10, value=50)
    dimensions["B"] = st.number_input("B (mm)", min_value=10, value=30)
    dimensions["C"] = st.number_input("C (mm)", min_value=10, value=70)
elif forme == "Seuil":
    dimensions["Largeur"] = st.number_input("Largeur (mm)", min_value=10, value=50)
    dimensions["Hauteur"] = st.number_input("Hauteur (mm)", min_value=10, value=30)
elif forme == "Tôle en U":
    dimensions["A"] = st.number_input("A (mm)", min_value=10, value=50)
    dimensions["B"] = st.number_input("B (mm)", min_value=10, value=40)
    dimensions["C"] = st.number_input("C (mm)", min_value=10, value=70)

if st.button("Ajouter la tôle"):
    st.session_state["toles"].append({
        "metal": metal,
        "epaisseur": epaisseur,
        "coloris": coloris,
        "laquage": laquage,
        "finition": finition,
        "note_finition": note_finition,
        "forme": forme,
        "dimensions": dimensions.copy(),
        "quantite": quantite,
        "longueur": longueur,
        "note": note
    })

# --- Dessin ---
def dessiner_schema(tole):
    img = Image.new("RGB", (300, 200), "white")
    draw = ImageDraw.Draw(img)

    def mm(x): return int(x * 1.5)
    def text_centered(text, x, y): draw.text((x, y), text, fill="black")

    forme = tole["forme"]
    d = tole["dimensions"]

    if forme == "Cornière":
        A, B = mm(d["A"]), mm(d["B"])
        draw.line([(50, 50), (50 + A, 50)], fill="black", width=2)
        draw.line([(50, 50), (50, 50 + B)], fill="black", width=2)
        text_centered(f"A={d['A']}", 50 + A // 2 - 15, 35)
        text_centered(f"B={d['B']}", 20, 50 + B // 2 - 5)

    elif forme == "Profil Z":
        A, B, C = mm(d["A"]), mm(d["B"]), mm(d["C"])
        x0, y0 = 50, 100
        path = [
            (x0, y0),
            (x0 + A, y0),
            (x0 + A, y0 - B),
            (x0 + A + C, y0 - B)
        ]
        draw.line(path, fill="black", width=2)
        text_centered(f"A={d['A']}", x0 + A // 2 - 10, y0 + 10)
        text_centered(f"B={d['B']}", x0 + A + 5, y0 - B // 2 - 5)
        text_centered(f"C={d['C']}", x0 + A + C // 2 - 10, y0 - B - 15)

    elif forme == "Seuil":
        L, H = mm(d["Largeur"]), mm(d["Hauteur"])
        x0, y0 = 50, 80
        draw.rectangle([x0, y0, x0 + L, y0 + H], outline="black", width=2)
        text_centered(f"Largeur={d['Largeur']}", x0 + L // 2 - 20, y0 - 15)
        text_centered(f"Hauteur={d['Hauteur']}", x0 - 40, y0 + H // 2 - 5)

    elif forme == "Tôle en U":
        A, B, C = mm(d["A"]), mm(d["B"]), mm(d["C"])
        x0, y0 = 50, 60
        draw.line([(x0, y0), (x0, y0 + A)], fill="black", width=2)
        draw.line([(x0, y0 + A), (x0 + B, y0 + A)], fill="black", width=2)
        draw.line([(x0 + B, y0 + A), (x0 + B, y0+A-C)], fill="black", width=2)
        text_centered(f"A={d['A']}", x0 - 35, y0 + A // 2 - 5)
        text_centered(f"B={d['B']}", x0 + B // 2 - 10, y0 + A + 5)
        text_centered(f"C={d['C']}", x0 + B + 5, y0 + d["C"] // 2)

    text = f"Laquage côté {tole['laquage']}"
    draw.text((10, 180), text, fill="red")  # position bas gauche

    return img

# --- Liste des tôles ---
st.markdown("## Tôles ajoutées")
for i, tole in enumerate(st.session_state["toles"]):
    finition_txt = tole['note_finition'] if tole['finition'] == "Autre" else tole['finition']
    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.write(
            f"🔹 {tole['forme']} - {tole['metal']} {tole['epaisseur']} - "
            f"{tole['coloris']} ({tole['laquage']} - {finition_txt}) - "
            f"{tole['quantite']}x{tole['longueur']}mm"
        )
        st.write(f"Dimensions : {tole['dimensions']}")
    with cols[1]:
        img = dessiner_schema(tole)
        st.image(img, use_container_width=True)
    with cols[2]:
        if st.button("❌ Supprimer", key=f"delete_{i}"):
            st.session_state["toles"].pop(i)
            st.session_state["refresh"] = not st.session_state.get("refresh", False)  # toggle un booléen

# --- PDF ---
import tempfile

def generer_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Fournisseur : {fournisseur}", ln=True)
    pdf.cell(200, 10, f"Référence chantier : {reference_chantier}", ln=True)
    pdf.ln(10)

    temp_dir = tempfile.gettempdir()

    for idx, tole in enumerate(st.session_state["toles"]):
        finition_txt = tole['note_finition'] if tole['finition'] == "Autre" else tole['finition']

        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, f"Tôle {idx+1} - {tole['forme']}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8,
            f"Métal : {tole['metal']}\n"
            f"Épaisseur : {tole['epaisseur']} \n"
            f"Coloris : {tole['coloris']}\n"
            f"Laquage : {tole['laquage']}\n"
            f"Finition : {finition_txt}\n"
            f"Dimensions : {tole['dimensions']}\n"
            f"Quantité : {tole['quantite']} x {tole['longueur']} mm\n"
            f"Note : {tole['note']}\n"
        )

        img = dessiner_schema(tole)
        img_path = os.path.join(temp_dir, f"tole_{idx}.png")
        img.save(img_path)
        pdf.image(img_path, w=100)
        pdf.ln(10)
        os.remove(img_path)

    return pdf.output(dest="S").encode("latin1")


if st.button("📄 Exporter en PDF"):
    pdf_data = generer_pdf()
    st.download_button("Télécharger le PDF", data=pdf_data, file_name="commande_tole.pdf", mime="application/pdf")