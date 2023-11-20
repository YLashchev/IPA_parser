from IPA import CustomCharacter, IPAString
import pandas as pd


GEMINATE = True 
CustomCharacter.clear_all_chars()
CustomCharacter.add_char('OP', 'PAUSE', rank = 0)
CustomCharacter.add_char('SP', 'PAUSE', rank = 0)
CustomCharacter.add_char('ai', 'VOWEL',rank=1)
CustomCharacter.add_char('iáː', 'VOWEL',rank=1)
CustomCharacter.add_char('iá', 'VOWEL',rank=1)
CustomCharacter.add_char('ái', 'VOWEL',rank=1)
CustomCharacter.add_char('ɛːi', 'VOWEL',rank=1)
CustomCharacter.add_char('ɨːi', 'VOWEL',rank=1)
CustomCharacter.add_char('ɨi', 'VOWEL',rank=1)
CustomCharacter.add_char('ió', 'VOWEL',rank=1)
CustomCharacter.add_char('oi', 'VOWEL',rank=1)
CustomCharacter.add_char('ɛ́i', 'VOWEL',rank=1)




#df = pd.read_excel('/Users/yanlashchev/Desktop/IPA_parser/british_english.xlsx', engine='openpyxl')
#df = pd.read_excel('/Users/yanlashchev/Desktop/IPA_parser/230512_Japanese_Lily (6).xlsx', engine='openpyxl')
df = pd.read_excel('/Users/yanlashchev/Desktop/IPA_parser/Sheets/230602_Northern Tepehuan_Lily (5).xlsx', engine='openpyxl')
new_columns = ['Filename', 'Sentence', 'Word', 'Phoneme', 'Begin', 'End', 'Duration (ms.)']
df.columns = new_columns 


def insert_sp(df):
    """
    Insert SP rows between sentences, and replace NaN values in 'Sentence' column with 'SP'
    """
    # Replace NaN values in 'Sentence' column with 'SP'
    if df['Sentence'].isna().any():
        df['Sentence'].fillna('SP', inplace=True)
        return df

    # If there's no NaN but transitions between sentences, add 'SP' rows
    rows = []
    for i in range(len(df) - 1):
        current_row = df.iloc[i].to_dict()
        next_row = df.iloc[i + 1].to_dict()
        
        rows.append(current_row)
        
        if current_row['Sentence'] != next_row['Sentence']:
            sp_row = {'Sentence': 'SP', 'Duration (ms.)': 0}
            for key in current_row:
                if key not in sp_row:
                    sp_row[key] = 'SP'
            rows.append(sp_row)
            
    rows.append(df.iloc[-1].to_dict())
    
    return pd.DataFrame(rows).reset_index(drop=True)



def assign_pauses(dataframe, phoneme_column='Phoneme', word_column='Word'):
    # Iterate through the DataFrame
    for i in dataframe.index:
        # Check if the current phoneme is 'OP' or 'SP'
        if dataframe.at[i, phoneme_column] in ['OP', 'SP']:
            # Assign it to the 'Word' column
            dataframe.at[i, word_column] = dataframe.at[i, phoneme_column]






# get the unique word list without repetitions like original transcript
def get_word_list_and_indices(df, word_column='Word'):
    if df.empty:
        return [], []

    unique_words = []
    indices = []
    last_word = None

    for idx, row in df.iterrows():
        word = row[word_column]
        if word != last_word:
            unique_words.append(word)
            indices.append(idx)
            last_word = word

    return unique_words, indices








# function to collapse nested lists of lists into one list
def collapse_nested_list(nested_list) -> list:
    collapsed = []
    for item in nested_list:
        if isinstance(item, list):
            collapsed.extend(item)
        else:
            collapsed.append(item)
            
    return collapsed



