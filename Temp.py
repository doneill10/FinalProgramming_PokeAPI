from flask import Flask, render_template, request
from collections import Counter
import requests
import openai

# Set your OpenAI API key
openai.api_key = None

app = Flask(__name__)

type_chart = {
    "Normal": {
        "weak_to": ["Fighting"],
        "resists": [],
        "immune": ["Ghost"]
    },
    "Fire": {
        "weak_to": ["Water", "Ground", "Rock"],
        "resists": ["Fire", "Grass", "Ice", "Bug", "Steel", "Fairy"],
        "immune": []
    },
    "Water": {
        "weak_to": ["Electric", "Grass"],
        "resists": ["Fire", "Water", "Ice", "Steel"],
        "immune": []
    },
    "Electric": {
        "weak_to": ["Ground"],
        "resists": ["Electric", "Flying", "Steel"],
        "immune": []
    },
    "Grass": {
        "weak_to": ["Fire", "Ice", "Poison", "Flying", "Bug"],
        "resists": ["Water", "Electric", "Grass", "Ground"],
        "immune": []
    },
    "Ice": {
        "weak_to": ["Fire", "Fighting", "Rock", "Steel"],
        "resists": ["Ice"],
        "immune": []
    },
    "Fighting": {
        "weak_to": ["Flying", "Psychic", "Fairy"],
        "resists": ["Bug", "Rock", "Dark"],
        "immune": []
    },
    "Poison": {
        "weak_to": ["Ground", "Psychic"],
        "resists": ["Grass", "Fighting", "Poison", "Bug", "Fairy"],
        "immune": []
    },
    "Ground": {
        "weak_to": ["Water", "Grass", "Ice"],
        "resists": ["Poison", "Rock"],
        "immune": ["Electric"]
    },
    "Flying": {
        "weak_to": ["Electric", "Ice", "Rock"],
        "resists": ["Grass", "Fighting", "Bug"],
        "immune": ["Ground"]
    },
    "Psychic": {
        "weak_to": ["Bug", "Ghost", "Dark"],
        "resists": ["Fighting", "Psychic"],
        "immune": []
    },
    "Bug": {
        "weak_to": ["Fire", "Flying", "Rock"],
        "resists": ["Grass", "Fighting", "Ground"],
        "immune": []
    },
    "Rock": {
        "weak_to": ["Water", "Grass", "Fighting", "Ground", "Steel"],
        "resists": ["Normal", "Fire", "Poison", "Flying"],
        "immune": []
    },
    "Ghost": {
        "weak_to": ["Ghost", "Dark"],
        "resists": ["Poison", "Bug"],
        "immune": ["Normal", "Fighting"]
    },
    "Dragon": {
        "weak_to": ["Ice", "Dragon", "Fairy"],
        "resists": ["Fire", "Water", "Electric", "Grass"],
        "immune": []
    },
    "Dark": {
        "weak_to": ["Fighting", "Bug", "Fairy"],
        "resists": ["Ghost", "Dark"],
        "immune": ["Psychic"]
    },
    "Steel": {
        "weak_to": ["Fire", "Fighting", "Ground"],
        "resists": [
            "Normal", "Grass", "Ice", "Flying", "Psychic", "Bug", "Rock", "Dragon", "Steel", "Fairy"
        ],
        "immune": ["Poison"]
    },
    "Fairy": {
        "weak_to": ["Poison", "Steel"],
        "resists": ["Fighting", "Bug", "Dark"],
        "immune": ["Dragon"]
    }
}

def calculate_team_weaknesses(team):
    weakness_count = Counter()

    # Loop through each Pokémon in the team
    for pokemon in team:
        for poke_type in pokemon.get("types", []):  # Get each type of the Pokémon
            # Add weaknesses for this type to the counter
            weaknesses = type_chart.get(poke_type, {}).get("weak_to", [])
            weakness_count.update(weaknesses)

    # Get the top 3 most common weaknesses
    top_weaknesses = weakness_count.most_common(3)
    return [weakness[0] for weakness in top_weaknesses]  # Return only the type names

