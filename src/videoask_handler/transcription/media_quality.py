"""Media quality analysis utilities."""
import requests
import mimetypes
from urllib.parse import urlparse

# Quality thresholds for different formats
AUDIO_QUALITY_THRESHOLDS = {
    'mp3': {
        'high': 192,    # 192 kbps or higher
        'medium': 128,  # 128-191 kbps
        'low': 64      # Below 128 kbps
    },
    'aac': {
        'high': 256,    # 256 kbps or higher
        'medium': 192,  # 192-255 kbps
        'low': 128     # Below 192 kbps
    }
}

VIDEO_QUALITY_THRESHOLDS = {
    'mp4': {
        'high': {
            'audio': 192,  # Audio bitrate (kbps)
            'video': 2000  # Video bitrate (kbps) - roughly 1080p
        },
        'medium': {
            'audio': 128,
            'video': 1000  # roughly 720p
        },
        'low': {
            'audio': 96,
            'video': 500   # roughly 480p or lower
        }
    }
}

def get_media_type(url):
    """
    Determine media type from URL.
    
    Args:
        url (str): Media file URL
        
    Returns:
        tuple: (media_type, format)
    """
    path = urlparse(url).path
    mime_type, _ = mimetypes.guess_type(path)
    
    if not mime_type:
        return None, None
        
    media_type, format = mime_type.split('/')
    return media_type, format

def analyze_media_quality(url, headers=None):
    """
    Analyze media file quality.
    
    Args:
        url (str): URL of the media file
        headers (dict): Optional headers for the request
        
    Returns:
        dict: Quality metrics for the media file
    """
    media_type, format = get_media_type(url)
    
    if not media_type:
        return {
            "quality_level": "unknown",
            "warnings": ["Could not determine media type"]
        }
    
    try:
        # Get file headers to check size and content type
        head_response = requests.head(url, headers=headers, allow_redirects=True)
        head_response.raise_for_status()
        
        content_length = int(head_response.headers.get('content-length', 0))
        content_type = head_response.headers.get('content-type', '')
        
        # Calculate approximate bitrate (assuming 3 minute duration)
        # This is a rough estimation as we don't have actual duration
        estimated_bitrate = (content_length * 8) / (3 * 60 * 1000)  # kbps
        
        quality_metrics = {
            "quality_level": "unknown",
            "media_type": media_type,
            "format": format,
            "bitrate": estimated_bitrate,
            "warnings": []
        }
        
        # Determine quality level based on media type and format
        if media_type == 'audio':
            if format in AUDIO_QUALITY_THRESHOLDS:
                thresholds = AUDIO_QUALITY_THRESHOLDS[format]
                if estimated_bitrate >= thresholds['high']:
                    quality_level = 'high'
                elif estimated_bitrate >= thresholds['medium']:
                    quality_level = 'medium'
                else:
                    quality_level = 'low'
                
                quality_metrics.update({
                    "quality_level": quality_level,
                    "recommended_minimum_bitrate": thresholds['medium']
                })
        
        elif media_type == 'video':
            if format in VIDEO_QUALITY_THRESHOLDS:
                thresholds = VIDEO_QUALITY_THRESHOLDS[format]
                # For video, we'll be more conservative with our estimation
                if estimated_bitrate >= thresholds['high']['video'] + thresholds['high']['audio']:
                    quality_level = 'high'
                elif estimated_bitrate >= thresholds['medium']['video'] + thresholds['medium']['audio']:
                    quality_level = 'medium'
                else:
                    quality_level = 'low'
                
                quality_metrics.update({
                    "quality_level": quality_level,
                    "recommended_minimum_bitrate": {
                        "audio": thresholds['medium']['audio'],
                        "video": thresholds['medium']['video']
                    }
                })
        
        # Add quality warnings
        warnings = []
        if quality_metrics.get("quality_level") == "low":
            warnings.append(f"Low quality {media_type} file may result in poor transcription")
            if media_type == "audio":
                warnings.append(f"Recommended minimum bitrate: {quality_metrics['recommended_minimum_bitrate']} kbps")
            elif media_type == "video":
                warnings.append("Recommended minimum bitrate: "
                            f"Audio {quality_metrics['recommended_minimum_bitrate']['audio']} kbps, "
                            f"Video {quality_metrics['recommended_minimum_bitrate']['video']} kbps")
        
        quality_metrics["warnings"] = warnings
        return quality_metrics
        
    except Exception as e:
        return {
            "quality_level": "unknown",
            "error": str(e),
            "warning": "Could not analyze media quality"
        }
