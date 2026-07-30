#!/usr/bin/env python3
"""
Benchmark for the '[' guard clause in extract_category_from_query()
(src/nominatim_api/v1/helpers.py).

extract_category_from_query() runs on every free-form search. CATEGORY_REGEX
is `(?P<pre>.*?)\\[...` used with .search(), which is quadratic in the query
length when the query contains no '[': the lazy `.*?` scans forward from every
start position. Since almost no real query carries a `[key=value]` category,
the quadratic path is the one nearly every request takes.

The guard returns early when there is no '[' at all. It cannot change any
result, because CATEGORY_REGEX requires a '[' to match.

This script measures only that guard. CATEGORY_REGEX itself is unchanged and
stays quadratic for queries that do contain a '[' -- see the last row of the
output.

Run:  ./bench_category_guard.py
"""
import re
import timeit
from typing import Optional, Tuple

REPEATS = 9

CATEGORY_REGEX = re.compile(r'(?P<pre>.*?)\[(?P<cls>[a-zA-Z_]+)=(?P<typ>[a-zA-Z_]+)\](?P<post>.*)')


def without_guard(query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """ extract_category_from_query() as it was before the change. """
    match = CATEGORY_REGEX.search(query)
    if match is not None:
        return (match.group('pre').strip() + ' ' + match.group('post').strip()).strip(), \
               match.group('cls'), match.group('typ')

    return query, None, None


def with_guard(query: str) -> Tuple[str, Optional[str], Optional[str]]:
    """ extract_category_from_query() as it is after the change. """
    if '[' not in query:
        return query, None, None

    match = CATEGORY_REGEX.search(query)
    if match is not None:
        return (match.group('pre').strip() + ' ' + match.group('post').strip()).strip(), \
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
    # The rare case: a real category. The guard must not slow this down.
    yield '200ch, [shop=bakery]', address(200) + ' [shop=bakery]'
    # A '[' that is not a category. The guard does not fire, so the quadratic
    # regex still runs. Fixing that needs a CATEGORY_REGEX change, which is
    # deliberately not part of this commit.
    yield '200ch, bare "[" only', address(100) + ' [ ' + address(100)


def per_call_ms(func, query: str) -> float:
    timer = timeit.Timer(lambda: func(query))
    loops, _ = timer.autorange()
    return min(timer.repeat(repeat=REPEATS, number=loops)) / loops * 1000.0


def main() -> None:
    print('extract_category_from_query(), milliseconds per call, '
          f'best of {REPEATS}\n')
    print(f'{"case":<24} {"without guard":>14} {"with guard":>12} {"change":>14}')
    print('-' * 68)

    for label, query in cases():
        before, after = without_guard(query), with_guard(query)
        assert before == after, f'guard changed the result for {label}: {before} != {after}'

        old = per_call_ms(without_guard, query)
        new = per_call_ms(with_guard, query)

        factor = old / new if new else 0.0
        if factor >= 1.05:
            change = f'{factor:.0f}x faster' if factor >= 10 else f'{factor:.1f}x faster'
        elif 0 < factor <= 0.95:
            change = f'{1 / factor:.2f}x slower'
        else:
            change = 'unchanged'

        print(f'{label:<24} {old:>14.5f} {new:>12.5f} {change:>14}')

    print()
    print('The assert checks the guard returns an identical result for every case.')


if __name__ == '__main__':
    main()
