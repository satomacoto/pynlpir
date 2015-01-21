# -*- coding: utf-8 -*-

"""Provides an easy-to-use Python interface to NLPIR/ICTCLAS.

The functions below are not as extensive as the full set of functions exported
by NLPIR (for that, see :mod:`pynlpir.nlpir`). A few design choices have been
made with these functions as well, e.g. they have been renamed and their output
is formatted differently.

The functions in this module all assume input is either unicode or encoded
using the encoding specified when :func:`open` is called.
These functions return unicode strings.

After importing this module, you must call :func:`open` in order to initialize
the NLPIR API. When you're done using the NLPIR API, call :func:`close` to exit
the API.

"""

from __future__ import unicode_literals
import logging
import sys

from . import nlpir, pos_map

__version__ = '0.2.2'

logger = logging.getLogger('pynlpir')

is_python3 = sys.version_info[0] > 2
if is_python3:
    unicode = str

#: The encoding configured by :func:`open`.
ENCODING = 'utf_8'


def open(data_dir=nlpir.PACKAGE_DIR, encoding=ENCODING, license_code=None):
    """Initializes the NLPIR API.

    This calls the function :func:`~pynlpir.nlpir.Init`.

    :param str data_dir: The absolute path to the directory that has NLPIR's
        `Data` directory (defaults to :data:`pynlpir.nlpir.PACKAGE_DIR`).
    :param str encoding: The encoding that the Chinese source text will be in
        (defaults to ``'utf_8'``). Possible values include ``'gbk'``,
        ``'utf_8'``, or ``'big5'``.
    :param str license_code: The license code that should be used when
        initializing NLPIR. This is generally only used by commercial users.
    :raises RuntimeError: The NLPIR API failed to initialize. Sometimes, NLPIR
        leaves an error log in the current working directory that provides
        more detailed messages (but this isn't always the case).

    """
    if license_code is None:
        license_code = ''
    global ENCODING
    if encoding.lower() in ('utf_8', 'utf-8', 'u8', 'utf', 'utf8'):
        ENCODING = 'utf_8'
        encoding_constant = nlpir.UTF8_CODE
    elif encoding.lower() in ('gbk', '936', 'cp936', 'ms936'):
        ENCODING = 'gbk'
        encoding_constant = nlpir.GBK_CODE
    elif encoding.lower() in ('big5', 'big5-tw', 'csbig5'):
        ENCODING = 'big5'
        encoding_constant = nlpir.BIG5_CODE
    else:
        raise ValueError("encoding must be one of 'utf_8', 'big5', or 'gbk'.")
    logger.debug("Initializing the NLPIR API: {'data_dir': '%s', 'encoding': "
                 "'%s', 'license_code': '%s'}"
                 % (data_dir, encoding, license_code))

    # Init in Python 3 expects bytes, not strings.
    if is_python3 and isinstance(data_dir, str):
        data_dir = _encode(data_dir)
    if is_python3 and isinstance(license_code, str):
        license_code = _encode(license_code)

    if not nlpir.Init(data_dir, encoding_constant, license_code):
        raise RuntimeError("NLPIR function 'NLPIR_Init' failed.")
    else:
        logger.debug("NLPIR API initialized.")


def close():
    """Exits the NLPIR API and frees allocated memory.

    This calls the function :func:`~pynlpir.nlpir.Exit`.

    """
    logger.debug("Exiting the NLPIR API.")
    if not nlpir.Exit():
        logger.warning("NLPIR function 'NLPIR_Exit' failed.")
    else:
        logger.debug("NLPIR API exited.")


def _decode(s, encoding=None):
    """Decodes *s*."""
    if encoding is None:
        encoding = ENCODING
    try:
        return s if isinstance(s, unicode) else s.decode(encoding)
    except Exception, e:
        logging.warn(e)
        return s if isinstance(s, unicode) else s.decode(encoding, errors='replace')


def _encode(s, encoding=None):
    """Encodes *s*."""
    if encoding is None:
        encoding = ENCODING
    return s.encode(encoding) if isinstance(s, unicode) else s


def _to_float(s):
    """Converts *s* to a float if possible; if not, returns `False`."""
    try:
        f = float(s)
        return f
    except ValueError:
        return False


def _get_pos_name(code, name='parent', english=True, delimiter=':'):
    """Gets the part of speech name for *code*.

    Joins the names together with *delimiter* if *name* is ``'all'``.

    See :func:``pynlpir.pos_map.get_pos_name`` for more information.

    """
    pos_name = pos_map.get_pos_name(code, name, english)
    return delimiter.join(pos_name) if name == 'all' else pos_name


