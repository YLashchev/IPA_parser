# IPA_parser
UTF-8 Unicode Parser

Created for easier analysis of PRAAT TextGrids.


Parses UTF-8/ASCII character strings phonologically not character-wise based on JSON dictionary covering up-to-date IPA symbols.


```python
word = 'bə.ˈnæ.nə'
phoneme_string = IPAString(unicode_string)
```
### Phonological Length
```
print(len(word)) 
print(phoneme_string.total_length()) 
```
  `9` (Counting every Unicode character)
  
  `6` (Counting characters that only contribute to the length phonologically)

### Type & Name
```
print(phoneme_string.segment_type)
print(phoneme_string.segment_count)

for char in word:
  print(IPA_CHAR.name(char)
```
`['CONSONANT', 'VOWEL', 'SUPRASEGMENTAL', 'SUPRASEGMENTAL', 'CONSONANT', 'VOWEL', 'SUPRASEGMENTAL', 'CONSONANT', 'VOWEL']`

`{'V': 3, 'C': 3}`

`VOICED BILABIAL PLOSIVE,
MID CENTRAL VOWEL,
SYLLABLE BREAK,
PRIMARY STRESS,
VOICELESS DENTAL/ALVEOLAR NASAL,
NEAR-OPEN FRONT UNROUNDED VOWEL,
SYLLABLE BREAK,
VOICELESS DENTAL/ALVEOLAR NASAL,
MID CENTRAL VOWEL`

