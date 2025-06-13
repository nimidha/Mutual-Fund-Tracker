import requests

def get_mutual_fund_names():
    url = "https://www.amfiindia.com/spages/NAVAll.txt"
    response = requests.get(url)
    data = response.text.splitlines()


    fund_names = set()

    for line in data:
        parts = line.split(";")
        if len(parts) >= 4 and parts[0].isdigit():
            scheme_name = parts[3].strip()
            fund_names.add(parts[3].strip())


    return sorted(fund_names)