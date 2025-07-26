import streamlit as st
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

# Stockage des pièces en session
if "pieces" not in st.session_state:
    st.session_state.pieces = []

st.title("Commande de Tôles Pliées - Cornières Égales")

st.subheader("Ajouter une cornière égale")

with st.form("ajout_corniere"):
    a = st.number_input("Largeur aile A (mm)", min_value=10, max_value=1000, value=50)
    epaisseur = st.number_input("Épaisseur (mm)", min_value=1.0, max_value=20.0, value=2.0, step=0.5)
    longueur = st.number_input("Longueur (mm)", min_value=100, max_value=6000, value=1000)
    quantite = st.number_input("Quantité", min_value=1, max_value=100, value=1)
    submitted = st.form_submit_button("Ajouter")

    if submitted:
        st.session_state.pieces.append({
            "type": "cornière égale",
            "A": a,
            "épaisseur": epaisseur,
            "longueur": longueur,
            "quantité": quantite
        })
        st.success("Cornière ajoutée à la commande.")

st.subheader("Commande en cours")

for i, piece in enumerate(st.session_state.pieces):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text(
            f"{piece['quantité']}x Cornière égale {piece['A']}x{piece['A']}x{piece['longueur']} mm (ép. {piece['épaisseur']} mm)")
    with col2:
        if st.button("Supprimer", key=f"supprimer_{i}"):
            st.session_state.pieces.pop(i)
            st.experimental_rerun()


def dessiner_corniere(a, epaisseur):
    fig, ax = plt.subplots(figsize=(4, 4))
    # Tracé d'une cornière égale en L
    ax.plot([0, 0, epaisseur, epaisseur, a, a, 0], [0, a, a, epaisseur, epaisseur, 0, 0], color="black")
    ax.set_aspect('equal')
    ax.set_xlim(-10, a + 20)
    ax.set_ylim(-10, a + 20)
    ax.axis('off')
    # Cotes
    ax.text(a / 2, -5, f"A = {a} mm", ha="center", va="top")
    ax.text(-5, a / 2, f"A = {a} mm", ha="right", va="center", rotation=90)
    ax.text(a + 5, epaisseur / 2, f"ép. = {epaisseur} mm", va="center")
    st.pyplot(fig)
    return fig


st.subheader("Aperçu du dessin")

if st.session_state.pieces:
    dernier = st.session_state.pieces[-1]
    dessiner_corniere(dernier["A"], dernier["épaisseur"])


# PDF export
def export_pdf(pieces):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for piece in pieces:
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Commande de Tôle Pliée - Cornière Égale", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10,
                 txt=f"{piece['quantité']}x Cornière {piece['A']}x{piece['A']}x{piece['longueur']} mm (ép. {piece['épaisseur']} mm)",
                 ln=True)

        # Dessin temporaire
        fig = dessiner_corniere(piece["A"], piece["épaisseur"])
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        fig.savefig(tmpfile.name)
        plt.close(fig)
        pdf.image(tmpfile.name, x=30, y=50, w=120)
        os.unlink(tmpfile.name)

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_pdf.name)
    return temp_pdf.name


if st.button("📄 Exporter en PDF"):
    if st.session_state.pieces:
        pdf_path = export_pdf(st.session_state.pieces)
        with open(pdf_path, "rb") as f:
            st.download_button("Télécharger le PDF", data=f, file_name="commande_cornieres.pdf", mime="application/pdf")
        os.remove(pdf_path)
    else:
        st.warning("Aucune pièce à exporter.")
