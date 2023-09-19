
from classes import CustomCharacter, IPAString


CustomCharacter.add_char('ai', 'VOWEL')
CustomCharacter.remove_char('C')
word = IPAString('the.quick.brown.fox.jumps.over.the.lazy.dog')

print(word.total_length())
print(word.segment_count)
print(word.segment_type)
print(word.syllables)
print(word.stress)
#print(word.unicode_string)
print(word.coda)
print(IPAString(word.syllables[0]).total_length())