#function to create word columns
def word_columns(original_word_list)-> tuple:
    j=1
    repeated_word_list = []
    word_labels = []
    unique_idx = []
    i=1
    for word in original_word_list:
        if word == 'OP':
            repeated_word_list.append(word)
            word_labels.append(word)
            unique_idx.append(word)
        elif word == 'SP':
            i=0
            repeated_word_list.append(word)
            word_labels.append(word)
            unique_idx.append(word)
        else:
            phonological_length = IPAString(word).total_length()
            repeated_word_list.append([word]*phonological_length)
            word_labels.append([i]*phonological_length)
            unique_idx.append([j]*phonological_length)
        i+=1
        j+=1
        
    repeated_word_list = collapse_nested_list(repeated_word_list)
    word_labels = collapse_nested_list(word_labels)
    unique_idx = collapse_nested_list(unique_idx)
    
    return repeated_word_list, word_labels,unique_idx


#function to create syllable columns
def pre_syllable_columns(original_word_list) -> tuple:
    syllable_list = []

    for word in original_word_list:
        if word == 'OP' or word == 'SP':
            syllable_list.append(word)
        else:
            syllables = IPAString(word).syllables
            syllable_list.append(syllables)

    return syllable_list


# function to create syllable labels
def syllable_columns(original_syllable_list) -> list:
    syllable_labels = []
    
    for item in original_syllable_list:
        # Check for 'OP' and 'SP' and add them directly
        if item == 'OP' or item == 'SP':
            syllable_labels.append(item)
            continue
        
        # For each syllable in the list item
        syllable_count = 1
        for syllable in item:
            phonological_length = IPAString(syllable).total_length()
            syllable_labels.extend([syllable_count] * phonological_length)
            syllable_count += 1
            
    return syllable_labels


#function to create segment type column
def segment_type(list):
    segment_type_list = []
    for segment in list:    
        if segment == 'OP' or segment == 'SP':
            segment_type_list.append(segment)
        else:
            temp = IPAString(segment).char_only()
            type = IPAString(temp).segment_type
            segment_type_list.append(type)
            
    temp = collapse_nested_list(segment_type_list)
    segment_type_column = ['C' if item == 'CONSONANT' else 'V' if item == 'VOWEL' else item for item in temp]
    return segment_type_column


#function to label coda 
#Note make it actually count the coda
def coda_column(syllable_list_flat):
    coda_list = [] 
    for syllable in syllable_list_flat:
        if syllable == 'OP' or syllable == 'SP':
            coda_list.append(syllable)
        else:
         coda_list.append(IPAString(syllable).coda)
    return coda_list


#function to label stress
def stress_column(syllable_list_flat):
    stress_list = []
    for syllable in syllable_list_flat: 
        if syllable == 'OP' or syllable == 'SP':
            stress_list.append(syllable)
        else:
            stress_list.append(IPAString(syllable).stress())
            
    return stress_list


#function to label syllable length by phoneme
def Syllable_Length_By_Phoneme(syllable_list_flat):
    slbp = [] 
    for syllable in syllable_list_flat:
        if syllable == 'OP' or syllable == 'SP':
            slbp.append(syllable)
        else:
            slbp.append(IPAString(syllable).total_length())
    return slbp


    
#function to label word length by phoneme
def Word_Length_By_Phoneme(repeated_word_list):
    wlbp = [] 
    for word in repeated_word_list:
        if word == 'OP' or word == 'SP':
            wlbp.append(word)
        else:
            wlbp.append(IPAString(word).total_length())
            #print(word, IPAString(word).total_length())
    return wlbp


#function to label word length by syllable
def Word_Length_By_Syllable(repeated_word_list):
    wlbs = [] 
    for word in repeated_word_list:
        if word == 'OP' or word == 'SP':
            wlbs.append(word)
        else:
            wlbs.append(len(IPAString(word).syllables))
    return wlbs



def SentenceDuration(df):
    sentence_unique_durations= []
    sentence_duration = 0
    counter = 0
    for index, (i, j) in enumerate(zip(df['Duration (ms.)'].tolist(), df['Word'].tolist())):
        if j == 'SP' and counter > 0:
            sentence_unique_durations.append([sentence_duration] * counter)
            # Avoid adding the last 'SP'
            if index != len(df['Word']) - 1:
                sentence_unique_durations.append(j)
            sentence_duration = 0
            counter = 0
        else:
            sentence_duration += float(i)
            counter += 1
    # Handle the case where there's no 'SP' at the end
    if counter > 0:
        sentence_unique_durations.extend([sentence_duration] * counter)
    
    return collapse_nested_list(sentence_unique_durations)



