import pandas as pd
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import json
import re
from pathlib import Path
import logging

class TeluguPronunciationConverter:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
          
    def is_telugu(self, text):
        """Check if text contains Telugu characters."""
        if not isinstance(text, str):
            return False
        # Telugu Unicode range: 0C00-0C7F
        telugu_pattern = re.compile(r'[\u0C00-\u0C7F]+')
        return bool(telugu_pattern.search(text))
    
    def basic_pronunciation(self, text):
        """Convert Telugu text to basic Latin pronunciation"""
        if not text or not isinstance(text, str):
            return None
            
        if not self.is_telugu(text):
            return None
            
        try:
            # First convert to IAST (more accurate than direct conversion)
            iast = transliterate(text, sanscript.TELUGU, sanscript.IAST)
            
            # Then apply some basic pronunciation rules
            pronunciation = iast.replace('ā', 'aa')\
                              .replace('ī', 'ii')\
                              .replace('ū', 'uu')\
                              .replace('ṃ', 'm')\
                              .replace('ḥ', 'h')\
                              .replace('ṛ', 'ru')
            
            return pronunciation
        except Exception as e:
            self.logger.error(f"Error in basic pronunciation: {str(e)}")
            return None
    
    def telugu_to_latin(self, text):
        """Convert Telugu text to Latin script (IAST)"""
        if not text or not isinstance(text, str):
            return None
            
        if not self.is_telugu(text):
            return None
            
        try:
            return transliterate(text, sanscript.TELUGU, sanscript.IAST)
        except Exception as e:
            self.logger.error(f"Error converting to Latin: {str(e)}")
            return None
    
    def process_words_file(self, input_file, output_file):
        """Process a file containing Telugu words and create a JSON with pronunciations"""
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        results = []
        failed_words = []
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                telugu_words = f.read().splitlines()
        except Exception as e:
            raise IOError(f"Error reading input file: {str(e)}")
        
        for word in telugu_words:
            if not self.is_telugu(word):
                failed_words.append(word)
                continue
                
            word_data = {
                'telugu': word,
                'pronunciation': self.basic_pronunciation(word),
                'latin': self.telugu_to_latin(word)
            }
            results.append(word_data)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise IOError(f"Error writing output file: {str(e)}")
        
        if failed_words:
            self.logger.warning(f"Failed to process {len(failed_words)} words: {failed_words}")
        
        return results
    
    def process_dataframe(self, df, telugu_column):
        """Process a pandas DataFrame containing Telugu words"""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")
            
        if telugu_column not in df.columns:
            raise ValueError(f"Column '{telugu_column}' not found in DataFrame")
        
        result_df = df.copy()
        result_df['is_valid_telugu'] = result_df[telugu_column].apply(self.is_telugu)
        
        mask = result_df['is_valid_telugu']
        result_df.loc[mask, 'pronunciation'] = (
            result_df.loc[mask, telugu_column].apply(self.basic_pronunciation)
        )
        result_df.loc[mask, 'latin'] = (
            result_df.loc[mask, telugu_column].apply(self.telugu_to_latin)
        )
        
        result_df.loc[~mask, ['pronunciation', 'latin']] = None
        
        invalid_count = (~mask).sum()
        if invalid_count > 0:
            self.logger.warning(f"Found {invalid_count} invalid Telugu entries")
        
        return result_df

def test_converter():
    """Test function to verify the converter works"""
    try:
        converter = TeluguPronunciationConverter()
        test_words = ["నమస్కారం", "ధన్యవాదాలు", "శుభోదయం", "తెలుగు"]
        
        df = pd.DataFrame({'telugu_word': test_words})
        result_df = converter.process_dataframe(df, 'telugu_word')
        print(result_df)
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_converter()
