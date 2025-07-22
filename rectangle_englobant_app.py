import streamlit as st
import math
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

# --- Fonctions de formes géométriques ---
def losange_points_cote_angle(cote, angle_deg):
    angle_rad = math.radians(angle_deg)
    dx = cote * math.cos(angle_rad / 2)
    dy = cote * math.sin(angle_rad / 2)
    return [(-dx, 0), (0, dy), (dx, 0), (0, -dy)]

def losange_points_diagonales(d1, d2):
    return [(-d1 / 2, 0), (0, d2 / 2), (d1 / 2, 0), (0, -d2 / 2)]

def trapeze_points(base1, base2, hauteur):
    dx = (base1 - base2) / 2
    return [(-base1 / 2, 0), (base1 / 2, 0), (base2 / 2, hauteur), (-base2 / 2, hauteur)]

def parallelogramme_points(base, cote, angle_deg):
    angle_rad = math.radians(angle_deg)
    dx = cote * math.cos(angle_rad)
    dy = cote * math.sin(angle_rad)
    return [(0, 0), (base, 0), (base + dx, dy), (dx, dy)]

# --- Calcul du rectangle englobant ---
def minimum_bounding_rectangle(points):
    poly = Polygon(points)
    rect = poly.minimum_rotated_rectangle
    return list(rect.exterior.coords)[:-1]

# --- Dessin de la forme et du rectangle ---
def draw_shape_and_rectangle(shape_pts, rect_pts):
    fig, ax = plt.subplots()

    # Tracer la forme
    shape_poly = Polygon(shape_pts)
    x, y = shape_poly.exterior.xy
    ax.fill(x, y, alpha=0.5, label="Forme")

    # Tracer le rectangle englobant
    rect_poly = Polygon(rect_pts)
    x_rect, y_rect = rect_poly.exterior.xy
    ax.plot(x_rect, y_rect, 'r--', label="Rectangle englobant")

    # Affichage des dimensions sur les côtés
    # Supposé : ordre des points rect_pts = [p0, p1, p2, p3]
    p0, p1, p2, p3 = rect_pts
    mid_top = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    mid_right = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

    width = round(math.dist(p0, p1), 2)
    height = round(math.dist(p1, p2), 2)

    ax.text(*mid_top, f"{width}", color='red', fontsize=12, ha='center', va='bottom', backgroundcolor='white')
    ax.text(*mid_right, f"{height}", color='red', fontsize=12, ha='left', va='center', rotation=90, backgroundcolor='white')

    ax.axis('equal')
    ax.legend()
    return fig


# --- Export PDF ---
def export_pdf(points, rect, titre="Rectangle englobant"):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, height - 70, titre)

    # Dimensions
    rect_width = round(math.dist(rect[0], rect[1]), 2)
    rect_height = round(math.dist(rect[1], rect[2]), 2)

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, height - 90, f"Largeur : {rect_width}")
    pdf.drawString(100, height - 110, f"Hauteur : {rect_height}")

    # Schéma simple (optionnel)
    scale = 20
    offset_x = 100
    offset_y = 400

    def draw_poly(poly, color):
        pdf.setStrokeColor(color)
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            pdf.line(offset_x + x1 * scale, offset_y + y1 * scale,
                     offset_x + x2 * scale, offset_y + y2 * scale)

    draw_poly(points, color="black")
    draw_poly(rect, color="red")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# --- Interface Streamlit ---
def main():
    st.title("📐 Calcul du rectangle englobant")
    forme = st.selectbox("Choisir une forme :", [
        "Losange (côté + angle)",
        "Losange (2 diagonales)",
        "Trapèze isocèle",
        "Parallélogramme"
    ])

    points = []
    if forme == "Losange (côté + angle)":
        cote = st.number_input("Longueur du côté (mm)", value=1000, min_value=1)
        angle = st.number_input("Angle en degrés", value=60.0, min_value=1.0, max_value=179.0)
        points = losange_points_cote_angle(cote, angle)

    elif forme == "Losange (2 diagonales)":
        d1 = st.number_input("Diagonale 1 (mm)", value=1000, min_value=1)
        d2 = st.number_input("Diagonale 2 (mm)", value=600, min_value=1)
        points = losange_points_diagonales(d1, d2)

    elif forme == "Trapèze isocèle":
        base1 = st.number_input("Grande base (mm)", value=1000, min_value=1)
        base2 = st.number_input("Petite base (mm)", value=600, min_value=1)
        hauteur = st.number_input("Hauteur (mm)", value=400, min_value=1)
        points = trapeze_points(base1, base2, hauteur)

    elif forme == "Parallélogramme":
        base = st.number_input("Longueur de la base (mm)", value=1000, min_value=1)
        cote = st.number_input("Longueur du côté adjacent (mm)", value=600, min_value=1)
        angle = st.number_input("Angle entre base et côté (°)", value=60.0, min_value=1.0, max_value=179.0)
        points = parallelogramme_points(base, cote, angle)

    if points:
        rect = minimum_bounding_rectangle(points)
        fig = draw_shape_and_rectangle(points, rect)
        st.pyplot(fig)

        # Dimensions rectangle englobant
        rect_width = round(math.dist(rect[0], rect[1]), 2)
        rect_height = round(math.dist(rect[1], rect[2]), 2)

        st.success("📏 Dimensions du rectangle englobant :")
        st.markdown(f"**Largeur** : {rect_width} mm")
        st.markdown(f"**Hauteur** : {rect_height} mm")

        # Export PDF
        if st.button("📄 Exporter en PDF"):
            pdf_buffer = export_pdf(points, rect, titre="Rectangle englobant de la forme")
            st.download_button("Télécharger le PDF", pdf_buffer, file_name="rectangle_englobant.pdf")

if __name__ == "__main__":
    main()



#python -m streamlit run rectangle_englobant_app.py