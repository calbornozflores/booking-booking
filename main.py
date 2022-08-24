import optparse
from src.dateResearcher import run


def main():
    parser = optparse.OptionParser()

    parser.add_option("-c", "--city", dest = "input_place",
                      type = "str",
                      help = "[Country, City] to travel")

    parser.add_option("-a", "--arrivalDate", dest = "arrivalDate",
                      type = "str",
                      help = "Arrival Date in format %Y-%d-%d")

    parser.add_option("-d", "--departureDate", dest = "departureDate",
                      type = "str",
                      help = "Departure Date in format %Y-%d-%d")

    (options, args) = parser.parse_args()

    run()


if __name__== "__main__":
    main()