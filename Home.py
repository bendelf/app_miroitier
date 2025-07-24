
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Accueil", page_icon="🏠")
st.title("Bienvenue dans l'application ToolBox Miroiterie Dignoise")
st.write("Utilisez le menu à gauche pour naviguer entre les pages.")
st.image(Image.open('./images/logo_miroiterie.png'))