def process_durations(df,unique_list):
    durations_output = []

    current_word = None
    current_sum = 0 

    for _, row in df.iterrows():
        idx_number = row[unique_list]
        duration = row['Duration (ms.)']

        # Directly append for OP or SP
        if idx_number == "OP" or idx_number == "SP":
            if current_word is not None:
                durations_output.extend([current_sum] * current_count)
                current_word = None
                current_sum = 0
                current_count = 0
            durations_output.append(duration)
            continue

        # Summing logic
        if current_word == idx_number:
            current_sum += duration
            current_count += 1
        else:
            if current_word is not None:
                durations_output.extend([current_sum] * current_count)
            current_word = idx_number
            current_sum = duration
            current_count = 1

    # Add the durations for the last word
    if current_word is not None:
        durations_output.extend([current_sum] * current_count)

    return durations_output



def by_sentence_count(syllable_indices):
    # Split the list into sublists whenever 'SP' is encountered
    splits = []
    current_split = []
    
    for idx in syllable_indices:
        if idx == 'SP':
            if current_split:  # only add non-empty splits
                splits.append(current_split)
            current_split = []
        else:  # Include 'OP' in the splits for counting the length
            current_split.append(idx)
    
    # Add the last split if 'SP' wasn't the last element
    if current_split:
        splits.append(current_split)
    
    # Initialize result lists
    sentence_length_by_phoneme_repeated = []
    sentence_length_by_syllable_repeated = []
    
    # Process all splits
    for i, split in enumerate(splits):
        # Calculate phoneme length including 'OP'
        phoneme_length = len(split)
        # Calculate syllable length excluding 'OP'
        syllable_length = len(set(idx for idx in split if idx != 'OP'))
        
        # Include 'OP' in the count only once if it's present
        op_count = split.count('OP')
        syllable_length += op_count
        
        # Extend by phoneme count, excluding 'OP' for the syllable count
        sentence_length_by_phoneme_repeated.extend([phoneme_length - split.count('OP')] * (phoneme_length))
        sentence_length_by_syllable_repeated.extend([syllable_length - split.count('OP')] * (phoneme_length))
        
        # Append 'SP' after each complete sentence except the last one
        if i < len(splits) - 1:
            sentence_length_by_phoneme_repeated.append('SP')
            sentence_length_by_syllable_repeated.append('SP')

    return sentence_length_by_phoneme_repeated, sentence_length_by_syllable_repeated







# Function to update the 'new_block' column
def create_isi_blocks(df):
    df['new_block'] = False
    # Initialize a variable to track the occurrence of a stressed syllable
    encountered_stressed_syllable = False

    # Iterate through the DataFrame starting from the second row
    for i in range(1, len(df)):
        curr_stress = df.at[i, 'Stress']
        prev_syll_idx = df.at[i-1, 'unique_syll_idx']
        curr_syll_idx = df.at[i, 'unique_syll_idx']
        curr_duration = df.at[i, 'Duration (ms.)']

        # If the current syllable is stressed, set the encountered_stressed_syllable to True
        if curr_stress in ['STRESSED', 'STRESSED_2']:
            encountered_stressed_syllable = True
        
        # Start a new block if the current syllable is stressed and there was a change in unique_syll_idx
        # Only do this if we have previously encountered a stressed syllable
        if encountered_stressed_syllable and \
           ((curr_stress in ['STRESSED', 'STRESSED_2']) and curr_syll_idx != prev_syll_idx):
            df.at[i, 'new_block'] = True
        # Reset the block if 'SP' is detected with duration 0
        # and set the next syllable to start a new block if it's stressed
        elif curr_syll_idx == 'SP' and curr_duration == 0:
            encountered_stressed_syllable = False  # Reset encountered_stressed_syllable
            if (i+1 < len(df)) and (df.at[i+1, 'Stress'] in ['STRESSED', 'STRESSED_2']):
                df.at[i+1, 'new_block'] = True
        else:
            df.at[i, 'new_block'] = False

    # Set the first entry to start a new block only if it's stressed
    df.at[0, 'new_block'] = df.at[0, 'Stress'] in ['STRESSED', 'STRESSED_2']
    
    return df



