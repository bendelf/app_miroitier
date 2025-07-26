import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

# Stockage des données en session
if "pieces" not in st.session_state:
    st.session_state.pieces = []
if "commande_info" not in st.session_state:
    st.session_state.commande_info = {
        "reference": "",
        "couleur": "",
        "face": "Intérieure"
    }

st.title("Commande de Tôles Pliées")

st.subheader("Informations générales")

st.session_state.commande_info["reference"] = st.text_input("Référence de commande", value=st.session_state.commande_info["reference"])
st.session_state.commande_info["couleur"] = st.text_input("Couleur (ex : Blanc RAL 9010)", value=st.session_state.commande_info["couleur"])
st.session_state.commande_info["face"] = st.selectbox("Face laquée", ["Intérieure", "Extérieure", "Deux faces"], index=["Intérieure", "Extérieure", "Deux faces"].index(st.session_state.commande_info["face"]))

st.subheader("Ajouter une pièce")

with st.form("ajout_piece"):
    type_piece = st.selectbox("Type de profil", ["Cornière égale", "Cornière inégale", "Profil Z"])

    if type_piece == "Cornière égale":
        a = st.number_input("Aile A (mm)", min_value=10, max_value=1000, value=50)
        b = a
        c = None
    elif type_piece == "Cornière inégale":
        a = st.number_input("Aile A (mm)", min_value=10, max_value=1000, value=40)
        b = st.number_input("Aile B (mm)", min_value=10, max_value=1000, value=60)
        c = None
    else:  # Profil Z
        a = st.number_input("Aile A (mm)", min_value=10, max_value=1000, value=30)
        b = st.number_input("Aile B (mm)", min_value=10, max_value=1000, value=50)
        c = st.number_input("Aile C (mm)", min_value=10, max_value=1000, value=30)

    epaisseur = st.number_input("Épaisseur (mm)", min_value=1.0, max_value=20.0, value=2.0, step=0.5)
    longueur = st.number_input("Longueur (mm)", min_value=100, max_value=6000, value=1000)
    quantite = st.number_input("Quantité", min_value=1, max_value=100, value=1)

    submitted = st.form_submit_button("Ajouter")

    if submitted:
        piece = {
            "type": type_piece,
            "A": a,
            "B": b,
            "C": c,
            "epaisseur": epaisseur,
            "longueur": longueur,
            "quantite": quantite,
            "couleur": st.session_state.commande_info["couleur"],
            "face": st.session_state.commande_info["face"]
        }
        st.session_state.pieces.append(piece)
        st.success("Pièce ajoutée à la commande.")

st.subheader("Commande en cours")

for i, piece in enumerate(st.session_state.pieces):
    col1, col2 = st.columns([4, 1])
    with col1:
        desc = f"{piece['quantite']}x {piece['type']} - A={piece['A']} B={piece['B']}"
        if piece['type'] == "Profil Z":
            desc += f" C={piece['C']}"
        desc += f" L={piece['longueur']} mm, ép. {piece['epaisseur']} mm - {piece['couleur']} - {piece['face']}"
        st.text(desc)
    with col2:
        if st.button("Supprimer", key=f"suppr_{i}"):
            st.session_state.pieces.pop(i)
            st.experimental_rerun()

# Fonctions de dessin

def dessiner_piece(piece):
    fig, ax = plt.subplots(figsize=(3, 2.5))
    a, b, c = piece["A"], piece["B"], piece.get("C")
    ep = piece["epaisseur"]

    if piece["type"] in ["Cornière égale", "Cornière inégale"]:
        ax.plot([0, 0, ep, ep, a, a, 0], [0, b, b, ep, ep, 0, 0], color="black")
        ax.text(a / 2, -3, f"A = {a} mm", ha="center", va="top", fontsize=8)
        ax.text(-3, b / 2, f"B = {b} mm", ha="right", va="center", rotation=90, fontsize=8)
    elif piece["type"] == "Profil Z":
        # Tracé d’un Z : ailes a, b, c séparées par épaisseurs
        x = [0, a, a, a + ep, a + ep, a + b, a + b, a + b + ep, a + b + ep, a + b + ep + c, a + b + ep + c, 0, 0]
        y = [0, 0, ep, ep, -b, -b, -b - ep, -b - ep, -b - ep + ep, -b - ep + ep, 0, 0, 0]
        ax.plot(x, y, color="black")
        ax.text(a / 2, 3, f"A = {a} mm", ha="center", va="bottom", fontsize=8)
        ax.text(a + b / 2, -b / 2, f"B = {b} mm", ha="center", va="center", fontsize=8)
        ax.text(a + b + c / 2, 3, f"C = {c} mm", ha="center", va="bottom", fontsize=8)

    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig)
    return fig

if st.session_state.pieces:
    st.subheader("Aperçu du dernier dessin")
    dessiner_piece(st.session_state.pieces[-1])

# PDF Export

def export_pdf(pieces):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for piece in pieces:
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Commande de Tôle Pliée", ln=True, align='C')
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Référence : {st.session_state.commande_info['reference']}", ln=True)
        pdf.cell(200, 10, txt=f"Type : {piece['type']}", ln=True)
        dims = f"A={piece['A']} mm, B={piece['B']} mm"
        if piece['C']: dims += f", C={piece['C']} mm"
        pdf.cell(200, 10, txt=f"Dimensions : {dims}", ln=True)
        pdf.cell(200, 10, txt=f"Longueur : {piece['longueur']} mm, Épaisseur : {piece['epaisseur']} mm", ln=True)
        pdf.cell(200, 10, txt=f"Quantité : {piece['quantite']}", ln=True)
        pdf.cell(200, 10, txt=f"Couleur : {piece['couleur']}, Face laquée : {piece['face']}", ln=True)

        fig = dessiner_piece(piece)
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig.savefig(tmpfile.name)
        plt.close(fig)
        pdf.image(tmpfile.name, x=30, y=80, w=140)
        os.unlink(tmpfile.name)

    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    return tmp_pdf.name

if st.button("📄 Exporter en PDF"):
    if st.session_state.pieces:
        pdf_path = export_pdf(st.session_state.pieces)
        with open(pdf_path, "rb") as f:
            st.download_button("Télécharger le PDF", data=f, file_name="commande_toles.pdf", mime="application/pdf")
        os.remove(pdf_path)
    else:
        st.warning("Aucune pièce à exporter.")
