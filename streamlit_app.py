import streamlit as st
import pandas as pd
import pdfkit
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
tz = pytz.timezone('US/Eastern')


st.title("House Budget Committee Speaking Order")

data = pd.read_csv("budget_committee_members.csv")
data["Member"] = data["Member"].str.split(" ")
data['First Name'] = data["Member"].apply(lambda x: x[0])
data["Member"] = data["Member"].apply(lambda x: x[1])


st.markdown(
    """
<style>
span[data-baseweb="tag"] {
  background-color: #004647 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

members_present = st.multiselect("Select the members present (or start typing):", data["Member"].tolist())
st.session_state.members_present = members_present

def speaking_order(present, data):
    # Filter data for present members
    data = data[data['Member'].isin(present)]
    
    # Sort Republicans and Democrats by rank
    republicans = data[data['Party'] == 'R'].sort_values('Rank')
    democrats = data[data['Party'] == 'D'].sort_values('Rank')
    
    # Interleave Republicans and Democrats
    order = {"Speaker" : [], "Party" : [], "Rank":[], "State":[]}
    for i in range(max(len(republicans), len(democrats))):
        if i < len(republicans):
            order["Speaker"].append(republicans.iloc[i]['First Name'] + " " + republicans.iloc[i]['Member'])
            order["Party"].append(republicans.iloc[i]['Party'])
            order["Rank"].append(republicans.iloc[i]['Rank'])
            order["State"].append(republicans.iloc[i]['State'])
        if i < len(democrats):
            order["Speaker"].append(democrats.iloc[i]["First Name"] + " " + democrats.iloc[i]['Member'])
            order["Party"].append(democrats.iloc[i]['Party'])
            order["Rank"].append(democrats.iloc[i]['Rank'])
            order["State"].append(democrats.iloc[i]['State'])
    order = pd.DataFrame(order)
    order["Order"] = order.index + 1
    
    return order

subtle_red = "#ffcccc"
subtle_blue = "#cce5ff"

def highlight_party(row):
     return [f'background-color: {subtle_red}']*len(row) if (row.Party == "R") else [f'background-color: {subtle_blue}']*len(row)

if st.button("Generate Speaking Order"):
    # Generate Speaking Order
    order = speaking_order(members_present, data)[["Speaker", "State", "Party", "Rank"]]
    order.reset_index(drop=True, inplace=True)
    order.index = order.index + 1
    # Style the Speaking Order
    styled = order.style.apply(highlight_party, axis=1)
    styled_pdf = order.drop(columns=["Rank"]).style.apply(highlight_party, axis=1)
    # Display Speaking Order
    html = styled.to_html(index=False)
    st.write(html, unsafe_allow_html=True)
    # Generate PDF html
    html_pdf = styled_pdf.to_html(index=False)
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %I:%M %p")   
    header_html = "<h1 style='text-align: center;'>House Budget Committee Speaking Order</h1>"
    timestamp_html = f"<h3 style='text-align: center;'>Generated at {timestamp}</h3>"
    html_pdf = header_html + timestamp_html + html_pdf
    html_pdf = html_pdf.replace('<table', '<table style="border-spacing: 0 5px;"')
    html_pdf = html_pdf.replace('<td', '<td style="padding: 0 15px;"')

    # Use BeautifulSoup to Remove Party Column
    soup = BeautifulSoup(html_pdf, 'html.parser')
    table = soup.find('table')
  
    for row in table.find_all('tr'):
        cells = row.find_all(["th", "td"])
        if len(cells) > 2:
            cells[3].extract()
         
    html_pdf = str(soup.prettify("utf-8", "html"))

    # Add a button to download the PDF
    pdf = pdfkit.from_string(html_pdf, False, options={"enable-local-file-access": ""})
    st.download_button(
        "⬇️ Download PDF",
        data=pdf,
        file_name=f"House Budget Committee Speaking Order.pdf",
    mime="application/octet-stream"
)