# Call the function to set new blocks
def get_isi_idx(df):
    df = create_isi_blocks(df)
    isi_idx = df.index[df['new_block']].tolist()
    isi_idx.append(len(df))
    return isi_idx

    
def calculate_interstress_duration(df, isi_idx, summed_col_name='', excluded_words=None):
    # Initialize the new column for summed durations with the syllable's own duration
    df[summed_col_name] = df['SyllableDuration']

    # Loop to calculate the sum durations for each range
    for start, end in zip(isi_idx, isi_idx[1:] + [None]):
        # If 'end' is None, it means we reached the last index, so include the last item
        range_end = end or len(df)

        # Select the slice of the DataFrame we're interested in
        df_slice = df[start:range_end]

        # Perform the sum, either excluding specific words or not
        if excluded_words:
            sum_duration = df_slice[~df_slice['Word'].isin(excluded_words)]['Duration (ms.)'].sum()
        else:
            sum_duration = df_slice['Duration (ms.)'].sum()

        # Assign the sum to the new column in the appropriate slice
        df.loc[start:range_end - 1, summed_col_name] = sum_duration

    # Return the modified DataFrame
    return df


def ISI_Pause(df, isi_idx):
    # Initialize a new column with 'No' indicating no difference
    df['ISIPause'] = 'No'
    
    # Loop to check for differences in each block range
    for start, end in zip(isi_idx, isi_idx[1:] + [None]):
        # Define the range end
        range_end = end if end is not None else len(df)
        
        # Get the slice of the DataFrame we're interested in
        df_slice = df.iloc[start:range_end]
        
        # Check for differences in the slice
        difference = df_slice['InterStressDuration'] != df_slice['ISIDurationNoPause']
        
        # If there's a difference, we'll mark it accordingly
        if difference.any():
            if 'SP' in df_slice['syllables'].values:
                df.loc[start:range_end-1, 'ISIPause'] = 'yes(SP)'
            else:
                df.loc[start:range_end-1, 'ISIPause'] = 'yes'
        # If there's no difference, it will remain 'No'

    return df


def ISI_By_Segment(df, isi_idx, segment_col='SegmentType'):
    isi_idx.insert(0, 0) 
    # Initialize lists to hold the final repeated segment counts
    ISI_consonant_count = []
    ISI_vowel_count = []

    # Loop over each interval
    for start, end in zip(isi_idx, isi_idx[1:] + [None]):
        # Define the range end (non-inclusive)
        range_end = end if end is not None else len(df)

        # Get the slice of the DataFrame we're interested in
        df_slice = df.iloc[start:range_end]

        # Count the occurrences of consonants and vowels, ignoring 'SP' and 'OP'
        consonant_count = (df_slice[segment_col] == 'C').sum()
        vowel_count = (df_slice[segment_col] == 'V').sum()

        # Calculate the length of the interval including 'OP' and 'SP'
        interval_length = range_end - start

        # Repeat the counts for the length of the interval
        ISI_consonant_count.extend([consonant_count] * interval_length)
        ISI_vowel_count.extend([vowel_count] * interval_length)
        
        ISI_segment_count= [x + y for x, y in zip(ISI_consonant_count, ISI_vowel_count)]

    return ISI_segment_count, ISI_consonant_count, ISI_vowel_count



def ISI_By_Syllable(df, intervals, unique_syll_col='unique_syll_idx', word_column='Word'):
    isi_idx.insert(0, 0)
    # This list will hold the final repeated syllable counts
    repeated_syllable_counts = []

    # Loop over each interval
    for start, end in zip(intervals, intervals[1:] + [None]):
        # Define the range end (non-inclusive)
        range_end = end if end is not None else len(df)

        # Get the slice of the DataFrame we're interested in
        df_slice = df.iloc[start:range_end]

        # Determine the set of unique syllable indices, excluding 'SP' and 'OP'
        unique_syllables = set(df_slice[~df_slice[word_column].isin(['SP', 'OP'])][unique_syll_col])

        # Calculate the length of the unique syllables
        unique_syllable_count = len(unique_syllables)

        # Repeat this count for the length of the interval
        repeated_syllable_counts.extend([unique_syllable_count] * (range_end - start))

    return repeated_syllable_counts




