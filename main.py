import streamlit as st
import pandas as pd
import time
import os

# Aumentar o limite de renderização do Styler do Pandas
pd.set_option("styler.render.max_elements", 1705232)

st.set_page_config(layout="wide")

# Definir o caminho do arquivo auxiliar
project_folder = os.path.dirname(__file__)  # Diretório do script atual
auxiliary_file_path = os.path.join(project_folder, 'auxiliar_file.csv')

def filter_columns(data, filter_data):
    """
    Exclude columns based on the 'Include/Exclude' value from the auxiliary spreadsheet.
    """
    # Normalize column names to lowercase
    data.columns = data.columns.str.lower()
    filter_data['Attribute'] = filter_data['Attribute'].str.lower()
    exclude_columns = filter_data[filter_data['Include/Exclude'].str.lower() == 'exclude']['Attribute'].tolist()
    filtered_data = data.drop(columns=exclude_columns, errors='ignore')
    return filtered_data


def compare_datasets(pim_data, ci_data):
    start_time = time.time()  # Start the processing timer

    # Tag each dataset with its source
    pim_data['source'] = 'PIM'
    ci_data['source'] = 'CI'

    # Combine both datasets
    combined_data = pd.concat([pim_data, ci_data], ignore_index=True)

    # Group by Material Bank SKU and filter groups with more than one element
    differences = combined_data.groupby('material bank sku').filter(lambda x: len(x) > 1)

    # Find rows that differ within the same group (same Material Bank SKU)
    discrepant_data = differences.drop_duplicates(subset=differences.columns.difference(['source']), keep=False)

    # Find rows that are identical within the same group (same Material Bank SKU)
    identical_data = differences[differences.duplicated(subset=differences.columns.difference(['source']), keep=False)]

    # Organize discrepancies into pairs
    paired_discrepancies = []
    for sku in discrepant_data['material bank sku'].unique():
        sku_discrepancies = discrepant_data[discrepant_data['material bank sku'] == sku]
        pim_discrepancy = sku_discrepancies[sku_discrepancies['source'] == 'PIM'].reset_index(drop=True)
        ci_discrepancy = sku_discrepancies[sku_discrepancies['source'] == 'CI'].reset_index(drop=True)
        paired_discrepancies.append(pim_discrepancy)
        paired_discrepancies.append(ci_discrepancy)
        paired_discrepancies.append(pd.DataFrame())  # Adds an empty row between pairs

    if paired_discrepancies:
        paired_discrepancies_df = pd.concat(paired_discrepancies, ignore_index=True)
    else:
        paired_discrepancies_df = pd.DataFrame()

    # Identificar SKUs exclusivos de cada dataset
    pim_skus = set(pim_data['material bank sku'])
    ci_skus = set(ci_data['material bank sku'])

    pim_unique_skus = pim_skus - ci_skus
    ci_unique_skus = ci_skus - pim_skus

    all_unique_skus = list(pim_unique_skus.union(ci_unique_skus))

    num_discrepant_rows = len(discrepant_data)
    num_identical = len(identical_data)

    processing_time = time.time() - start_time  # End the processing timer

    return paired_discrepancies_df, num_discrepant_rows, num_identical, all_unique_skus, processing_time


def icon():
    # Inclui o CSS da FontAwesome
    fontawesome_css = "<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css'>"
    st.markdown(fontawesome_css, unsafe_allow_html=True)  # Isso só precisa ser feito uma vez na aplicação

    # HTML para o ícone da câmera ao lado do texto "Image Scraper"
    icon_and_text_html = (
        '<span style="font-size: 2em; display: flex; align-items: center;"><i class="fas fa-fingerprint" '
        'style="font-size: 120%; padding-right: 0.5em;"></i> DATA COMPARISON</span>')
    st.markdown(icon_and_text_html, unsafe_allow_html=True)


def load_data(file, chunksize=10000):
    data_chunks = []
    for chunk in pd.read_csv(file, chunksize=chunksize, dtype={'Material Bank SKU': str}, low_memory=False):
        data_chunks.append(chunk)
    return pd.concat(data_chunks, ignore_index=True)


@st.experimental_fragment
def download_csv_fragment(csv_data):
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name='discrepant_data.csv',
        mime='text/csv',
        type="primary"
    )


def main():
    icon()

    st.markdown("#")

    col1, col2 = st.columns(2)

    with col1:
        pim_file = st.file_uploader("Select PIM CSV file", type="csv")

    with col2:
        ci_file = st.file_uploader("Select CI CSV file", type="csv")

    st.sidebar.subheader("PIM-CI Checker Tool", divider="green")

    if pim_file is not None and ci_file is not None:
        with st.spinner('Loading PIM data...'):
            pim_data = load_data(pim_file)

        with st.spinner('Loading CI data...'):
            ci_data = load_data(ci_file)

        with st.spinner('Loading Filter data...'):
            filter_data = pd.read_csv(auxiliary_file_path)

        # Apply column filters
        pim_data = filter_columns(pim_data, filter_data)
        ci_data = filter_columns(ci_data, filter_data)

        # Contar e exibir o número de linhas preenchidas para cada dataset
        num_filled_pim = pim_data.dropna(how='all').shape[0]
        num_filled_ci = ci_data.dropna(how='all').shape[0]
        total_diff = abs(num_filled_pim - num_filled_ci)

        stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns([1, .7, .9, .8, 1])

        with st.spinner('Processing statistics...'):
            paired_discrepancies_df, num_discrepant, num_identical, unique_skus, processing_time = compare_datasets(
                pim_data, ci_data)

        with stat_col1:
            st.subheader("Data Upload Statistics", divider='blue')
            st.write(f"Number of filled rows in PIM dataset: {num_filled_pim}")
            st.write(f"Number of filled rows in CI dataset: {num_filled_ci}")
            st.write(f"Difference between datasets: {total_diff} rows")

        with stat_col3:
            st.subheader("Datasets Statistics", divider='green')
            st.write(f"Number of identical rows: {num_identical}")
            st.write(f"Number of discrepant rows: {num_discrepant}")
            st.write(f"Processing time: {processing_time:.2f} seconds")

        with stat_col1:
            st.markdown("##")
            st.subheader("Download Data")
            csv_data = paired_discrepancies_df.to_csv(index=False).encode('utf-8')
            download_csv_fragment(csv_data)

        with stat_col5:
            if num_discrepant > 0:
                st.subheader("Discrepant MB SKUs", divider='orange')
                st.dataframe(pd.DataFrame(unique_skus, columns=["Material Bank SKU"]).astype(str))

        if num_discrepant == 0:
            st.success("No discrepant records found between the datasets.")


if __name__ == "__main__":
    main()
