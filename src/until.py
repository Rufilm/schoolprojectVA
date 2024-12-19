def filter_command(command, tbr_phrases):

    command = command.lower()
    for phrase in tbr_phrases:
        command = command.replace(phrase, "")
    return command.strip()