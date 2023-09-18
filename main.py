import os
from ipa_classes import IPA_CHAR, IPAString




json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'IPA_Table.json')
IPA_CHAR.load_data(json_path)

#test

# Example usage
IPAString.add_custom_char('ai', 'VOWEL')
IPAString.remove_custom_char('ai')
print(IPAString.CUSTOM_IPA) 
word = IPAString('the.quick.brown.fox.jumps.over.the.lazy.dog')
print(word.total_length())
print(word.segment_count)
print(word.segment_type)
print(word.syllables)
print(word.stress)
#print(word.unicode_string)
print(word.coda)
print(IPAString(word.syllables[0]).total_length())
