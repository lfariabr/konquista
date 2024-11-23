import os
import pandas as pd
from flask import request, jsonify
from werkzeug.utils import secure_filename
from ..apicrmgraphql.dicts import dic_store_ident, dic_region_ident, stores, region_map, ddd_dict

def clean_phone_number(number):
    # Remove any non-digit characters, except for leading '+' 
    cleaned = ''.join(filter(lambda x: x.isdigit() or x == '+', str(number)))
    # If the number starts with '55'
    if cleaned.startswith('55'):
        # Remove the first two characters ('55') if the number is longer than 11 digits
        return cleaned[2:] if len(cleaned) > 11 else cleaned
    return cleaned

# Versão 1.0 - sem considerar Tag/Region/Store
# Função para processar os arquivos CSV
def process_csv_files_v1(botox_file_path=None, preenchimento_file_path=None):
    df_list = []

    try:
        if botox_file_path:
            # Ensure the file exists and is read correctly
            df_botox = pd.read_csv(botox_file_path)
            df_botox['filename'] = 'botox'  # Adiciona a coluna 'filename' com o valor 'botox'
            df_list.append(df_botox)

        if preenchimento_file_path:
            df_preenchimento = pd.read_csv(preenchimento_file_path)
            df_preenchimento['filename'] = 'preenchimento'  # Adiciona a coluna 'filename' com o valor 'preenchimento'
            df_list.append(df_preenchimento)

        # If no files were processed, return an empty DataFrame
        if not df_list:
            return pd.DataFrame()

        # Combina todos os DataFrames em um só
        df_leads_whatsapp = pd.concat(df_list, ignore_index=True)

        # Realize aqui o processamento necessário nos DataFrames
        df_leads_whatsapp['Whatsapp'] = df_leads_whatsapp['Whatsapp'].astype(str)
        df_leads_whatsapp['Whatsapp'] = df_leads_whatsapp['Whatsapp'].apply(clean_phone_number)

        return df_leads_whatsapp

    except Exception as e:
        # Handle exceptions like missing files or bad CSV formatting
        print(f"Error processing CSV files: {str(e)}")
        return None
    
# Process CSV v2.0 - considering Tag/Region/Store
def process_csv_files(botox_file_path=None, preenchimento_file_path=None):
    df_list = []
    # *task* maybe here we'll need to write conditions
    # to not make mandatory both of botox_file_path and preenchimento_file_path
    # maybe user is gonna upload only one... or three.. 
    # and want to have "tags" or "filename" option to chose from
    try:
        if botox_file_path:
            # Ensure the file exists and is read correctly
            df_botox = pd.read_csv(botox_file_path)
            df_botox['filename'] = 'botox'  
            # Adiciona a coluna 'filename' com o valor 'botox'
            df_list.append(df_botox)

        if preenchimento_file_path:
            df_preenchimento = pd.read_csv(preenchimento_file_path)
            df_preenchimento['filename'] = 'preenchimento'  # Adiciona a coluna 'filename' com o valor 'preenchimento'
            df_list.append(df_preenchimento)

        # If no files were processed, return an empty DataFrame
        if not df_list:
            return pd.DataFrame()

        # Combining all DataFrames in a single one
        df_leads_whatsapp = pd.concat(df_list, ignore_index=True)

        # Processing whatsapp column
        df_leads_whatsapp['Whatsapp'] = df_leads_whatsapp['Whatsapp'].astype(str)
        df_leads_whatsapp['Whatsapp'] = df_leads_whatsapp['Whatsapp'].apply(clean_phone_number)

       # Ensuring "Tags" is uppercase and string type
        default_tag = "SEM TAGS"
        df_leads_whatsapp['Tags'] = df_leads_whatsapp['Tags'].fillna(default_tag)
        df_leads_whatsapp['Tags'] = df_leads_whatsapp['Tags'].replace('NAN', default_tag)
        df_leads_whatsapp['Tags'] = df_leads_whatsapp['Tags'].str.upper().astype(str)
        
        # Applying Unidade and Região based on 'Tags'
        df_leads_whatsapp['Unidade'] = df_leads_whatsapp['Tags'].apply(create_stores)
        df_leads_whatsapp['Região'] = df_leads_whatsapp['Tags'].apply(create_regions)

        # Extracting DDD from Whatsapp number
        df_leads_whatsapp['DDD'] = df_leads_whatsapp['Whatsapp'].astype(str).str[:2]

        # Mapping Região based on DDD using ddd dict
        default_region = 'DDD aleatório'
        df_leads_whatsapp['Região_DDD'] = df_leads_whatsapp['DDD'].map(ddd_dict).fillna(default_region)

        # Option 1: Overwrite 'Região' with 'Região_DDD' NOT WORKING
        # df_leads_whatsapp['Região'] = df_leads_whatsapp['Região_DDD']

        # Option 2: Fill missing 'Região' values with 'Região_DDD'
        # df_leads_whatsapp['Região'] = df_leads_whatsapp['Região'].fillna(df_leads_whatsapp['Região_DDD'])
        
        # Option 3: testing
        default_region = 'São Paulo'
        # Replacing default region with região_ddd when appropriate
        df_leads_whatsapp['Região'] = df_leads_whatsapp.apply(
            lambda row: row['Região_DDD'] if row['Região'] == default_region or pd.isnull(row['Região']) else row['Região'],
            axis=1
        )

        # Dropping the aux 'Região_DDD' column
        df_leads_whatsapp.drop(columns=['Região_DDD'], inplace=True)

        return df_leads_whatsapp

    except Exception as e:
        print(f"Error processing CSV files: {str(e)}")
        return None
        
# Stores definition
def create_stores(tag):
    return next((store for store in stores if store in tag), 'CENTRAL')

# Region Definition
def create_regions(tag):
    return region_map.get(next((region for region in region_map if region in tag), 'CENTRAL'), 'São Paulo')
