# Copyright (C) 2017 Olzhas Rakhimov
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for the analysis facilities."""

from __future__ import absolute_import

import platform

import mock
import pytest

import cppdep
from cppdep import Include


@pytest.mark.parametrize('filename,expected',
                         [('path.cc', 'path'), ('path.', 'path'),
                          ('.path', '.path'), ('path', 'path'),
                          ('very/long/path.h', 'very/long/path'),
                          ('./.././path.cc', './.././path')])
def test_strip_ext(filename, expected):
    """Test extraction of file name."""
    assert cppdep.strip_ext(filename) == expected


@pytest.mark.skipif(platform.system() == 'Windows', reason='non-POSIX')
@pytest.mark.parametrize('path,paths,expected',
                         [('root', ('../file',), 'file'),
                          ('root', ('file',), 'root/file'),
                          ('.', ('./file',), 'file')])
def test_path_normjoin_posix(path, paths, expected):
    """Test the normalized join of paths on POSIX systems."""
    assert cppdep.path_normjoin(path, *paths) == expected


@pytest.mark.skipif(platform.system() != 'Windows', reason='non-DOS')
@pytest.mark.parametrize('path,paths,expected',
                         [(r'C:\root', (r'..\file',), r'C:\file'),
                          ('root', ('file',), r'root\file'),
                          ('.', (r'.\file',), 'file'),
                          ('root\\', ('dir/file',), r'root\dir\file')])
def test_path_normjoin_dos(path, paths, expected):
    """Test the normalized join of paths on DOS systems."""
    assert cppdep.path_normjoin(path, *paths) == expected


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason='The same logic with different path separators.')
@pytest.mark.parametrize('paths,expected',
                         [(['/path', '/path/file', '/path/file2'], '/path'),
                          (['/path', '/dir'], '/'),
                          (['/path/file', '/pa'], '/'),
                          (['/path/dir/file', '/path/dir1/file'], '/path'),
                          (['/path/dir/', '/path/dir/file'], '/path/dir')])
def test_path_common_posix(paths, expected):
    """Test common directory for paths."""
    assert cppdep.path_common(paths) == expected


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason='The same logic with different path separators.')
@pytest.mark.parametrize('parent,child,expected',
                         [('/dir', '/dir/file', True),
                          ('/dir/file', '/dir', False),
                          ('/dir/', '/dir/file', True),
                          ('/di', '/dir/file', False),
                          ('/', '/dir/file', True),
                          ('/dir', '/dir/dir2/file', True),
                          ('/tar', '/dir/file', False),
                          ('/dir', '/dir', True)])
def test_path_isancestor(parent, child, expected):
    """Test proper ancestor directory check for paths."""
    assert cppdep.path_isancestor(parent, child) == expected


@pytest.mark.skipif(platform.system() != 'Windows', reason='POSIX is noop.')
@pytest.mark.parametrize('path,expected',
                         [('file', 'file'), ('/dir/file', '/dir/file'),
                          (r'\dir\file', '/dir/file'),
                          (r'/dir\file', '/dir/file')])
def test_path_to_posix_sep(path, expected):
    """Test POSIX separator normalization for DOS paths."""
    assert cppdep.path_to_posix_sep(path) == expected


@pytest.mark.parametrize('entry,expected',
                         [('file', ['file']), (['file'], ['file'])])
def test_yaml_list(entry, expected):
    """Test list extraction from yaml configuration."""
    assert cppdep.yaml_list(entry) == expected


@pytest.mark.parametrize('dictionary,element,default_value,expected',
                         [({'tag': 'value'}, 'tag', 'default', 'value'),
                          ({}, 'tag', 'default', 'default'),
                          ({'label': 'value'}, 'tag', 'default', 'default')])
def test_yaml_optional(dictionary, element, default_value, expected):
    """Test retrieval of an optional value from yaml configuration."""
    assert cppdep.yaml_optional(dictionary, element, default_value) == expected


@pytest.mark.parametrize('dictionary,element,default_list,expected',
                         [({'tag': 'value'}, 'tag', None, ['value']),
                          ({'tag': ['value']}, 'tag', None, ['value']),
                          ({}, 'tag', None, []),
                          ({}, 'tag', ['default'], ['default']),
                          ({'label': 'value'}, 'tag', None, [])])
def test_yaml_optional_list(dictionary, element, default_list, expected):
    """Test special handling of optional lists in yaml configurations."""
    assert (cppdep.yaml_optional_list(dictionary, element, default_list) ==
            expected)


@pytest.mark.parametrize(
    'include,expected',
    [(Include('vector', with_quotes=True), '"vector"'),
     (Include('vector', with_quotes=False), '<vector>'),
     (Include('dir/vector.h', with_quotes=False), '<dir/vector.h>'),
     (Include(r'dir\vector.h', with_quotes=False), r'<dir\vector.h>')])
def test_include_str(include, expected):
    """Tests proper string representation of include upon string conversion."""
    assert str(include) == expected


@pytest.mark.parametrize(
    'include_one,include_two',
    [(Include('vector', True), Include('vector', True)),
     (Include('vector', True), Include('vector', False)),
     (Include('./vector', True), Include('vector', True)),
     (Include('include/./vector', True), Include('include/vector', True))])
def test_include_eq(include_one, include_two):
    """Include equality and hash tests for storage in containers."""
    assert include_one == include_two
    assert hash(include_one) == hash(include_two)


def test_include_ne_impl():
    """Makes sure that __ne__ is implemented."""
    with mock.patch('cppdep.Include.__eq__') as mock_eq:
        include_one = Include('vector', True)
        check = include_one != include_one
        assert mock_eq.called
        assert not check


@pytest.mark.parametrize(
    'include_one,include_two',
    [(Include('vector.hpp', True), Include('vector', True)),
     (Include('dir/vector', True), Include('include/vector', True))])
def test_include_neq(include_one, include_two):
    """__ne__ doesn't imply (not __eq__) in Python."""
    assert include_one != include_two