def fill_pause_columns(df):
    # Initialize the new columns
    df['OtherPauses'] = 'N/A'
    df['SentencePauses'] = 'N/A'
    
    # Trackers for the most recent 'OP' and 'SP' durations
    last_op_duration = 'N/A'
    last_sp_duration = 'N/A'
    
    # Iterate backwards through the DataFrame
    for i in range(len(df) - 1, -1, -1):
        word = df.at[i, 'Word']
        duration = df.at[i, 'Duration (ms.)']
        
        if word == 'OP':
            # Update the last 'OP' duration encountered
            last_op_duration = duration
        elif word == 'SP':
            # Update the last 'SP' duration if it's greater than 0
            last_sp_duration = duration if duration > 0 else 'N/A'
            # Reset the 'OP' duration because 'SP' indicates a new interval
            last_op_duration = 'N/A'
        
        # Apply the last 'OP' duration encountered to the current row
        if last_op_duration != 'N/A':
            df.at[i, 'OtherPauses'] = last_op_duration
        
        # Apply the last 'SP' duration encountered to the current row
        if last_sp_duration != 'N/A':
            df.at[i, 'SentencePauses'] = last_sp_duration

    # Reset the 'SP' duration for the next interval
    df.loc[df['Word'] == 'SP', 'SentencePauses'] = df.loc[df['Word'] == 'SP', 'Duration (ms.)'].apply(lambda x: x if x > 0 else 'N/A')

    return df


def find_mismatches_with_phoneme_alignment(df, original_word_list, word_start_indices, phoneme_column='Phoneme'):
    mismatches = []
    num_words = len(original_word_list)

    for i in range(num_words):
        word = original_word_list[i]
        start_idx = word_start_indices[i]
        end_idx = word_start_indices[i + 1] if i + 1 < num_words else len(df)

        # Concatenate phonemes for the current word
        concatenated_phoneme = ''.join([IPAString(df.at[idx, phoneme_column].strip()).char_only() for idx in range(start_idx, end_idx)])

        # Check for a mismatch
        if IPAString(word.strip()).char_only() != concatenated_phoneme:
            mismatches.append((start_idx+2, word))

    return mismatches


def remove_pause_rows(df):
    # Get indices of rows with 'OP' or 'SP'
    op_sp_indices = df.index[df['Word'].isin(['OP', 'SP'])].tolist()
    
    # Drop rows with 'OP' or 'SP'
    df_cleaned = df.drop(op_sp_indices).reset_index(drop=True)

    return df_cleaned


######################## PRE-PROCESSING ########################
df = insert_sp(df)
assign_pauses(df)




    
######################### WORD LEVEL #############################

original_word_list, word_start_indices = get_word_list_and_indices(df)
mismatches = find_mismatches_with_phoneme_alignment(df, original_word_list, word_start_indices)

print(mismatches)
print('original_word_list',len(original_word_list))
repeated_word_list, word_labels, unique_word_idx = word_columns(original_word_list)
print('repeated_word_list',len(repeated_word_list))
print('word_labels',len(word_labels))
print('unique_word_idx',len(unique_word_idx))


# test_word_1 = ''.join(test_word_1)
# test_phoneme_1 = ''.join(test_phoneme)
# test_word_1=test_word_1.strip()
# test_phoneme_1=test_phoneme_1.strip()
# test_word_2 = IPAString(test_word_1).char_only()
# test_phoneme_2 = IPAString(test_phoneme_1).char_only()



wlbp = Word_Length_By_Phoneme(repeated_word_list)
print('wlbp',len(wlbp))
wlbs = Word_Length_By_Syllable(repeated_word_list)
print('wlbs',len(wlbs))


df['WordLengthByPhoneme'] = wlbp
df['WordLengthBySyllable'] = wlbs
df['WordNumber'] = word_labels
df['unique_word_idx'] = unique_word_idx



summed_word_durations = process_durations(df,'unique_word_idx')
df['WordDuration'] = summed_word_durations




##################################################################







######################## SYLLABLE LEVEL ########################

