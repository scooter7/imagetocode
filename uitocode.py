import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from io import BytesIO
from PIL import Image

# Function to create a chart based on the user's input
def create_chart(columns, df, chart_type):
    fig = None
    if chart_type == "Bar Chart":
        if len(columns) == 2:
            data = df.groupby(columns).size().reset_index(name='counts')
            fig = px.bar(data, x=columns[0], y='counts', color=columns[1], barmode='group')
        else:
            st.write("Please select exactly two columns for the bar chart.")
    elif chart_type == "Line Chart":
        if len(columns) == 2:
            data = df.groupby(columns).size().reset_index(name='counts')
            fig = px.line(data, x=columns[0], y='counts', color=columns[1])
        else:
            st.write("Please select exactly two columns for the line chart.")
    elif chart_type == "Pie Chart":
        if len(columns) == 1:
            data = df[columns[0]].value_counts().reset_index()
            data.columns = [columns[0], 'counts']
            fig = px.pie(data, names=columns[0], values='counts')
        else:
            st.write("Please select exactly one column for the pie chart.")
    return fig

# Function to save Plotly figure as an image
def save_chart_as_image(fig):
    img_bytes = pio.to_image(fig, format="png")
    return img_bytes

# Streamlit UI
st.title("Infographic Creator")

# Upload CSV file
csv_file = st.file_uploader("Upload CSV", type=["csv"])
if csv_file:
    df = pd.read_csv(csv_file)
    st.write("Data Preview:")
    st.write(df)

    # Allow the user to select columns via checkboxes
    st.subheader("Select Columns for Chart/Table")
    selected_columns = []
    for column in df.columns:
        if st.checkbox(column):
            selected_columns.append(column)

    # Dropdown to select chart type
    chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Pie Chart", "Table"])

    # Generate chart or table based on selected columns and chart type
    fig = None
    if st.button("Generate Chart/Table"):
        if len(selected_columns) > 0:
            fig = create_chart(selected_columns, df, chart_type)
            if fig:
                st.plotly_chart(fig)
        else:
            st.write("Please select at least one column for the chart/table.")

    # Button to save chart as image and display it
    if fig and st.button("Save Chart as Image"):
        img_bytes = save_chart_as_image(fig)
        if img_bytes:
            st.image(img_bytes, caption="Saved Chart as Image", use_column_width=True)

            # Provide basic resizing options
            img = Image.open(BytesIO(img_bytes))
            width, height = img.size
            new_width = st.slider("Resize Image Width", min_value=50, max_value=width, value=width)
            new_height = st.slider("Resize Image Height", min_value=50, max_value=height, value=height)
            
            resized_img = img.resize((new_width, new_height))
            st.image(resized_img, caption="Resized Image", use_column_width=True)