@pytest.mark.parametrize(
    'text,expected',
    [('#include <vector>', ['<vector>']),
     ('#include "vector"', ['"vector"']),
     ('#  include <vector>', ['<vector>']),
     ('#\tinclude <vector>', ['<vector>']),
     ('#include "vector.h"', ['"vector.h"']),
     ('#include "vector.h++"', ['"vector.h++"']),
     ('#include "vector.any"', ['"vector.any"']),
     ('#include "vector.hpp"', ['"vector.hpp"']),
     ('#include "vector.cpp"', ['"vector.cpp"']),
     ('#include "dir/vector.hpp"', ['"dir/vector.hpp"']),
     (r'#include "dir\vector.hpp"', [r'"dir\vector.hpp"']),
     ('#include "./vector"', ['"./vector"']),
     ('#include <./vector>', ['<./vector>']),
     ('#include <a>\n#include <b>', ['<a>', '<b>']),
     ('#include <b>\n#include <a>', ['<b>', '<a>']),
     ('#include <b> // a>', ['<b>']),
     ('#include "b" // a"', ['"b"']),
     ('#include <b> /* a> */', ['<b>']),
     ('#include "b" /* a" */', ['"b"']),
     ('#include ""', []),
     ('#include <>', []),
     ('//#include <vector>', []),
     ('/*#include <vector>*/', []),
     ('#import <vector>', []),
     ('include <vector>', []),
     ('#nclude <vector>', []),
     ('<vector>', []),
     ('"vector"', []),
     ('#<vector>', []),
     ('#include < vector>', []),
     ('#include <vector >', []),
     ('#include <vector nonconventional>', []),
     ('#include " vector"', []),
     ('#include "vector "', []),
     ('    #include <vector>', ['<vector>']),
     ('#include <vector>        ', ['<vector>']),
     ('some_code #include <vector>', []),
     ('#include <vector> some_code', ['<vector>']),
     pytest.mark.xfail(('#if 0\n#include <vector>\n#endif', [])),
     pytest.mark.xfail(('/*\n#include <vector>\n*/', [])),
     pytest.mark.xfail(('#define V  <vector>\n#include V\n', ['<vector>']))])
def test_include_grep(text, expected, tmpdir):
    """Tests the include directive search from a text."""
    src = tmpdir.join('include_grep')
    src.write(text)
    assert [str(x) for x in Include.grep(str(src))] == expected
