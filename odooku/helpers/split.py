def split(value, seperator):
    splitted = [
        part.strip()
        for part in value.split(seperator)
        if value.strip()
    ] if value else []
    return splitted