syllable_list = pre_syllable_columns(original_word_list)
syllable_column_flat = collapse_nested_list(syllable_list) #unique syllables 

#use word_columns function to flatten the list as syllables repeat the same way
syllable_list_flat, _,unique_syll_idx = word_columns(syllable_column_flat) #apply repeat 
syllable_labels = syllable_columns(syllable_list) #apply labels
print('syllable_labels',len(syllable_labels))
print('syllable_list_flat',len(syllable_list_flat))
print('unique_syll_idx',len(unique_syll_idx))

slbp = Syllable_Length_By_Phoneme(syllable_list_flat)
print('slbp',len(slbp))

df['SyllableLengthByPhoneme'] = slbp
df['syllables'] = syllable_list_flat
df['SyllableNumber'] = syllable_labels
df['unique_syll_idx'] = unique_syll_idx 
summed_syll_durations = process_durations(df,'unique_syll_idx')
df['SyllableDuration'] = summed_syll_durations

######################################################################## 





######################## PHONEME LEVEL ##########################

original_phonemes_list = df['Phoneme'].tolist()
segment_type_column = segment_type(original_phonemes_list)
print('segment_type_column',len(segment_type_column))

df['SegmentType'] = segment_type_column

##################################################################




######################### SENTENCE LEVEL #########################

sentence_unique_durations = SentenceDuration(df)   
sentence_length_by_phoneme, sentence_length_by_syllable = by_sentence_count(unique_syll_idx)    
df['SentenceDuration'] = sentence_unique_durations
df['SentenceLengthByPhoneme'] = sentence_length_by_phoneme
df['SentenceLengthBySyllable'] = sentence_length_by_syllable

######################## CODA ########################

coda_column = coda_column(syllable_list_flat)
print('coda_column',len(coda_column))


#fix this to actually count the coda
df['CodaComplexity'] = coda_column

#########################################################




######################## STRESS ########################

stress_column = stress_column(syllable_list_flat)
print('stress_column',len(stress_column))

df['Stress'] = stress_column

##########################################################



############# INTER-STRESS INTERVALS #####################

isi_idx = get_isi_idx(df)
df = calculate_interstress_duration(df, isi_idx, 'InterStressDuration', excluded_words=None)
df = calculate_interstress_duration(df, isi_idx, 'ISIDurationNoPause', excluded_words={'OP', 'SP'})
df = ISI_Pause(df, isi_idx)

# Assuming df is your DataFrame and 'SegmentType' identifies segment types
by_segment, by_consonant, by_vowel = ISI_By_Segment(df, isi_idx)
ISIBySyllable = ISI_By_Syllable(df, isi_idx)
print('by_segment',len(by_segment))
print('by_consonant',len(by_consonant))
print('by_vowel',len(by_vowel))
print('by_syllable',len(ISIBySyllable))

df['ISIBySyllable'] = ISIBySyllable
df['ISIBySegment'] = by_segment
df['ISIByConsonant'] = by_consonant
df['ISIByVowel'] = by_vowel

#######################################################

################# PAUSE COLUMNS AND FINAL DATAFRAME #####################
df = fill_pause_columns(df)
df = remove_pause_rows(df)
df['WordNumber']  = ['W' + str(i) for i in df['WordNumber']]
df['SyllableNumber']  = ['SYLL' + str(i) for i in df['SyllableNumber']]

final_df = df[['Filename','Sentence','WordNumber','Word','SyllableNumber','Phoneme','SegmentType','CodaComplexity','Stress','SyllableLengthByPhoneme','WordLengthByPhoneme',
               'SentenceLengthByPhoneme','SentenceLengthBySyllable','WordLengthBySyllable',	'Begin','End',	'Duration (ms.)','SyllableDuration','WordDuration',
               'SentenceDuration',	'InterStressDuration'	,'ISIDurationNoPause',	'ISIPause',	'ISIBySegment',	'ISIBySyllable',	'ISIByConsonant',	'ISIByVowel',	'OtherPauses',	'SentencePauses']]

########################  ########################

print(final_df)





file_path = "/Users/yanlashchev/Desktop/IPA_parser/test.csv"
final_df.to_csv(file_path, index=False)
final_df.to_excel("output.xlsx")



# Usage of the function






