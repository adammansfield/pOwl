"""Provides classes to perform specific actions."""
import time

class Action(object):
    """
    Provides methods to do an action with given data.
    """

    def do(self, string, date):
    """
    Perform an action on the given string.

    Parameters
    ----------
    string : str
        A string containing data for the action.
    date : time.struct_time
        Date associated with the action.
    """
        pass


class BodyCompositionAction(Action):
    """
    Performs a body composition action.
    """

    _OUTPUT_DATE_FORMAT = "%Y-%m-%d"

    def __init__(self, log, parser, file_object):
        """
        Parameters
        ----------
        parser : powl.parser.BodyCompositionDataParser
            Used to parse input string.
        file_object : powl.filesystem.File
            Output file.
        """
        self._log = log
        self._parser = parser
        self._file = file_object

    def do(self, string, date):
        """
        Output body composition to file.

        Parameters
        ----------
        string : str
            Formatted string containing mass and fat percentage.
        date : time.struct_time
            Date associated with the action.
        """
        data = self._parser.parse(string)

        output = "{0}, {1}, {2}".format(
            time.strftime(self._OUTPUT_DATE_FORMAT, date),
            data.mass,
            data.fat_percentage)

        self._file.append_line(output)
        self._log.info(
            "Performed body composition action. Outputted '%s' to '%s'",
            string,
            self._file.filename)


class NoteAction(Action):
    """
    Performs a body composition action.
    """

    def __init__(self, log, file_object):
        """
        Parameters
        ----------
            log (powl.logwriter.Log):
                Used to log.
            file_object (powl.filesystem.File):
                Output file.
        """
        self._log = log
        self._file = file_object

    def do(self, string, date):
        """
        Output the note to file.

        Parameters
        ----------
        string : str
            String to record as a note.
        date : time.struct_time
            Date associated with the action.
        """
        self._file.append_line(string)
        self._log.info(
            "Performed note action. Outputted '%s' to '%s'",
            string,
            self._file.filename)


class TransactionAction(Action):
    """
    Performs a transaction recording action.
    """

    def __init__(self, log, parser, converter):
        """
        Parameters
        ----------
        log : powl.logwriter.Log
            Used to log.
        parser : powl.parser.TransactionDataParser
            Used to parse input.
        converter : powl.transactionconverter.TransactionConverter
            Used to convert transaction into a given output.
        """
        self._log = log
        self._parser = parser
        self._converter = converter

    def do(self, string, date):
        """
        Convert and output transaction to a QIF file.

        Parameters
        ----------
        string : str
            Formatted string containing debit, credit, amount, and memo.
        date : time.struct_time
            Date of the transaction.
        """
        data = self._parser.parse(string)

        financial_data, financial_file = self._converter.convert(data)
        financial_file.append_line(financial_data)

        self._log.info(
            "Performed transaction action. Input was '%s'. Wrote to '%s'.",
            string,
            financial_file.filename)