def segment(s, pos_tagging=True, pos_names='parent', pos_english=True):
    """Segment Chinese text *s* using NLPIR.

    The segmented tokens are returned as a list. Each item of the list is a
    string if *pos_tagging* is `False`, e.g. ``['我们', '是', ...]``. If
    *pos_tagging* is `True`, then each item is a tuple (``(token, pos)``), e.g.
    ``[('我们', 'pronoun'), ('是', 'verb'), ...]``.

    If *pos_tagging* is `True` and a segmented word is not recognized by
    NLPIR's part of speech tagger, then the part of speech code/name will
    be returned as :data:`None` (e.g. a space returns as ``(' ', None)``).

    This uses the function :func:`~pynlpir.nlpir.ParagraphProcess` to segment
    *s*.

    :param s: The Chinese text to segment. *s* should be Unicode or a UTF-8
        encoded string.
    :param bool pos_tagging: Whether or not to include part of speech tagging
        (defaults to ``True``).
    :param pos_names: What type of part of speech names to return. This
        argument is only used if *pos_tagging* is ``True``. :data:`None`
        means only the original NLPIR part of speech code will be returned.
        Other than :data:`None`, *pos_names* may be one of ``'parent'``,
        ``'child'``, or ``'all'``. Defaults to ``'parent'``. ``'parent'``
        indicates that only the most generic name should be used, e.g.
        ``'noun'`` for ``'nsf'``. ``'child'`` indicates that the most specific
        name should be used, e.g. ``'transcribed toponym'`` for ``'nsf'``.
        ``'all'`` indicates that all names should be used, e.g.
        ``'noun:toponym:transcribed toponym'`` for ``'nsf'``.
    :type pos_names: ``str`` or :data:`None`
    :param bool pos_english: Whether to use English or Chinese for the part
        of speech names, e.g. ``'conjunction'`` or ``'连词'``. Defaults to
        ``True``. This is only used if *pos_names* is ``True``.

    """
    s = _decode(s)
    logger.debug("Segmenting text with%s POS tagging: %s." %
                 ('' if pos_tagging else 'out', s))
    result = nlpir.ParagraphProcess(_encode(s), pos_tagging)
    result = _decode(result)
    logger.debug("Finished segmenting text: %s." % result)
    logger.debug("Formatting segmented text.")
    tokens = result.strip().replace('  ', ' ').split(' ')
    tokens = [' ' if t == '' else t for t in tokens]
    if pos_tagging:
        for i, t in enumerate(tokens):
            token = tuple(t.rsplit('/', 1))
            if len(token) == 1:
                token = (token[0], None)
            if pos_names is not None and token[1] is not None:
                try:
                    pos_name = _get_pos_name(token[1], pos_names, pos_english)
                except Exception, e:
                    logging.warn(e)
                    pos_name = "undefined"
                token = (token[0], pos_name)
            tokens[i] = token
    logger.debug("Formatted segmented text: %s." % tokens)
    return tokens


def get_key_words(s, max_words=50, weighted=False):
    """Determines key words in Chinese text *s*.

    The key words are returned in a list. If *weighted* is ``True``,
    then each list item is a tuple: ``(word, weight)``, where
    *weight* is a float. If it's *False*, then each list item is a string.

    This uses the function :func:`~pynlpir.nlpir.GetKeyWords` to determine
    the key words in *s*.

    :param s: The Chinese text to analyze. *s* should be Unicode or a UTF-8
        encoded string.
    :param int max_words: The maximum number of key words to find (defaults to
        ``50``).
    :param bool weighted: Whether or not to return the key words' weights
        (defaults to ``True``).

    """
    s = _decode(s)
    logger.debug("Searching for up to %s%s key words in: %s." %
                 (max_words, ' weighted' if weighted else '', s))
    result = nlpir.GetKeyWords(_encode(s), max_words, weighted)
    result = _decode(result)
    logger.debug("Finished key word search: %s." % result)
    logger.debug("Formatting key word search results.")
    fresult = result.strip('#').split('#') if result else []
    if weighted:
        weights, words = [], []
        for w in fresult:
            word, pos, weight, count = w.split('/')
            weight = _to_float(weight)
            weights.append(weight or 0.0)
            words.append(word)
        fresult = zip(words, weights)
        if is_python3:
            # Return a list instead of a zip object in Python 3.
            fresult = list(fresult)
    logger.debug("Key words formatted: %s." % fresult)
    return fresult
