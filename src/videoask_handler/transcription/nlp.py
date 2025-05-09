"""NLP processing for transcript quality enhancement."""
import spacy
from typing import Dict, List, Tuple

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def analyze_transcript_content(text: str) -> Dict:
    """
    Analyze transcript content using NLP.
    
    Args:
        text: Transcript text to analyze
        
    Returns:
        dict: NLP analysis results
    """
    doc = nlp(text)
    
    # Basic metrics
    sentence_count = len(list(doc.sents))
    word_count = len([token for token in doc if not token.is_punct])
    
    # Word frequency analysis
    word_freq = {}
    for token in doc:
        if not token.is_stop and not token.is_punct and token.text.strip():
            word_freq[token.text.lower()] = word_freq.get(token.text.lower(), 0) + 1
    
    # Most frequent words
    frequent_words = sorted(
        word_freq.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Named entity recognition
    entities = [
        {
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        }
        for ent in doc.ents
    ]
    
    # Quality checks
    analysis = {
        "metrics": {
            "sentence_count": sentence_count,
            "word_count": word_count,
            "avg_words_per_sentence": word_count / sentence_count if sentence_count > 0 else 0
        },
        "frequent_words": frequent_words,
        "entities": entities,
        "quality_issues": []
    }
    
    # Check for quality issues
    if sentence_count == 0:
        analysis["quality_issues"].append("No complete sentences detected")
    elif sentence_count == 1 and word_count > 50:
        analysis["quality_issues"].append("Long text without proper sentence breaks")
        
    if word_count < 10:
        analysis["quality_issues"].append("Very short response")
        
    # Check for repeated words
    for word, count in frequent_words:
        if count > word_count * 0.1:  # Word appears in more than 10% of response
            analysis["quality_issues"].append(f"Frequent repetition of word '{word}'")
            
    return analysis

def enhance_transcript(text: str, doc=None) -> Tuple[str, List[str]]:
    """
    Enhance transcript text using NLP processing.
    
    Args:
        text: Original transcript text
        doc: Optional pre-processed spaCy doc
        
    Returns:
        tuple: (enhanced_text, warnings)
    """
    if not doc:
        doc = nlp(text)
        
    warnings = []
    enhanced_text = text
    
    # Fix sentence capitalization
    sentences = list(doc.sents)
    for sent in sentences:
        if sent.text[0].islower():
            sent_start = sent.start_char
            if sent_start == 0:
                enhanced_text = sent.text[0].upper() + sent.text[1:]
            else:
                enhanced_text = (
                    enhanced_text[:sent_start] +
                    sent.text[0].upper() +
                    enhanced_text[sent_start + 1:]
                )
    
    # Check for missing punctuation
    last_char = enhanced_text.strip()[-1] if enhanced_text.strip() else ''
    if last_char not in '.!?':
        enhanced_text = enhanced_text.strip() + '.'
        warnings.append("Added missing sentence-ending punctuation")
    
    # Add paragraph breaks for readability
    if len(sentences) > 5:
        # Group sentences into paragraphs (roughly 3-4 sentences each)
        paragraphs = []
        current_para = []
        
        for sent in sentences:
            current_para.append(sent.text.strip())
            if len(current_para) >= 3:
                paragraphs.append(' '.join(current_para))
                current_para = []
                
        if current_para:  # Add any remaining sentences
            paragraphs.append(' '.join(current_para))
            
        enhanced_text = '\n\n'.join(paragraphs)
        
    return enhanced_text, warnings

def get_transcript_analysis(text: str) -> Dict:
    """
    Get comprehensive transcript analysis with enhancements.
    
    Args:
        text: Original transcript text
        
    Returns:
        dict: Analysis results and enhanced text
    """
    # Process with spaCy
    doc = nlp(text)
    
    # Get content analysis
    analysis = analyze_transcript_content(text)
    
    # Enhance transcript
    enhanced_text, enhancement_warnings = enhance_transcript(text, doc)
    
    # Combine results
    return {
        "enhanced_text": enhanced_text,
        "original_text": text,
        "enhancement_warnings": enhancement_warnings,
        "content_analysis": analysis,
        "quality_score": calculate_quality_score(analysis)
    }

def calculate_quality_score(analysis: Dict) -> float:
    """
    Calculate an overall quality score for the transcript.
    
    Args:
        analysis: Content analysis dictionary
        
    Returns:
        float: Quality score between 0 and 1
    """
    score = 1.0
    metrics = analysis["metrics"]
    
    # Penalize for quality issues
    score -= len(analysis["quality_issues"]) * 0.1
    
    # Penalize very short responses
    if metrics["word_count"] < 20:
        score -= 0.2
    elif metrics["word_count"] < 50:
        score -= 0.1
        
    # Penalize lack of sentence structure
    if metrics["sentence_count"] == 0:
        score -= 0.3
    elif metrics["avg_words_per_sentence"] > 40:
        score -= 0.2  # Penalize run-on sentences
        
    # Ensure score stays between 0 and 1
    return max(0.0, min(1.0, score))
