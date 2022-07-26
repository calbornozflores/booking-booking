from config.config import list_to_remove_property_card, list_to_replace_property_card


def remove_string(text, list_to_remove):
    for str_to_remove in list_to_remove:
        text = text.replace(str_to_remove, "")
    return text


def str2space(text, list_to_replace):
    for str_to_replace in list_to_replace:
        text = text.replace(str_to_replace, " ")
    return text


def clean_property_card(text):
    text = remove_string(text, list_to_remove_property_card)
    text = str2space(text, list_to_replace_property_card)
    return text

