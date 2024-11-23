import os
from dotenv import load_dotenv

# load file variables from env file
load_dotenv(dotenv_path='.env')

# PRÓ-CORPO CRM 
# GRAPHQL
graphql_api_url = 'https://open-api.eprocorpo.com.br/graphql'
graphql_api_token = os.getenv('GRAPHQL_API_TOKEN')

# SOCIAL HUB
# API tokens
socialhub_api_url = 'https://apinew.socialhub.pro/api/'

socialhub_token_botox = os.getenv('SOCIALHUB_TOKEN_BOTOX')
socialhub_token_preench = os.getenv('SOCIALHUB_TOKEN_PREENCH')

#########
# Videos # isso aqui tem que ir pro message handler

socialhub_video_botox = '/content/drive/MyDrive/LUIS/WORK/18digital/pro-corpo/Lab Programação/projeto-botox-socialhub/botox.mp4'
socialhub_video_preench = '/content/drive/MyDrive/LUIS/WORK/18digital/pro-corpo/Lab Programação/projeto-botox-socialhub/preenchimento.mp4'
