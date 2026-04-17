from pecha_api import get_text_content


def parse_segmentations(segmentations):
    parsed_segmentations=[]
    for seg in segmentations:
        for segment in seg["segments"]:
            # Assume each 'lines' array in segment contains dict(s) with 'start' and 'end'
            for line in segment["lines"]:
                parsed_segmentations.append({
                    "start": line["start"],
                    "end": line["end"],
                    "id": segment["id"]
                })
    return parsed_segmentations
            
def parse_related_segments(related_segments):
    one=[]
    two=[]
    for instance in related_segments:
        Imeta = instance.get("instance_metadata", {})
        Tmeta = instance.get("text_metadata", {})
        segments = instance.get("segments", [])    
        typ = Tmeta.get("type", "").lower()
        for seg in segments:
            seg_id = seg.get("segment_id")
            span = seg.get("span", {})
            start = span.get("start")
            end = span.get("end")
            if start is not None and end is not None:
                text_content = get_text_content(edition_id=Imeta.get("id"),span_start=start,span_end=end)
                entry = {
                    "instance_id": Imeta.get("id"),
                    "segment_id": seg_id,
                    "start": start,
                    "end": end,
                    "text": text_content,
                    "meta": Imeta
                }
                if typ == "commentary":
                    one.append(entry)
                elif typ == "translation":
                    two.append(entry)
    return one, two

