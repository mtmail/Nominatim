#!/usr/bin/env python3
"""
Benchmark for the two changes to extract_category_from_query()
(src/nominatim_api/v1/helpers.py).

extract_category_from_query() runs on every /search request that carries a
free-form 'q' parameter. It does not run for /reverse, for structured search,
or for the CLI.

The original CATEGORY_REGEX was `(?P<pre>.*?)\\[...` used with .search(), which
is quadratic in the query length: the lazy `.*?` scans forward from every start
position. Two changes address it:

  1. guard      -- return early when the query contains no '[' at all. Real
                   queries carrying a [key=value] category are rare, so this
                   covers nearly every request. Cannot change any result,
                   because the pattern needs a '[' to match.
  2. slice      -- match only the category and recover the surrounding text by
                   slicing the query. This keeps the pattern anchored on a
                   literal '[', so matching is linear, which also fixes the
                   case the guard cannot help with: a query that contains a '['
                   without forming a valid category.

Change 2 is not behaviour-preserving for queries containing a newline; see the
final section of the output.

Run:  ./bench_category_guard.py
"""
import re
import timeit
from typing import Optional, Tuple

REPEATS = 9

OLD_REGEX = re.compile(r'(?P<pre>.*?)\[(?P<cls>[a-zA-Z_]+)=(?P<typ>[a-zA-Z_]+)\](?P<post>.*)')
NEW_REGEX = re.compile(r'\[(?P<cls>[a-zA-Z_]+)=(?P<typ>[a-zA-Z_]+)\]')


def original(query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """ Before either change. """
    match = OLD_REGEX.search(query)
    if match is not None:
        return (match.group('pre').strip() + ' ' + match.group('post').strip()).strip(), \
               match.group('cls'), match.group('typ')

    return query, None, None


def guard_only(query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """ With the '[' guard, original regex. """
    if '[' not in query:
        return query, None, None

    return original(query)


def guard_and_slice(query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """ Current implementation: guard plus the sliced, linear regex. """
    if '[' not in query:
        return query, None, None

    match = NEW_REGEX.search(query)
    if match is not None:
        return (query[:match.start()].strip() + ' ' + query[match.end():].strip()).strip(), \
               match.group('cls'), match.group('typ')

    return query, None, None


# 169 characters. Test queries are cut from this (and repeated for the longer
# sizes), so every case is address-shaped text of an exact length.
ADDRESS = ('Sir Alexander Fleming Building, Imperial College London, South Kensington '
           'Campus, Exhibition Road, London SW7 2AZ, United Kingdom, Europe, Earth, '
           'Solar System, Milky Way')


def address(length: int) -> str:
    text = ADDRESS
    while len(text) < length:
        text += ', ' + ADDRESS
    return text[:length]


def cases():
    """ (label, query) pairs. """
    # The common case: a plain address, no category anywhere.
    for n in (10, 20, 50, 100, 150, 200, 512):
        yield f'{n}ch, no category', address(n)
    # A real category. Neither change should slow this down.
    yield '200ch, [shop=bakery]', address(200) + ' [shop=bakery]'
    # A '[' that is not a category. The guard cannot fire here, so this is the
    # case that only the sliced regex fixes.
    yield '200ch, bare "[" only', address(100) + ' [ ' + address(100)
    yield '512ch, bare "[" only', address(255) + ' [ ' + address(255)


NEWLINE_CASES = ['foo [shop=fish]\nbar', 'foo\nbar [shop=fish]', 'a\nb [shop=fish] c\nd']


def per_call_ms(func, query: str) -> float:
    timer = timeit.Timer(lambda: func(query))
    loops, _ = timer.autorange()
    return min(timer.repeat(repeat=REPEATS, number=loops)) / loops * 1000.0


def main() -> None:
    print('extract_category_from_query(), milliseconds per call, '
          f'best of {REPEATS}\n')
    print(f'{"case":<24} {"original":>10} {"+guard":>10} {"+guard+slice":>13} '
          f'{"vs original":>13}')
    print('-' * 75)

    for label, query in cases():
        # The guard is a pure optimisation, so it must never change a result.
        assert original(query) == guard_only(query), f'guard changed {label}'
        # These cases contain no newline, so the sliced regex must agree too.
        assert original(query) == guard_and_slice(query), f'slice changed {label}'

        a = per_call_ms(original, query)
        b = per_call_ms(guard_only, query)
        c = per_call_ms(guard_and_slice, query)

        factor = a / c if c else 0.0
        if factor >= 1.05:
            change = f'{factor:.0f}x faster' if factor >= 10 else f'{factor:.1f}x faster'
        elif 0 < factor <= 0.95:
            change = f'{1 / factor:.2f}x slower'
        else:
            change = 'unchanged'

        print(f'{label:<24} {a:>10.5f} {b:>10.5f} {c:>13.5f} {change:>13}')

    print()
    print('Deliberate behaviour change: the original matched the text around the')
    print('category with ".", which stops at a newline, so anything past the line')
    print('break was silently dropped. Slicing keeps the whole query.')
    print()
    for query in NEWLINE_CASES:
        assert original(query) == guard_only(query)
        before, after = original(query)[0], guard_and_slice(query)[0]
        assert before != after
        print(f'  {query!r}')
        print(f'      original {before!r}')
        print(f'      now      {after!r}')


if __name__ == '__main__':
    main()
