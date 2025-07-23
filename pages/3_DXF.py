import streamlit as st
import matplotlib.pyplot as plt
import ezdxf
import numpy as np
import tempfile

def plot_dxf_file(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    fig, ax = plt.subplots()

    for entity in msp:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            ax.plot([start.x, end.x], [start.y, end.y], 'b-')
        elif entity.dxftype() == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius
            circle = plt.Circle((center.x, center.y), radius, fill=False, color='green')
            ax.add_patch(circle)
        elif entity.dxftype() == "ARC":
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = np.radians(entity.dxf.start_angle)
            end_angle = np.radians(entity.dxf.end_angle)
            theta = np.linspace(start_angle, end_angle, 100)
            x = center.x + radius * np.cos(theta)
            y = center.y + radius * np.sin(theta)
            ax.plot(x, y, 'r-')
        elif entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
            try:
                points = entity.get_points()
                points = [p[0:2] for p in points]
            except AttributeError:
                points = [(v.dxf.x, v.dxf.y) for v in entity.vertices()]
            x, y = zip(*points)
            ax.plot(x, y, 'm-')

    ax.set_aspect('equal')
    ax.set_title("Aperçu du fichier DXF")
    ax.grid(True)
    return fig

def main():
    st.title("📐 Visionneuse DXF simple")

    uploaded_file = st.file_uploader("Chargez un fichier DXF", type=["dxf"])

    if uploaded_file is not None:
        # Enregistrement temporaire pour lecture par ezdxf
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        try:
            fig = plot_dxf_file(tmp_path)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Erreur : {e}")

if __name__ == "__main__":
    main()