# Store Pokémon slots in memory for simplicity
pokemon_slots = [None] * 6  # Six slots initialized as empty

@app.route("/", methods=["GET", "POST"])
def index():
    global pokemon_slots  # Allow access to modify the global slots

    selected_slot = None  # Initialize selected_slot to None by default

    if request.method == "GET":
        # Reset slots and default to Box 1 (index 0) on page refresh
        pokemon_slots = [None] * 6
        selected_slot = 0  # Default to Box 1

    elif request.method == "POST":
        action = request.form.get("action")

        if action == "choose":
            # User clicked "Choose Pokémon" button
            slot_index = int(request.form.get("slot_index"))
            selected_slot = slot_index

        elif action == "submit":
            # User submitted a Pokémon name for a specific slot
            slot_index = int(request.form.get("slot_index"))
            pokemon_name = request.form.get("pokemon_name")

            if pokemon_name:
                url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()

                    # Extract Pokémon's types
                    types = [t['type']['name'].capitalize() for t in data['types']]

                    # Extract Base Stats
                    base_stats = [
                        {
                            "stat": stat['stat']['name'].capitalize(),
                            "value": stat['base_stat']
                        }
                        for stat in data['stats']
                    ]

                    # Extract Abilities
                    abilities = [
                        {
                            "name": ability['ability']['name'].capitalize(),
                            "is_hidden": ability['is_hidden']
                        }
                        for ability in data['abilities']
                    ]

                    # Replace Pokémon in the slot
                    pokemon_slots[slot_index] = {
                        "name": data['name'].capitalize(),
                        "image_url": data['sprites']['front_default'],
                        "types": types,
                        "base_stats": base_stats,
                        "abilities": abilities,
                        "selected_ability": None  # Reset the ability selection
                    }

                    # Find the next empty slot
                    selected_slot = next((i for i, slot in enumerate(pokemon_slots) if slot is None), None)
                else:
                    selected_slot = slot_index  # Stay on the current slot if submission fails
            else:
                selected_slot = slot_index  # Stay on the current slot if no name provided

        elif action == "clear":
            # Clear all Pokémon slots
            pokemon_slots = [None] * 6
            selected_slot = 0  # Reset to default Box 1

        elif action == "select_ability":
            # Handle ability selection
            slot_index = int(request.form.get("slot_index"))
            ability_name = request.form.get("ability_name")
            if slot_index is not None and ability_name:
                if pokemon_slots[slot_index]:
                    pokemon_slots[slot_index]["selected_ability"] = ability_name
                selected_slot = slot_index  # Retain the current slot index

    # Collect unique typings
    all_types = set()
    for slot in pokemon_slots:
        if slot and 'types' in slot:
            all_types.update(slot['types'])

    return render_template(
        "index.html",
        slots=pokemon_slots,
        selected_slot=selected_slot,
        unique_types=sorted(all_types)  # Pass unique types to the template
    )

@app.route("/suggest_pokemon", methods=["POST"])
def suggest_pokemon():
    # Extract the user's team from the request
    user_team = request.json.get("team", [])

    # Define a prompt for GPT
    prompt = f"""
    You are a competitive Pokémon team builder. The user has selected the following team:
    {', '.join(user_team)}.
    Suggest one Pokémon and who to replace that complements this team in competitive play, considering roles, type coverage, and weaknesses. 
    Provide a short explanation for your choice.
    """

    try:
        # Generate a suggestion from GPT
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use "gpt-4" if desired
            messages=[
                {"role": "system", "content": "You are a Pokémon team building assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        suggestion = response['choices'][0]['message']['content'].strip()

        # Return the suggestion to the frontend
        return {"suggestion": suggestion}, 200
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/analyze_team", methods=["POST"])
def analyze_team():
    team = request.json.get("team", [])

    # Transform the team to include types
    transformed_team = [{"types": slot.get("types", [])} for slot in pokemon_slots if slot]
    weaknesses = calculate_team_weaknesses(transformed_team)

    # Return the weaknesses list to the frontend
    return {"weaknesses": weaknesses}, 200


if __name__ == "__main__":
    app.run(debug=True)
