import curses
import argparse
import warnings
import sys
from pydantic import ValidationError, BaseModel
from enum import Enum
from typing import Any
from pathlib import Path
from denofo.utils.helpers import add_extension
from denofo.converter.convert import convert_to_json
from denofo.models import ModelValidError
from denofo.utils.constants import SECTIONS, GoQBack
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.questionnaire.questions import DeNovoQuestionnaire


def _show_message(stdscr: curses.window, message: str):
    """
    Show a message in the curses window.

    :param stdscr: The curses window.
    :type stdscr: curses.window
    :param message: The message to show.
    :type message: str
    """
    stdscr.addstr(
        5,
        0,
        f"{message}",
        curses.color_pair(3),
    )
    stdscr.refresh()
    curses.delay_output(2000)  # Delay for 2 seconds
    stdscr.clear()


def valid_input_for_pydmodel(
    pydmodel: BaseModel, field_name: str, inp_val: Any
) -> bool:
    """
    Validate the input value with a certain pydantic model and model field
    to ask the user for input again if the input is invalid.

    :param pydmodel: The pydantic model.
    :type pydmodel: BaseModel
    :param field_name: The field name of the model.
    :type field_name: str
    :param inp_val: The input value to validate.
    :type inp_val: Any
    :return: True if the input is valid, False otherwise.
    :rtype: bool
    """
    try:
        # pydmodel.validate({field_name: inp_val})
        pydmodel.__pydantic_validator__.validate_assignment(
            pydmodel.model_construct(), field_name, inp_val
        )
        return True
    except UserWarning as w:
        warning = w
        curses.wrapper(lambda stdscr: _show_message(stdscr, warning))
        return True
    except ValidationError as e:
        errors = e.errors()
        modelValErr = errors[0].get("ctx", dict()).get("error", None)
        if isinstance(modelValErr, ModelValidError):
            return True
        else:
            val_err = e
            err_msg = ", ".join(val_err.errors()[0]["msg"].split(",")[1:])
            curses.wrapper(lambda stdscr: _show_message(stdscr, err_msg))
            return False


def init_colors(stdscr: curses.window):
    """
    Initialize the colors for the curses window.

    :param stdscr: The curses window.
    :type stdscr: curses.window
    """
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)


