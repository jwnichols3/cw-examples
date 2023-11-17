def prompt_for_choice(options, prompt_message):
    if not options:
        return None
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    choice = input(prompt_message)
    try:
        return options[int(choice) - 1]
    except (IndexError, ValueError):
        print("Invalid choice.")
        return prompt_for_choice(options, prompt_message)


def prompt_if_none(value, prompt_message):
    return value if value is not None else input(prompt_message)
