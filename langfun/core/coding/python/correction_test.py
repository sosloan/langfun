# Copyright 2023 The Langfun Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for code correction."""

import inspect
import unittest

from langfun.core.coding.python import correction
from langfun.core.coding.python import errors
from langfun.core.llms import fake


class RunWithCorrectionTest(unittest.TestCase):

  def test_run_with_correction(self):
    result = correction.run_with_correction(
        inspect.cleandoc("""
            x = 1,
            y = x + 2
             z = x + y
            """),
        lm=fake.StaticSequence([
            inspect.cleandoc("""
                CodeCorrection(
                    latest_code=CodeWithError(
                        code='x = 1,\\ny = x + 2\\n z = x + y',
                        error='IndentationError: unexpected indent (<unknown>, line 3)\\n  z = x + y'
                    ),
                    correction_history=[],
                    corrected_code='x = 1,\\ny = x + 2\\nz = x + y',
                )
                """),
            inspect.cleandoc("""
                CodeCorrection(
                    latest_code=CodeWithError(
                        code='x = 1\\ny = x + 2\\n z = x + y',
                        error='TypeError: can only concatenate tuple (not "int") to tuple (<unknown>, line 2)\\n  y = x + 2'
                    ),
                    correction_history=[
                        CodeWithError(
                            code='x = 1,\\ny = x + 2\\n z = x + y',
                            error='IndentationError: unexpected indent (<unknown>, line 3)\\n  z = x + y'
                        )
                    ],
                    corrected_code='x = 1\\ny = x + 2\\nz = x + y',
                )
                """),
        ]),
    )
    self.assertEqual(result, 4)

  def test_run_without_correction(self):
    result = correction.run_with_correction(
        inspect.cleandoc("""
            x = 1
            y = x + 2
            z = x + y
            """),
        max_attempts=0,
    )
    self.assertEqual(result, 4)
    with self.assertRaises(errors.CodeError):
      correction.run_with_correction(
          inspect.cleandoc("""
            x = 1,
            y = x + 2
            z = x + y
            """),
          max_attempts=0,
      )


class CorrectTest(unittest.TestCase):

  def test_correct(self):
    corrected = correction.correct(
        inspect.cleandoc("""
            x = 1,
            y = x + 2
            z = x + y
            """),
        lm=fake.StaticSequence([
            inspect.cleandoc("""
                CodeCorrection(
                    latest_code=CodeWithError(
                        code='x = 1,\\ny = x + 2\\n z = x + y',
                        error='IndentationError: unexpected indent (<unknown>, line 3)\\n  z = x + y'
                    ),
                    correction_history=[],
                    corrected_code='x = 1,\\ny = x + 2\\nz = x + y',
                )
                """),
            inspect.cleandoc("""
                CodeCorrection(
                    latest_code=CodeWithError(
                        code='x = 1\\ny = x + 2\\n z = x + y',
                        error='TypeError: can only concatenate tuple (not "int") to tuple (<unknown>, line 2)\\n  y = x + 2'
                    ),
                    correction_history=[
                        CodeWithError(
                            code='x = 1,\\ny = x + 2\\n z = x + y',
                            error='IndentationError: unexpected indent (<unknown>, line 3)\\n  z = x + y'
                        )
                    ],
                    corrected_code='x = 1\\ny = x + 2\\nz = x + y',
                )
                """),
        ]),
    )
    self.assertEqual(corrected, 'x = 1\ny = x + 2\nz = x + y')

  def test_correct_good_code(self):
    self.assertEqual(
        correction.correct('x + y + z', global_vars=dict(x=0, y=1, z=2)),
        'x + y + z',
    )

  def test_correct_reaching_limit(self):
    with self.assertRaisesRegex(
        errors.CodeError, 'Cannot correct code after 1 attempts'
    ):
      correction.correct(
          inspect.cleandoc("""
              x = 1,
              y = x + 2
              z = x + y
              """),
          (
              'IndentationError: unexpected indent (<unknown>, line 3)\n'
              '  z = x + y'
          ),
          lm=fake.StaticSequence([
              inspect.cleandoc("""
                  CodeCorrection(
                      latest_code=CodeWithError(
                          code='x = 1,\\ny = x + 2\\n z = x + y',
                          error='IndentationError: unexpected indent (<unknown>, line 3)\\n  z = x + y'
                      ),
                      correction_history=[],
                      corrected_code='x = 1,\\ny = x + 2\\nz = x + y',
                  )
                  """),
          ]),
          max_attempts=1,
      )

  def test_correct_with_completion_error(self):
    with self.assertRaisesRegex(
        errors.CodeError, 'Cannot correct code after 1 attempts'
    ):
      correction.correct(
          inspect.cleandoc("""
              x = 1,
              y = x + 2
              z = x + y
              """),
          (
              'IndentationError: unexpected indent (<unknown>, line 3)\n'
              '  z = x + y'
          ),
          lm=fake.StaticSequence([
              inspect.cleandoc("""
                  CodeCorrection(
                      corrected_code='x = 1,\\ny = x + 2\\nz = x + y',
                  )
                  """),
          ]),
      )


if __name__ == '__main__':
  unittest.main()