def enum_choice_selection(
    stdscr: curses.window,
    question: str,
    items: list[Enum],
    multi: bool,
    selected: list[str],
    section_idx: int,
    prev_answer: Any,
) -> GoQBack | list[str]:
    """
    Select an item from a list of items.

    :param stdscr: The curses window.
    :type stdscr: curses.window
    :param question: The question to ask.
    :type question: str
    :param items: The list of items to choose from.
    :type items: list[Enum]
    :param multi: If multiple choices are allowed.
    :type multi: bool
    :param selected: The selected items.
    :type selected: list[str]
    :param section_idx: The index of the section.
    :type section_idx: int
    :param prev_answer: The previous answer.
    :type prev_answer: Any
    :return: The selected item/items.
    :rtype: GoQBack | list[str]
    """
    current_index = 0
    if prev_answer:
        if isinstance(prev_answer, str):
            prev_answer = [prev_answer]

        selected.extend(prev_answer)

    while True:
        stdscr.clear()

        # Display the progress bar
        tot_length = 0
        for index, section in enumerate(SECTIONS):
            centered_str = f" • {section} • "

            if index == section_idx:
                stdscr.addstr(0, tot_length, centered_str, curses.color_pair(4))
            else:
                stdscr.addstr(0, tot_length, centered_str, curses.color_pair(5))

            tot_length += len(centered_str)

        stdscr.addstr(3, 1, f"{question}\n", curses.color_pair(2))
        stdscr.addstr(
            4,
            1,
            "Select with Return/Spacebar and (a)ccept or Right/Left Arrow Key to navigate. "
            f"{'One choice.' if not multi else 'Multi-choice.'}",
        )

        # Display all the items
        for index, item in enumerate(items):
            if index == current_index:
                stdscr.attron(curses.A_REVERSE)

            if item in selected:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(index + 5, 1, f"{item.value}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(index + 5, 1, f"{item.value}")

            if index == current_index:
                stdscr.attroff(curses.A_REVERSE)

        stdscr.refresh()
        key = stdscr.getch()

        # Navigate the list
        if key == curses.KEY_UP and current_index > 0:
            current_index -= 1
        elif key == curses.KEY_DOWN and current_index < len(items) - 1:
            current_index += 1
        elif key in [ord("\n"), ord(" ")]:
            # Select/deselect the item
            if items[current_index].value in selected:
                selected.remove(items[current_index].value)
            else:
                selected.append(items[current_index].value)
        elif key == ord("a") or key == curses.KEY_RIGHT:
            if not selected:
                stdscr.addstr(
                    8, 0, "Please select at least one item.", curses.color_pair(3)
                )
                stdscr.refresh()
                curses.delay_output(1000)  # Delay for 1 second
                continue
            elif not multi and len(selected) > 1:
                stdscr.addstr(
                    8, 0, "Please select only one item.", curses.color_pair(3)
                )
                stdscr.refresh()
                curses.delay_output(1000)  # Delay for 1 second
                continue
            # Quit the application
            break
        elif key == curses.KEY_LEFT:
            stdscr.clear()
            return GoQBack()


def get_enum_choice_conversion(
    my_enum: Enum,
    question: str = "",
    multi_choice: bool = False,
    section_idx: int = 0,
    prev_answer: Any = None,
) -> GoQBack | str | list[str]:
    """
    Wrapper to get an enum choice from the user.

    :param my_enum: The enum to choose from.
    :type my_enum: Enum
    :param question: The question to ask.
    :type question: str
    :param multi_choice: If multiple choices are allowed.
    :type multi_choice: bool
    :param section_idx: The index of the section.
    :type section_idx: int
    :param prev_answer: The previous answer.
    :type prev_answer: Any
    :return: The selected item/items.
    :rtype: GoQBack | str | list[str]
    """
    selected = []
    items = list(my_enum)

    enum_answer = curses.wrapper(
        lambda stdscr: enum_choice_selection(
            stdscr, question, items, multi_choice, selected, section_idx, prev_answer
        )
    )

    if isinstance(enum_answer, GoQBack):
        return GoQBack()

    return selected if multi_choice else selected[0]


def custom_entry_insertion(
    stdscr: curses.window,
    description: str,
    multi_entries_lst: list,
    multi_choice: bool,
    section_idx: int,
    prev_answer: Any,
) -> str | list[str] | GoQBack:
    """
    Ask for custom entry/ies from the user.

    :param stdscr: The curses window.
    :type stdscr: curses.window
    :param description: The description of the question.
    :type description: str
    :param multi_entries_lst: The list of multiple entries.
    :type multi_entries_lst: list
    :param multi_choice: If multiple entries are allowed.
    :type multi_choice: bool
    :param section_idx: The index of the section.
    :type section_idx: int
    :param prev_answer: The previous answer.
    :type prev_answer: Any
    :return: The custom entry/ies.
    :rtype: str | list[str] | GoQBack
    """
    previous_entry = False

    if prev_answer:
        previous_entry = True
        if isinstance(prev_answer, str):
            prev_answer = [prev_answer]
        multi_entries_lst.extend(prev_answer)

    while True:
        stdscr.clear()

        # Display the progress bar
        tot_length = 0
        for index, section in enumerate(SECTIONS):
            centered_str = f" • {section} • "

            if index == section_idx:
                stdscr.addstr(0, tot_length, centered_str, curses.color_pair(4))
            else:
                stdscr.addstr(0, tot_length, centered_str, curses.color_pair(5))

            tot_length += len(centered_str)

        # Display the description
        stdscr.addstr(
            2,
            1,
            f"{description if description else 'Please provide your custom entry:'}\n",
            curses.color_pair(2),
        )
        stdscr.addstr(
            3,
            1,
            "Press Enter to submit custom entry or navigate with Right/Left Arrow Key between questions.",
        )

        # Show the already stored entries
        if previous_entry:
            custom_entry = prev_answer[-1]
            multi_entries_lst.pop()
            stdscr.addstr(4, 1, custom_entry)
            previous_entry = False
        else:
            custom_entry = ""

        if multi_entries_lst:
            stdscr.addstr(6, 0, "Your entries:", curses.color_pair(1))
            entries_str = " - ".join(multi_entries_lst)
            stdscr.addstr(7, 1, entries_str)

        while True:
            key = stdscr.getch()
            if key == ord("\n") or key == curses.KEY_RIGHT:
                stdscr.clear()
                break
            elif key == 27:  # 27 is the ASCII code for the Escape key
                custom_entry = ""
                stdscr.clear()
                break
            elif key == curses.KEY_BACKSPACE or key == 127:
                custom_entry = custom_entry[:-1]
            elif key == curses.KEY_LEFT:
                return GoQBack()
            else:
                custom_entry += chr(key)

            stdscr.clear()

            # Display the progress bar
            tot_length = 0
            for index, section in enumerate(SECTIONS):
                centered_str = f" • {section} • "

                if index == section_idx:
                    stdscr.addstr(0, tot_length, centered_str, curses.color_pair(4))
                else:
                    stdscr.addstr(0, tot_length, centered_str, curses.color_pair(5))

                tot_length += len(centered_str)

            stdscr.addstr(
                2,
                1,
                f"{description if description else 'Please provide your custom entry:'}\n",
                curses.color_pair(2),
            )
            stdscr.addstr(
                3,
                1,
                "Press Enter to submit custom entry or navigate with Right/Left Arrow Key between questions.",
            )
            stdscr.addstr(4, 1, custom_entry)
            # Show the already stored entries
            if multi_entries_lst:
                stdscr.addstr(6, 0, "Your entries:", curses.color_pair(1))
                entries_str = " - ".join(multi_entries_lst)
                stdscr.addstr(7, 1, entries_str)
            stdscr.refresh()

        if not custom_entry.strip():
            stdscr.addstr(5, 0, "Please provide a custom entry.", curses.color_pair(3))
            stdscr.refresh()
            curses.delay_output(1000)  # Delay for 1 second
            continue

        multi_entries_lst.append(custom_entry.strip())

        if multi_choice:
            while True:
                # Display the progress bar
                tot_length = 0
                for index, section in enumerate(SECTIONS):
                    centered_str = f" • {section} • "

                    if index == section_idx:
                        stdscr.addstr(0, tot_length, centered_str, curses.color_pair(4))
                    else:
                        stdscr.addstr(0, tot_length, centered_str, curses.color_pair(5))

                    tot_length += len(centered_str)

                stdscr.addstr(
                    5,
                    0,
                    "Do you want to provide another custom entry? (yes/no) Or (d)elete last entry.",
                )
                stdscr.addstr(6, 0, "Your entries:", curses.color_pair(1))
                entries_str = " - ".join(multi_entries_lst)
                stdscr.addstr(7, 1, entries_str)
                stdscr.refresh()

                # Get the user input
                key = stdscr.getch()
                if key == ord("y"):
                    stdscr.clear()
                    break
                elif key == ord("n") or key == curses.KEY_RIGHT:
                    if multi_entries_lst:
                        stdscr.clear()
                        return multi_entries_lst
                elif key == ord("d") or key == 27:
                    if multi_entries_lst:
                        multi_entries_lst.pop()
                        stdscr.clear()
                        continue
                elif key == curses.KEY_LEFT:
                    return GoQBack()

        elif not multi_choice and len(multi_entries_lst) == 1:
            stdscr.clear()
            return multi_entries_lst


def get_custom_entry(
    description: str = "",
    multi_choice: bool = False,
    section_idx: int = 0,
    prev_answer: Any = None,
) -> str | list[str] | GoQBack:
    """
    Wrapper to get custom entry/ies from the user.

    :param description: The description of the question.
    :type description: str
    :param multi_choice: If multiple entries are allowed.
    :type multi_choice: bool
    :param section_idx: The index of the section.
    :type section_idx: int
    :param prev_answer: The previous answer.
    :type prev_answer: Any
    :return: The custom entry/ies.
    :rtype: str | list[str] | GoQBack
    """

    multi_entries_lst = []

    cstm_answer = curses.wrapper(
        lambda stdscr: custom_entry_insertion(
            stdscr,
            description,
            multi_entries_lst,
            multi_choice,
            section_idx,
            prev_answer,
        )
    )

    if isinstance(cstm_answer, GoQBack):
        return GoQBack()

    if not multi_entries_lst:
        return get_custom_entry(description, multi_choice, section_idx, prev_answer)

    return multi_entries_lst if multi_choice else multi_entries_lst[0]


def yes_or_no(
    stdscr: curses.window,
    description: str = "",
    section_idx: int = 0,
    prev_answer: Any = None,
) -> bool | GoQBack:
    """
    Ask the user for a yes or no answer.

    :param stdscr: The curses window.
    :type stdscr: curses.window
    :param description: The description of the question.
    :type description: str
    :param section_idx: The index of the section.
    :type section_idx: int
    :param prev_answer: The previous answer.
    :type prev_answer: Any
    :return: The binary answer.
    :rtype: bool | GoQBack
    """

    while True:
        stdscr.clear()

        # Display the progress bar
        tot_length = 0
        for index, section in enumerate(SECTIONS):
            centered_str = f" • {section} • "

            if index == section_idx:
                stdscr.addstr(0, tot_length, centered_str, curses.color_pair(4))
            else:
                stdscr.addstr(0, tot_length, centered_str, curses.color_pair(5))

            tot_length += len(centered_str)

        stdscr.addstr(2, 1, f"{description}\n", curses.color_pair(2))
        stdscr.addstr(3, 1, "Select (y)es or (n)o.")
        if prev_answer is not None:
            if prev_answer:
                stdscr.addstr(5, 0, "Previous answer: Yes", curses.color_pair(1))
            else:
                stdscr.addstr(5, 0, "Previous answer: No", curses.color_pair(1))

        key = stdscr.getch()

        if key == ord("y"):
            stdscr.clear()
            return True
        elif key == ord("n"):
            stdscr.clear()
            return False
        elif key == curses.KEY_LEFT:
            return GoQBack()
        elif key == curses.KEY_RIGHT:
            if prev_answer or prev_answer is False:
                stdscr.clear()
                return prev_answer


def get_yes_no(
    description: str = "", section_idx: int = 0, prev_answer: Any = None
) -> GoQBack | bool:
    """
    Wrapper to get an answer for a yes or no question from the user.

    :param description: The description of the question.
    :param section_idx: The index of the section.
    :param prev_answer: The previous answer.
    :return: The binary answer.
    """

    bin_answer = curses.wrapper(
        lambda stdscr: yes_or_no(stdscr, description, section_idx, prev_answer)
    )

    return bin_answer


def main():
    """
    The main function of the program including argument parsing.
    Entry point of the denofo-questionnaire-cli executable.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Guide through a set of questions to produce the matching de novo gene"
            " file format of your choice for your de novo genes to describe."
        )
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help=(
            "The path and name of the output file. If no extension is provided, the"
            " default is *.dngf (de novo gene format, which is in JSON format)."
        ),
    )
    args = parser.parse_args()

    # Check the NCBI Taxonomy Database
    check_NCBI_taxDB()

    warnings.filterwarnings("ignore")

    CLI_INTERFACE_FUNCTS = {
        "get_enum_choice_conversion": get_enum_choice_conversion,
        "get_custom_entry": get_custom_entry,
        "get_yes_no": get_yes_no,
        "valid_input_for_pydmodel": valid_input_for_pydmodel,
    }

    output = add_extension(Path(args.output), "dngf")

    # Call the function for questionaire
    try:
        # Initialize the colors and hide the cursor
        curses.wrapper(lambda stdscr: (init_colors(stdscr), curses.curs_set(0)))
        de_novo_questionnaire = DeNovoQuestionnaire(CLI_INTERFACE_FUNCTS)
        gene_annotation = de_novo_questionnaire.deNovoGeneAnnotation

        try:
            curses.endwin()  # End the curses window
        except curses.error:
            pass

    except curses.error as e:
        if str(e) == "addwstr() returned ERR":
            print(
                "The terminal window is too small to display the questions."
                " Please increase the size of the terminal window and try again."
            )
        else:
            print(f"{e}")

        try:
            curses.endwin()  # End the curses window
        except curses.error:
            pass

        sys.exit(1)

    # Save model in the dngf (de novo gene format) format (JSON)
    convert_to_json(gene_annotation, output)


if __name__ == "__main__":
    main()
