import requests




def get_ability_description(ability_url):
    """
    Fetches the English description for a given ability from the PokeAPI.

    Parameters:
        ability_url (str): The URL endpoint for the ability's details.

    Returns:
        str: The ability's description in English, or a message if not available.
    """
    ability_response = requests.get(ability_url)

    if ability_response.status_code == 200:
        ability_data = ability_response.json()

        # Find the English description and remove line breaks
        description = next(
            (entry['effect'].replace("\n", " ")
             for entry in ability_data['effect_entries']
             if entry['language']['name'] == "en"),
            "Description not available"
        )
        return description
    else:
        return "Description could not be retrieved."