from classes import CustomCharacter, IPAString
import pandas as pd

CustomCharacter.add_char('aa', 'CONSONANT',rank=1)
GEMINATE = True 

unicode_string = 'ˈba.na.na'
word = IPAString(unicode_string, geminate=GEMINATE)
# print(word.total_length())
# print(word.segment_type)
# print(word.segment_count)
# print(word.syllables)
print(word.char_only())


# for syllable in word.syllables:
#     print(syllable)
#     print(IPAString(syllable).coda)
#     print(IPAString(syllable).stress())



