import streamlit as st

from booking_booking.webapp import analyzer_view

st.set_page_config(page_title="Booking Booking - Analyzer", page_icon="📊", layout="wide")

analyzer_view.render()
