import logging
import numpy as np

LOG = logging.getLogger(__name__)


class StringManager:
    @staticmethod
    def clean_str(messy):
        """
        Removes unwanted character in a str that we encounter alot
        """
        clean = messy

        # Strip of any chars that are beginning and end
        for ch in [' ', '\n']:
            clean = clean.strip(ch)

        # Remove colons but not when its between numbers (e.g time)
        if ':' in clean:
            work = clean.split(' ')
            result = []

            for w in work:
                s = w.replace(':', '')
                if s.isnumeric():
                    result.append(w)

                else:
                    result.append(s)

            clean = ' '.join(result)

        # Remove characters anywhere in string that is undesireable
        for ch in ['"', "'"]:
            clean = clean.replace(ch, '')

        clean = clean.strip(' ')
        return clean

    @staticmethod
    def get_encapsulated(str_line, encapsulator):
        """
        Returns items found in the encapsulator, useful for finding units

        Args:
            str_line: String that has encapusulated info we want removed
            encapsulator: string of characters encapusulating info to be removed
        Returns:
            result: list of strings found inside anything between encapsulators

        e.g.
            line = 'density (kg/m^3), temperature (C)'
            ['kg/m^3', 'C'] = get_encapsulated(line, '()')
        """

        result = []

        if len(encapsulator) > 2:
            raise ValueError('encapsulator can only be 1 or 2 chars long!')

        elif len(encapsulator) == 2:
            lcap = encapsulator[0]
            rcap = encapsulator[1]

        else:
            lcap = rcap = encapsulator

        # Split on the lcap
        if lcap in str_line:
            for i, val in enumerate(str_line.split(lcap)):
                # The first one will always be before our encapsulated
                if i != 0:
                    if lcap != rcap:
                        result.append(val[0:val.index(rcap)])
                    else:
                        result.append(val)

        return result

    @classmethod
    def strip_encapsulated(cls, str_line, encapsulator):
        """
        Removes from a str anything thats encapusulated by characters and the
        encapsulating chars themselves

        Args:
            str_line: String that has encapusulated info we want removed
            encapsulator: string of characters encapsulating info to be removed
        Returns:
            final: String without anything between encapsulators
        """
        final = str_line
        result = cls.get_encapsulated(final, encapsulator)

        if len(encapsulator) == 2:
            lcap = encapsulator[0]
            rcap = encapsulator[1]

        else:
            lcap = rcap = encapsulator

        # Remove all the encapsulated words
        for v in result:
            final = final.replace(lcap + v + rcap, '')

        # Make sure we remove the last one
        return final

    @staticmethod
    def parse_none(value):
        """
        parses values looking for NANs, Nones, etc...

        Args:
            value: Value potentially containing a none or nan

        Returns:
            result: If string value is nan or none, then return None type otherwise
                    return original value
        """
        result = value

        # If its a nan or none or the string is empty
        if isinstance(value, str):
            if value.lower() in ['nan', 'none'] or not value:
                result = None
        elif isinstance(value, float):
            if np.isnan(value):
                result = None

        return result

    @classmethod
    def standardize_key(cls, messy):
        """
        Preps a key for use in dataframe columns or dictionary. Makes everything
        lowercase, removes units, replaces spaces with underscores.

        Args:
            messy: string to be cleaned
        Returns:
            clean: String minus all characters and patterns of no interest
        """
        key = messy

        # Remove units
        for c in ['()', '[]']:
            key = cls.strip_encapsulated(key, c)

        key = cls.clean_str(key)
        key = key.lower().replace(' ', '_')
        key = key.lower().replace('-', '_')

        # This removes csv byte order mark for files in utf-8
        # while were encoding with latin
        key = ''.join([c for c in key if c not in 'ï»¿'])

        return key

    @classmethod
    def get_alpha_ratio(cls, str_line, encapsulator='""'):
        """
        Calculates the ratio of characters to numbers and
        potentially ignore things encapsulated

        Args:
            str_line: String to evaluate
            encapsulator: chars that encapsulate strings to be ignored

        Returns:
            ratio: float ratio of number of letter to number of numbers
        """

        line = str_line
        # Remove any quoted text
        if encapsulator:
            line = cls.strip_encapsulated(str_line, encapsulator='""')
        n_alpha = len([c for c in line if c.isalpha()])
        n_numeric = len([c for c in line if c.isnumeric()])

        if n_numeric == 0:
            ratio = 1
        else:
            ratio = n_alpha / n_numeric

        return ratio

    @classmethod
    def line_is_header(cls, str_line, header_sep=',', header_indicator='#',
                       previous_alpha_ratio=None, expected_columns=None):
        """
        Determine is line 1 a header line
        """
        # Definitive indication of a header line
        if header_indicator:
            return header_indicator == str_line[0]

        # No immediate answer so build confidence
        matches = []
        if previous_alpha_ratio:
            ratio = cls.get_alpha_ratio(str_line)
            matches.append(ratio >= previous_alpha_ratio)

        if header_sep:
            line = cls.strip_encapsulated(str_line, encapsulator='()')
            matches.append(len(line.split(header_sep)) == expected_columns)

        return matches.count(True) > matches.count(False)
