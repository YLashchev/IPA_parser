# IPA_parser
UTF-8 Unicode Parser

Created for easier analysis of PRAAT TextGrids.


Parses UTF-8/ASCII character strings phonologically not character-wise based on JSON dictionary covering up-to-date IPA symbols.


```python
unicode_string = 'bə.ˈnæ.nə'
ipa_parsed = IPAString(unicode_string)

print(len(unicode_string)) #9
print(ipa_parsed.total_length()) #6 
```
