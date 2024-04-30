import streamlit as st
import pandas as pd
import time

st.set_page_config(layout="wide")


def compare_datasets(pim_data, ci_data):
    start_time = time.time()  # Start the processing timer

    # Tag each dataset with its source
    pim_data['source'] = 'PIM'
    ci_data['source'] = 'CI'

    # Combine both datasets
    combined_data = pd.concat([pim_data, ci_data], ignore_index=True)

    # Group by MB SKU and filter groups with more than one element
    differences = combined_data.groupby('MB SKU').filter(lambda x: len(x) > 1)

    # Find rows that differ within the same group (same MB SKU)
    discrepant_data = differences.drop_duplicates(subset=differences.columns.difference(['source']), keep=False)

    # Organize discrepancies into pairs
    paired_discrepancies = []
    for sku in discrepant_data['MB SKU'].unique():
        sku_discrepancies = discrepant_data[discrepant_data['MB SKU'] == sku]
        pim_discrepancy = sku_discrepancies[sku_discrepancies['source'] == 'PIM'].reset_index(drop=True)
        ci_discrepancy = sku_discrepancies[sku_discrepancies['source'] == 'CI'].reset_index(drop=True)
        paired_discrepancies.append(pim_discrepancy)
        paired_discrepancies.append(ci_discrepancy)
        paired_discrepancies.append(pd.DataFrame())  # Adds an empty row between pairs

    paired_discrepancies_df = pd.concat(paired_discrepancies, ignore_index=True)

    # Apply style to highlight differences in red
    def highlight_diff(row):
        if pd.isnull(row['MB SKU']):
            return [''] * len(row)
        else:
            mb_sku = row['MB SKU']
            pim_row = paired_discrepancies_df[
                (paired_discrepancies_df['MB SKU'] == mb_sku) & (paired_discrepancies_df['source'] == 'PIM')]
            ci_row = paired_discrepancies_df[
                (paired_discrepancies_df['MB SKU'] == mb_sku) & (paired_discrepancies_df['source'] == 'CI')]
            return ['background-color: red' if col != 'source' and pim_row.iloc[0][col] != ci_row.iloc[0][col] else ''
                    for col in paired_discrepancies_df.columns]

    styled_df = paired_discrepancies_df.style.apply(highlight_diff, axis=1)

    num_discrepant = len(discrepant_data)
    num_identical = len(combined_data) - num_discrepant  # Assuming all other rows are identical

    processing_time = time.time() - start_time  # End the processing timer

    return styled_df, num_discrepant, num_identical, processing_time


def icon():
    """
        Embeds FontAwesome CSS into a Streamlit app and displays a title with an icon.

        This function inserts the FontAwesome stylesheet into the app to enable icon usage
        and then displays a custom HTML snippet that combines a camera icon with the text
        "Image Scraper". The insertion of the CSS link is intended to be done once per app
        lifecycle to provide iconography support throughout the app.
    """
    # Inclui o CSS da FontAwesome
    fontawesome_css = "<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css'>"
    st.markdown(fontawesome_css, unsafe_allow_html=True)  # Isso só precisa ser feito uma vez na aplicação

    # HTML para o ícone da câmera ao lado do texto "Image Scraper"
    icon_and_text_html = (
        '<span style="font-size: 2em; display: flex; align-items: center;"><i class="fas fa-fingerprint" '
        'style="font-size: 120%; padding-right: 0.5em;"></i> DATA COMPARISON</span>')
    st.markdown(icon_and_text_html, unsafe_allow_html=True)


def main():
    # st.header("PIM and CI Dataset Comparison", divider="orange")
    icon()

    st.markdown("#")

    col1, col2 = st.columns(2)

    with col1:

        pim_file = st.file_uploader("Select PIM CSV file", type="csv")

    with col2:

        ci_file = st.file_uploader("Select CI CSV file", type="csv")

    if pim_file is not None and ci_file is not None:
        col3, col4, col5, col6 = st.columns([1, .5, 2.85, 1.5])

        pim_data = pd.read_csv(pim_file)
        ci_data = pd.read_csv(ci_file)

        styled_discrepant_data, num_discrepant, num_identical, processing_time = compare_datasets(pim_data, ci_data)

        with col3:
            st.subheader("Datasets Statistics")
            with st.container(border=True):
                st.write(f"Number of identical rows: {num_identical}")
                st.write(f"Number of discrepant rows: {num_discrepant}")
                st.write(f"Processing time: {processing_time:.2f} seconds")

        if num_discrepant > 0:
            with col5:
                st.subheader("Discrepant Records")
                with st.container(border=True, height=320):
                    st.markdown("#")
                    st.dataframe(styled_discrepant_data, hide_index=True)
        else:
            st.success("No discrepant records found between the datasets.")


if __name__ == "__main__":
    main()

# def compare_datasets(pim_data, ci_data):
#     # Marca cada dataset com sua origem
#     pim_data['source'] = 'PIM'
#     ci_data['source'] = 'CI'
#
#     # Junta ambos os datasets
#     combined_data = pd.concat([pim_data, ci_data], ignore_index=True)
#
#     # Agrupa por MB SKU e filtra grupos com mais de um elemento
#     differences = combined_data.groupby('MB SKU').filter(lambda x: len(x) > 1)
#
#     # Encontra linhas diferentes dentro do mesmo grupo (mesmo MB SKU)
#     discrepant_data = differences.drop_duplicates(subset=differences.columns.difference(['source']), keep=False)
#
#     # Organiza as discrepâncias em pares
#     paired_discrepancies = []
#     for sku in discrepant_data['MB SKU'].unique():
#         sku_discrepancies = discrepant_data[discrepant_data['MB SKU'] == sku]
#         pim_discrepancy = sku_discrepancies[sku_discrepancies['source'] == 'PIM'].reset_index(drop=True)
#         ci_discrepancy = sku_discrepancies[sku_discrepancies['source'] == 'CI'].reset_index(drop=True)
#         paired_discrepancies.append(pim_discrepancy)
#         paired_discrepancies.append(ci_discrepancy)
#         paired_discrepancies.append(pd.DataFrame())  # Adiciona uma linha vazia entre pares
#
#     paired_discrepancies_df = pd.concat(paired_discrepancies, ignore_index=True)
#
#     return paired_discrepancies_df
