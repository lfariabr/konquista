import requests

class GraphQLClient:

    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}', 
        }

    def execute(self, query, variables=None):
        payload = {
            'query': query,
            'variables': variables
        }

        response = requests.post(self.base_url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()