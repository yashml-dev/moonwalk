
import streamlit as st
from location_component import location_tracker

st.set_page_config(page_title="MOONWALK GPS Test")
st.title("MOONWALK - GPS Test")

result = location_tracker()
location = getattr(result, "location", None)

if location:
    st.success("GPS coordinates received by Python!")
    st.write("Latitude:", location["latitude"])
    st.write("Longitude:", location["longitude"])
    st.write("Accuracy:", location["accuracy"], "metres")
else:
    st.info("Allow location access in your browser and wait for a GPS update.")
