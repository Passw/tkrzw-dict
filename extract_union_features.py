#! /usr/bin/python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Script to extract features of words
#
# Usage:
#   extract_union_features.py data_prefix
#
# Example
#   ./extract_union_feedback_tran.py union
#
# Copyright 2020 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License.  You may obtain a copy of the License at
#     https://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the
# License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.  See the License for the specific language governing permissions
# and limitations under the License.
#--------------------------------------------------------------------------------------------------

import json
import math
import regex
import sys
import tkrzw_union_searcher


def AddFeatures(searcher, word, weight, core_prob, features):
  entries = searcher.SearchBody(word)
  if not entries: return
  for entry in entries:
    if entry["word"] != word: continue
    prob = max(float(entry.get("probability") or 0.0), 0.000001)
    ratio = min(prob / core_prob, 1.0)
    for label, score in searcher.GetFeatures(entry).items():
      if label.startswith("__"): continue
      features[label] = (features.get(label) or 0) + score * weight * (ratio ** 0.5)


def main():
  args = sys.argv[1:]
  if len(args) < 1:
    raise ValueError("invalid arguments")
  data_prefix = args[0]
  searcher = tkrzw_union_searcher.UnionSearcher(data_prefix)
  page_index = 1
  while True:
    result = searcher.SearchByGrade(100, page_index, True)
    if not result: break
    for entry in result:
      word = entry["word"]
      prob = max(float(entry.get("probability") or 0.0), 0.000001)
      features = searcher.GetFeatures(entry)
      rel_words = {}
      parents = entry.get("parent")
      if parents:
        weight = 1 / (min(len(parents) + 1, 5))
        for parent in parents:
          rel_words[parent] = max(rel_words.get(parent) or 0, weight)
          weight *= 0.9
      children = entry.get("child")
      if children:
        weight = 1 / (min(len(children) + 2, 5))
        for child in children:
          rel_words[child] = max(rel_words.get(child) or 0, weight)
          weight *= 0.9
      related = entry.get("related")
      if related:
        weight = 1 / (min(len(related) + 2, 5))
        for rel_word in related:
          rel_words[rel_word] = max(rel_words.get(rel_word) or 0, weight)
          weight *= 0.9
      for rel_word, weight in rel_words.items():
        AddFeatures(searcher, rel_word, weight, prob, features)
      features = [x for x in features.items() if not x[0].startswith("__")]
      max_score = max(features, key=lambda x: x[1])[1]
      mod_features = []
      for label, score in features[:100]:
        score /= max_score
        mod_features.append((label, score))
      mod_features = sorted(mod_features, key=lambda x: x[1], reverse=True)
      fields = [word]
      for label, score in mod_features[:100]:
        fields.append(label)
        fields.append("{:.3f}".format(score))
      print("\t".join(fields))
    page_index += 1


if __name__=="__main__":
  main()
