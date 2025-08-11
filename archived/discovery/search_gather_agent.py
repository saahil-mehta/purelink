import json
import os

# Replace with your Perplexity API key
PERPLEXITY_API_KEY = "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"


def search_perplexity(query):
    """Searches Perplexity for the given query and returns the response."""
    if not PERPLEXITY_API_KEY:
        print("Error: Perplexity API key is missing. Please set the PERPLEXITY_API_KEY variable.")
        return None
    try:
        import requests
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant and a data annotator. Your job is to output a cohesive and most used exhaustive list of APIs or data sources for a given domain. Give me the 10 most used softwares, for each domain listed. The format must strictly be a JSON of column names : domain (from domain category), application name (software or app name). Save tokens, do not output anything else apart from the JSON. Do not name or title this JSON. The JSON should be a list of dictionaries, where each dictionary has the keys 'domain' and 'application_name'."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error during Perplexity API request: {e}")
        return None


def load_domain_categories(filepath):
    """Loads the domain categories from the given JSON filepath."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in file: {filepath}")
        return None


def write_to_fragment_kb(domain, application_name, output_file):
    """Writes the domain and application name to the fragmentKB1 file."""
    with open(output_file, 'a', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow([domain, application_name])



def main():
    """Main function to orchestrate the search and gather process."""
    domain_categories_file = "/Users/saahil/Documents/GitHub/purelink/domains/domainCategories.json"
    output_file = "/Users/saahil/Documents/GitHub/purelink/discovery/fragmentKB1.csv"

    domain_categories = load_domain_categories(domain_categories_file)
    if not domain_categories:
        return

    for domain in domain_categories.keys():
        query = f"list APIs for {domain}"
        print(f"Searching for: {query}")
        perplexity_response = search_perplexity(query)

        if perplexity_response and 'choices' in perplexity_response and len(perplexity_response['choices']) > 0:
            try:
                response_text = perplexity_response['choices'][0]['message']['content']
                # Attempt to parse the JSON response
                try:
                    applications_data = json.loads(response_text)
                    applications = [item['application_name'] for item in applications_data]
                    print(f"Found applications: {applications}")

                    for i, application in enumerate(applications):
                        if i >= 5:
                            break
                        write_to_fragment_kb(domain, application, output_file)
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"Error parsing JSON response: {e}")
                except KeyError:
                    print(f"Unexpected response format for domain: {domain}")
            except KeyError:
                print(f"Unexpected response format for domain: {domain}")
        else:
            print(f"No results found for domain: {domain}")

    print(f"\nSuccessfully wrote results to {output_file}")


if __name__ == "__main__":
    main()