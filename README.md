# IPA_parser
UTF-8 Unicode Parser

Created for easier analysis of PRAAT TextGrids for Rhythm Typology Research for the SPArK lab.  


Parses UTF-8/ASCII character strings phonetically, not character-wise, based on JSON dictionary covering up-to-date IPA symbols.


### Features
Parse IPA strings into individual phonemes
Identify and categorize linguistic features 
  - consonants/vowels
  - diacritics
  - stress
  - Coda Complexity
  - Lengths (word, syllable)
    
Convert IPA transcriptions to simplified phonetic representations.

Support for multiple languages and dialects with custom methods.

### Uses
Analyze syllable structure and stress patterns

Calculate various linguistic metrics, including:
- Word and syllable durations
- Sentence-level phoneme and syllable counts
- Stress/Inter-stress intervals

```python
word = 'bə.ˈnæ.nə'
phoneme_string = IPAString(word)
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


### Configure language-specific settings
```
GEMINATE = False 
CustomCharacter.clear_all_chars()
CustomCharacter.add_char('oʊ', 'VOWEL', rank=1)
```

### Example 
```
word = "həˈloʊ"  #hello
result = IPAString("həˈloʊ")

print(result.phonemes)  # ['h', 'ə', 'l', 'oʊ']
print(result.syllables)  # ['hə', 'loʊ']
print(result.stress)  # [False, True]
```

