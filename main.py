import optparse
from tools.io import ask_for_place, ask_for_dates
from src.dateResearcher import run


def main():
    parser = optparse.OptionParser()

    parser.add_option("-c", "--city", dest = "city",
                      type = "str",
                      help = "[City, Country] to travel")

    parser.add_option("-a", "--arrivalDate", dest = "arrival",
                      type = "str",
                      help = "Arrival Date in format %Y-%d-%d")

    parser.add_option("-d", "--departureDate", dest = "departure",
                      type = "str",
                      help = "Departure Date in format %Y-%d-%d")

    parser.add_option("-o", "--option", dest = "displayed_city",
                      type = "int",
                      help = "Index for Suggesteds Displayed City (typically in [1-4])")


    (options, args) = parser.parse_args()

    if options.city == None:
        input_place = ask_for_place()
    else:
        input_place = options.city

    if (options.arrival == None) or (options.departure == None):
        arrivalDate, departureDate = ask_for_dates()
    else:
        arrivalDate = options.arrival
        departureDate = options.departure

    displayed_city = options.displayed_city

    run(input_place, arrivalDate, departureDate, displayed_city)


if __name__== "__main__":
    main()