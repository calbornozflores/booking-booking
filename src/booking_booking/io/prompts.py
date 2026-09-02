import datetime


def ask_for_place() -> str:
    return input("Insert place name [City, Country]: ").strip()


def ask_for_dates() -> tuple[datetime.date, datetime.date]:
    while True:
        arrival_text = input("Insert arrival date [YYYY-MM-DD]: ").strip()
        departure_text = input("Insert departure date [YYYY-MM-DD]: ").strip()
        try:
            arrival = datetime.datetime.strptime(arrival_text, "%Y-%m-%d").date()
            departure = datetime.datetime.strptime(departure_text, "%Y-%m-%d").date()
        except ValueError:
            print("Dates must be in YYYY-MM-DD format. Try again.")
            continue
        if departure <= arrival:
            print("Departure date must be after arrival date. Try again.")
            continue
        return arrival, departure
