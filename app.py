import streamlit as st

from booking_booking.webapp import home_view

st.set_page_config(page_title="Booking Booking", page_icon="🏨", layout="wide")

home_view.render()
