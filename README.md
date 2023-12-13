# IPA_parser
UTF-8 Unicode Parser

Created for easier analysis of PRAAT TextGrids.


Parses UTF-8/ASCII character strings phonologically not character-wise based on JSON dictionary covering up-to-date IPA symbols.


```python
word = 'bə.ˈnæ.nə'
phoneme_string = IPAString(unicode_string)

print(len(word)) 
print(phoneme_string.total_length()) 
```
  `9` (Counting every Unicode character)
  
  `6` (Counting characters that only contribute to the length phonologically)
