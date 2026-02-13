import base64
import json
import asyncio
import logging
import io
from typing import Optional
from PIL import Image
from openai import AsyncOpenAI
from google import genai
from google.genai import types
from anthropic import AsyncAnthropic

from config import get_settings
from models import ModelAnalysisResult, QuadrantAnalysis, DecidingModelResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


DENTAL_ANALYSIS_PROMPT = """ You are an expert dental radiologist analyzing an OPG (Orthopantomogram) dental X-ray image.

Analyze the image and identify which teeth are MISSING in each of the four quadrants:
- Quadrant 1 (Upper Right): Teeth 11-18 (from center to back: central incisor to third molar)
- Quadrant 2 (Upper Left): Teeth 21-28 (from center to back: central incisor to third molar)
- Quadrant 3 (Lower Left): Teeth 31-38 (from center to back: central incisor to third molar)
- Quadrant 4 (Lower Right): Teeth 41-48 (from center to back: central incisor to third molar)

For each quadrant, list the tooth numbers that are MISSING (not visible or clearly absent).

Respond in this exact JSON format:
{
    "quadrant_1": {
        "quadrant_number": 1,
        "missing_teeth": [list of missing tooth numbers, e.g., 18, 17],
        "present_teeth": [list of present tooth numbers],
        "notes": "any relevant observations"
    },
    "quadrant_2": {
        "quadrant_number": 2,
        "missing_teeth": [],
        "present_teeth": [],
        "notes": ""
    },
    "quadrant_3": {
        "quadrant_number": 3,
        "missing_teeth": [],
        "present_teeth": [],
        "notes": ""
    },
    "quadrant_4": {
        "quadrant_number": 4,
        "missing_teeth": [],
        "present_teeth": [],
        "notes": ""
    },
    "confidence": 0.85
}

Be thorough and accurate. Only report teeth as missing if you are confident they are not present in the image."""


FORENSIC_DENTAL_PROMPT = """## **Role**

You are a **Dental Radiology Examiner (MDS Oral Medicine & Radiology)**.
You strictly follow **White & Pharoah, Langlais, and Whaites** standards.
You are **forbidden from guessing** and **forbidden from labeling a tooth as missing unless absence is radiographically proven beyond doubt**.

---

## **Task**

Interpret the given **Orthopantomogram (OPG)** using the **FDI tooth numbering system** by:

1. Correctly dividing the image into four quadrants.
2. Identifying each tooth number anatomically.
3. Classifying every tooth as **Present**, **Impacted**, **Not Visualized**, or **Missing (Proven)**.
4. Producing a **strict confirmed list of missing teeth only when criteria are fully met**.

---

## **Reasoning (NON-NEGOTIABLE RULES)**

### **Rule 1: Quadrant Division (MANDATORY FIRST STEP)**

Divide the image using the Cranial midline (nasal septum) and Mandibular symphysis.

* Q1: 11–18 (Maxillary Right) | Q2: 21–28 (Maxillary Left)
* Q3: 31–38 (Mandibular Left) | Q4: 41–48 (Mandibular Right)

### **Rule 2: Root-Priority Override Rule (CRITICAL)**

If **any part of a root** is visible → **Tooth MUST be classified as PRESENT**. This overrides crown loss, blur, or metallic overlap.

### **Rule 3: Crown Absence ≠ Missing**

A tooth cannot be labeled missing based only on a blurred crown or sinus overlap. Roots and supporting structures take priority.

### **Rule 4: “Not Visualized” Is the DEFAULT for Uncertainty**

If roots are unclear, region is blurred, or posterior border is not captured → Classify as **NOT VISUALIZED**. (Not Visualized ≠ Missing).

### **Rule 5: Strict Missing Tooth Criteria (ALL REQUIRED)**

A tooth is **MISSING (PROVEN)** only if: No crown, no root, no lamina dura, no PDL space, no follicle/crypt, and region is fully visualized with a healed ridge.

### **Rule 6: Posterior Maxilla Protection Rule**

For 14–17 and 24–27, missing diagnosis is allowed **only if** the sinus floor and alveolar ridge are clearly seen in the focal trough.

### **Rule 7: Third Molar Special Rule**

For 18, 28, 38, 48: If impacted → **Present (Impacted)**. If region unclear → **Not Visualized**.

### **Rule 8: Forbidden Actions**

Do NOT assume extraction, congenital absence, or "healed ridge" unless explicitly visible.

### **Rule 9: Restoration & High-Density Material Recognition**

If high-density radiopacity (fillings, crowns, RCT material) is visible, the tooth MUST be marked **Present**. Note the restoration in the justification.

### **Rule 10: Pathological Radiolucency Observation**

Severe decay or periapical dark areas (radiolucencies) do not constitute "missing." If any tooth structure or root remnants remain, the tooth is **Present**.

---

## **Output (STRICT FORMAT ONLY)**

### **1. Quadrant-wise Tooth Table (FDI)**

| Tooth # | Status | Radiographic Justification |
| --- | --- | --- |
| (List 11-48) | (Present/Impacted/Not Visualized/Missing-Proven) | (Short radiographic justification) |

### **2. Confirmed Missing Teeth List (STRICT)**

Include **ONLY** teeth that fully satisfy Rule 5. If none, state:

> “No teeth can be conclusively labeled as missing based on this OPG.”

### **3. Clinical & Pathological Observations**

* Note any **Impactions** (position/angulation).
* Note **Restorations/Endodontic treatments** visualized.
* Note **Pathological Radiolucencies** (decay or periapical lesions).

### **4. Tooth Count Summary**

* Teeth present per quadrant
* Total teeth present
* Teeth not visualized
* Teeth confirmed missing

---

**Stopping**
Stop immediately after structured output. Do not add treatment plans or speculation.
"""


class GPT4OClient:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GPT4O_MODEL
    
    async def analyze_dental_image(self, image_base64: str, mime_type: str) -> ModelAnalysisResult:
        logger.info(f"🔵 GPT-4o: Starting analysis with forensic prompt...")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": FORENSIC_DENTAL_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            raw_response = response.choices[0].message.content
            logger.info(f"🔵 GPT-4o Raw Response:\n{raw_response}")
            
            # Use the shared parser logic (duplicating specifically for this class to be self-contained or I could verify if there's a shared helper now. 
            # I will reuse the parsing logic I wrote for Gemini since it's the exact same output format).
            result = self._parse_forensic_response(raw_response)
            
            logger.info(f"🔵 GPT-4o Results (Parsed):")
            logger.info(f"   Q1 Missing: {result.quadrant_1.missing_teeth}")
            logger.info(f"   Q2 Missing: {result.quadrant_2.missing_teeth}")
            logger.info(f"   Q3 Missing: {result.quadrant_3.missing_teeth}")
            logger.info(f"   Q4 Missing: {result.quadrant_4.missing_teeth}")
            
            return result
            
        except Exception as e:
            logger.error(f"🔵 GPT-4o Error: {str(e)}")
            return self._create_error_result(str(e))
    
    def _parse_forensic_response(self, text: str) -> ModelAnalysisResult:
        """Parses the detailed Examiner table format."""
        import re
        
        missing_teeth = []
        present_teeth = []
        impacted_teeth = []
        not_visualized_teeth = []
        
        # Remove bolding/markdown for easier parsing
        clean_text = text.replace('**', '').replace('*', '')

        lines = clean_text.split('\n')
        
        for line in lines:
            if "|" not in line:
                continue
                
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 3: 
                continue 
            
            # Find tooth number
            tooth_num_match = re.search(r'\b([1-4][1-8])\b', line)
            if not tooth_num_match:
                continue
            tooth_num = int(tooth_num_match.group(1))
            
            # Status check (case insensitive, stripped of markdown)
            lower_line = line.lower().replace('**', '').replace('*', '')
            
            if "missing" in lower_line: 
               # Check specifically for "missing (proven)" or simply "missing" if clearly stated
               # The prompt asks for "Missing (Proven)", but let's be robust
               if "proven" in lower_line or "missing" in lower_line:
                   if "not" not in lower_line: # avoid "not missing"
                       if tooth_num not in missing_teeth:
                           missing_teeth.append(tooth_num)

            elif "not visualized" in lower_line:
                if tooth_num not in not_visualized_teeth:
                    not_visualized_teeth.append(tooth_num)
            
            elif "impacted" in lower_line:
                if tooth_num not in impacted_teeth:
                    impacted_teeth.append(tooth_num)
                # Count as present usually
                if tooth_num not in present_teeth:
                    present_teeth.append(tooth_num)
            
            elif "present" in lower_line:
                if tooth_num not in present_teeth:
                    present_teeth.append(tooth_num)

        # Also Parse "Confirmed Missing Teeth List" as backup/confirmation
        confirmed_match = re.search(r"Confirmed missing teeth.*?:(.+)", clean_text, re.IGNORECASE)
        if confirmed_match:
            content = confirmed_match.group(1)
            nums = re.findall(r'\b[1-4][1-8]\b', content)
            for n in nums:
                tn = int(n)
                if tn not in missing_teeth:
                    missing_teeth.append(tn)
                # Ensure it's removed from others if found here
                if tn in present_teeth: present_teeth.remove(tn)
                if tn in not_visualized_teeth: not_visualized_teeth.remove(tn)

        # Distribute into quadrants
        def get_q(t_list, start, end):
            return sorted([t for t in t_list if start <= t <= end])

        q_data = {}
        for q in range(1, 5):
            start = q * 10 + 1
            end = q * 10 + 8
            q_data[f"q{q}_missing"] = get_q(missing_teeth, start, end)
            q_data[f"q{q}_present"] = get_q(present_teeth, start, end)
            q_data[f"q{q}_impacted"] = get_q(impacted_teeth, start, end)
            q_data[f"q{q}_not_viz"] = get_q(not_visualized_teeth, start, end)
        
        return ModelAnalysisResult(
            model_name="GPT-4o",
            quadrant_1=QuadrantAnalysis(
                quadrant_number=1, 
                missing_teeth=q_data["q1_missing"], 
                present_teeth=q_data["q1_present"],
                impacted_teeth=q_data["q1_impacted"],
                not_visualized_teeth=q_data["q1_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_2=QuadrantAnalysis(
                quadrant_number=2, 
                missing_teeth=q_data["q2_missing"], 
                present_teeth=q_data["q2_present"],
                impacted_teeth=q_data["q2_impacted"],
                not_visualized_teeth=q_data["q2_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_3=QuadrantAnalysis(
                quadrant_number=3, 
                missing_teeth=q_data["q3_missing"], 
                present_teeth=q_data["q3_present"],
                impacted_teeth=q_data["q3_impacted"],
                not_visualized_teeth=q_data["q3_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_4=QuadrantAnalysis(
                quadrant_number=4, 
                missing_teeth=q_data["q4_missing"], 
                present_teeth=q_data["q4_present"],
                impacted_teeth=q_data["q4_impacted"],
                not_visualized_teeth=q_data["q4_not_viz"],
                notes="Parsed from Examiner table"
            ),
            confidence=0.90, 
            raw_response=text
        )
    
    def _create_error_result(self, error: str) -> ModelAnalysisResult:
        empty_quadrant = lambda n: QuadrantAnalysis(
            quadrant_number=n, missing_teeth=[], present_teeth=[], notes=f"Error: {error}"
        )
        return ModelAnalysisResult(
            model_name="GPT-4o",
            quadrant_1=empty_quadrant(1),
            quadrant_2=empty_quadrant(2),
            quadrant_3=empty_quadrant(3),
            quadrant_4=empty_quadrant(4),
            confidence=0.0,
            raw_response=f"Error: {error}"
        )


class GeminiClient:
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model_name = settings.GEMINI_MODEL
    
    async def analyze_dental_image(self, image_base64: str, mime_type: str) -> ModelAnalysisResult:
        logger.info(f"🟢 Gemini: Starting analysis with forensic prompt using ThinkingConfig (genai SDK)...")
        try:
            # Decode base64 to bytes, then to PIL Image
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Use Thinking Config with gemini-3-pro-preview
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=[FORENSIC_DENTAL_PROMPT, image],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="high"),
                    temperature=1.0, 
                    top_p=0.95,
                    max_output_tokens=4000
                )
            )
            
            raw_response = response.text
            logger.info(f"🟢 Gemini Raw Response:\n{raw_response}")
            
            # DEBUG: Write to file
            try:
                with open("gemini_debug.txt", "w", encoding="utf-8") as f:
                    f.write(raw_response)
            except Exception as e:
                logger.error(f"Failed to write gemini_debug.txt: {e}")
            
            # Parse the text response into the expected JSON structure
            result = self._parse_forensic_response(raw_response)
            
            logger.info(f"🟢 Gemini Results (Parsed):")
            logger.info(f"   Q1 Missing: {result.quadrant_1.missing_teeth}")
            logger.info(f"   Q2 Missing: {result.quadrant_2.missing_teeth}")
            logger.info(f"   Q3 Missing: {result.quadrant_3.missing_teeth}")
            logger.info(f"   Q4 Missing: {result.quadrant_4.missing_teeth}")
            
            return result
            
        except Exception as e:
            logger.error(f"🟢 Gemini Error: {str(e)}")
            return self._create_error_result(str(e))
    
    def _parse_forensic_response(self, text: str) -> ModelAnalysisResult:
        """Parses the detailed Examiner table format."""
        import re
        
        missing_teeth = []
        present_teeth = []
        impacted_teeth = []
        not_visualized_teeth = []
        
        clean_text = text.replace('**', '').replace('*', '')
        lines = clean_text.split('\n')
        
        for line in lines:
            if "|" not in line:
                continue
                
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 3: 
                continue 
            
            tooth_num_match = re.search(r'\b([1-4][1-8])\b', line)
            if not tooth_num_match:
                continue
            tooth_num = int(tooth_num_match.group(1))
            
            lower_line = line.lower().replace('**', '').replace('*', '')
            
            if "missing" in lower_line:
                if "proven" in lower_line or "missing" in lower_line:
                     if "not" not in lower_line:
                        if tooth_num not in missing_teeth:
                            missing_teeth.append(tooth_num)

            elif "not visualized" in lower_line:
                if tooth_num not in not_visualized_teeth:
                    not_visualized_teeth.append(tooth_num)

            elif "impacted" in lower_line:
                if tooth_num not in impacted_teeth:
                    impacted_teeth.append(tooth_num)
                if tooth_num not in present_teeth:
                    present_teeth.append(tooth_num)
            
            elif "present" in lower_line:
                if tooth_num not in present_teeth:
                    present_teeth.append(tooth_num)

        # Confirmed list backup
        confirmed_match = re.search(r"Confirmed missing teeth.*?:(.+)", clean_text, re.IGNORECASE)
        if confirmed_match:
            content = confirmed_match.group(1)
            nums = re.findall(r'\b[1-4][1-8]\b', content)
            for n in nums:
                tn = int(n)
                if tn not in missing_teeth: missing_teeth.append(tn)
                if tn in present_teeth: present_teeth.remove(tn)
                if tn in not_visualized_teeth: not_visualized_teeth.remove(tn)

        # Distribute into quadrants
        def get_q(t_list, start, end):
            return sorted([t for t in t_list if start <= t <= end])

        q_data = {}
        for q in range(1, 5):
            start = q * 10 + 1
            end = q * 10 + 8
            q_data[f"q{q}_missing"] = get_q(missing_teeth, start, end)
            q_data[f"q{q}_present"] = get_q(present_teeth, start, end)
            q_data[f"q{q}_impacted"] = get_q(impacted_teeth, start, end)
            q_data[f"q{q}_not_viz"] = get_q(not_visualized_teeth, start, end)
        
        return ModelAnalysisResult(
            model_name="Gemini",
            quadrant_1=QuadrantAnalysis(
                quadrant_number=1, 
                missing_teeth=q_data["q1_missing"], 
                present_teeth=q_data["q1_present"],
                impacted_teeth=q_data["q1_impacted"],
                not_visualized_teeth=q_data["q1_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_2=QuadrantAnalysis(
                quadrant_number=2, 
                missing_teeth=q_data["q2_missing"], 
                present_teeth=q_data["q2_present"],
                impacted_teeth=q_data["q2_impacted"],
                not_visualized_teeth=q_data["q2_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_3=QuadrantAnalysis(
                quadrant_number=3, 
                missing_teeth=q_data["q3_missing"], 
                present_teeth=q_data["q3_present"],
                impacted_teeth=q_data["q3_impacted"],
                not_visualized_teeth=q_data["q3_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_4=QuadrantAnalysis(
                quadrant_number=4, 
                missing_teeth=q_data["q4_missing"], 
                present_teeth=q_data["q4_present"],
                impacted_teeth=q_data["q4_impacted"],
                not_visualized_teeth=q_data["q4_not_viz"],
                notes="Parsed from Examiner table"
            ),
            confidence=0.95,
            raw_response=text
        )

    def _create_error_result(self, error: str) -> ModelAnalysisResult:
        empty_quadrant = lambda n: QuadrantAnalysis(
            quadrant_number=n, missing_teeth=[], present_teeth=[], notes=f"Error: {error}"
        )
        return ModelAnalysisResult(
            model_name="Gemini",
            quadrant_1=empty_quadrant(1),
            quadrant_2=empty_quadrant(2),
            quadrant_3=empty_quadrant(3),
            quadrant_4=empty_quadrant(4),
            confidence=0.0,
            raw_response=f"Error: {error}"
        )


class AnthropicClient:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
    
    async def analyze_dental_image(self, image_base64: str, mime_type: str) -> ModelAnalysisResult:
        logger.info(f"🟣 Anthropic Claude: Starting analysis with forensic prompt...")
        try:
            # Map common mime types to Anthropic's accepted formats
            media_type_map = {
                "image/jpeg": "image/jpeg",
                "image/jpg": "image/jpeg",
                "image/png": "image/png",
                "image/gif": "image/gif",
                "image/webp": "image/webp"
            }
            media_type = media_type_map.get(mime_type, "image/jpeg")
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": FORENSIC_DENTAL_PROMPT
                            }
                        ]
                    }
                ]
            )
            
            raw_response = response.content[0].text
            logger.info(f"🟣 Anthropic Claude Raw Response:\n{raw_response}")
            
            # Use parsing logic (duplicated for safety/simplicity in this context)
            result = self._parse_forensic_response(raw_response)
            
            logger.info(f"🟣 Anthropic Claude Results (Parsed):")
            logger.info(f"   Q1 Missing: {result.quadrant_1.missing_teeth}")
            logger.info(f"   Q2 Missing: {result.quadrant_2.missing_teeth}")
            logger.info(f"   Q3 Missing: {result.quadrant_3.missing_teeth}")
            logger.info(f"   Q4 Missing: {result.quadrant_4.missing_teeth}")
            
            return result
            
        except Exception as e:
            logger.error(f"🟣 Anthropic Claude Error: {str(e)}")
            return self._create_error_result(str(e))
            
    def _parse_forensic_response(self, text: str) -> ModelAnalysisResult:
        """Parses the detailed Examiner table format."""
        import re
        
        missing_teeth = []
        present_teeth = []
        impacted_teeth = []
        not_visualized_teeth = []
        
        clean_text = text.replace('**', '').replace('*', '')
        lines = clean_text.split('\n')
        
        for line in lines:
            if "|" not in line:
                continue
                
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 3: 
                continue 
            
            tooth_num_match = re.search(r'\b([1-4][1-8])\b', line)
            if not tooth_num_match:
                continue
            tooth_num = int(tooth_num_match.group(1))
            
            lower_line = line.lower().replace('**', '').replace('*', '')
            
            if "missing" in lower_line: 
               if "proven" in lower_line or "missing" in lower_line:
                   if "not" not in lower_line:
                       if tooth_num not in missing_teeth:
                           missing_teeth.append(tooth_num)

            elif "not visualized" in lower_line:
                if tooth_num not in not_visualized_teeth:
                    not_visualized_teeth.append(tooth_num)
            
            elif "impacted" in lower_line:
                if tooth_num not in impacted_teeth:
                    impacted_teeth.append(tooth_num)
                if tooth_num not in present_teeth:
                    present_teeth.append(tooth_num)
            
            elif "present" in lower_line:
                if tooth_num not in present_teeth:
                    present_teeth.append(tooth_num)

        # Confirm list backup
        confirmed_match = re.search(r"Confirmed missing teeth.*?:(.+)", clean_text, re.IGNORECASE)
        if confirmed_match:
            content = confirmed_match.group(1)
            nums = re.findall(r'\b[1-4][1-8]\b', content)
            for n in nums:
                tn = int(n)
                if tn not in missing_teeth: missing_teeth.append(tn)
                if tn in present_teeth: present_teeth.remove(tn)
                if tn in not_visualized_teeth: not_visualized_teeth.remove(tn)

        # Distribute into quadrants
        def get_q(t_list, start, end):
            return sorted([t for t in t_list if start <= t <= end])

        q_data = {}
        for q in range(1, 5):
            start = q * 10 + 1
            end = q * 10 + 8
            q_data[f"q{q}_missing"] = get_q(missing_teeth, start, end)
            q_data[f"q{q}_present"] = get_q(present_teeth, start, end)
            q_data[f"q{q}_impacted"] = get_q(impacted_teeth, start, end)
            q_data[f"q{q}_not_viz"] = get_q(not_visualized_teeth, start, end)
        
        return ModelAnalysisResult(
            model_name="Anthropic Claude",
            quadrant_1=QuadrantAnalysis(
                quadrant_number=1, 
                missing_teeth=q_data["q1_missing"], 
                present_teeth=q_data["q1_present"],
                impacted_teeth=q_data["q1_impacted"],
                not_visualized_teeth=q_data["q1_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_2=QuadrantAnalysis(
                quadrant_number=2, 
                missing_teeth=q_data["q2_missing"], 
                present_teeth=q_data["q2_present"],
                impacted_teeth=q_data["q2_impacted"],
                not_visualized_teeth=q_data["q2_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_3=QuadrantAnalysis(
                quadrant_number=3, 
                missing_teeth=q_data["q3_missing"], 
                present_teeth=q_data["q3_present"],
                impacted_teeth=q_data["q3_impacted"],
                not_visualized_teeth=q_data["q3_not_viz"],
                notes="Parsed from Examiner table"
            ),
            quadrant_4=QuadrantAnalysis(
                quadrant_number=4, 
                missing_teeth=q_data["q4_missing"], 
                present_teeth=q_data["q4_present"],
                impacted_teeth=q_data["q4_impacted"],
                not_visualized_teeth=q_data["q4_not_viz"],
                notes="Parsed from Examiner table"
            ),
            confidence=0.90, 
            raw_response=text
        )
    
    def _create_error_result(self, error: str) -> ModelAnalysisResult:
        empty_quadrant = lambda n: QuadrantAnalysis(
            quadrant_number=n, missing_teeth=[], present_teeth=[], notes=f"Error: {error}"
        )
        return ModelAnalysisResult(
            model_name="Anthropic Claude",
            quadrant_1=empty_quadrant(1),
            quadrant_2=empty_quadrant(2),
            quadrant_3=empty_quadrant(3),
            quadrant_4=empty_quadrant(4),
            confidence=0.0,
            raw_response=f"Error: {error}"
        )


class DecidingModelClient:
    """GPT-5.2 client that decides which model's analysis is most accurate."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GPT52_MODEL
    
    async def decide(
        self,
        image_base64: str,
        mime_type: str,
        gpt4o_result: ModelAnalysisResult,
        gemini_result: ModelAnalysisResult,
        anthropic_result: ModelAnalysisResult
    ) -> DecidingModelResult:
        
        logger.info(f"🟡 GPT-5.2 Deciding Model: Starting decision process...")
        
        deciding_prompt = f"""You are an expert dental radiologist and the final arbiter in a multi-model dental analysis system.

You have been given an OPG (Orthopantomogram) dental X-ray image and the analysis results from three different AI models.
Your task is to:
1. Analyze the image yourself
2. Compare your analysis with the three model outputs
3. Decide which model (if any) provided the most accurate analysis
4. If all models are wrong or significantly inaccurate, provide your own corrected analysis

## Model Results:

### GPT-4o Analysis:
- Quadrant 1 (Upper Right) Missing: {gpt4o_result.quadrant_1.missing_teeth}
- Quadrant 2 (Upper Left) Missing: {gpt4o_result.quadrant_2.missing_teeth}
- Quadrant 3 (Lower Left) Missing: {gpt4o_result.quadrant_3.missing_teeth}
- Quadrant 4 (Lower Right) Missing: {gpt4o_result.quadrant_4.missing_teeth}
- Confidence: {gpt4o_result.confidence}

### Gemini Analysis:
- Quadrant 1 (Upper Right) Missing: {gemini_result.quadrant_1.missing_teeth}
- Quadrant 2 (Upper Left) Missing: {gemini_result.quadrant_2.missing_teeth}
- Quadrant 3 (Lower Left) Missing: {gemini_result.quadrant_3.missing_teeth}
- Quadrant 4 (Lower Right) Missing: {gemini_result.quadrant_4.missing_teeth}
- Confidence: {gemini_result.confidence}

### Anthropic Claude Analysis:
- Quadrant 1 (Upper Right) Missing: {anthropic_result.quadrant_1.missing_teeth}
- Quadrant 2 (Upper Left) Missing: {anthropic_result.quadrant_2.missing_teeth}
- Quadrant 3 (Lower Left) Missing: {anthropic_result.quadrant_3.missing_teeth}
- Quadrant 4 (Lower Right) Missing: {anthropic_result.quadrant_4.missing_teeth}
- Confidence: {anthropic_result.confidence}

## Instructions:
Analyze the dental X-ray image and provide your decision in the following JSON format:

{{
    "internal_scratchpad_step_1_independent_analysis": "Detailed independent findings for each quadrant based ONLY on the image.",
    "internal_scratchpad_step_2_comparison": "Comparison with GPT-4o, Gemini, and Claude outputs.",
    "selected_model": "GPT-4o" or "Gemini" or "Anthropic Claude" or null (if you're providing your own analysis),
    "reasoning": "The FINAL CLINICAL RADIOGRAPHIC REPORT to be displayed to the doctor. Synthesize your independent analysis into a clear, professional statement explaining the final diagnosis. \n\n**CRITICAL INSTRUCTIONS:**\n- DO NOT mention 'Step 1' or 'Step 2'.\n- DO NOT mention 'models', 'AI', 'GPT-4o', 'Gemini', 'Claude', 'Consensus', or 'Agreement'.\n- Focus ONLY on the radiographic findings and clinical impression.\n- Use a professional, medical tone.\n- Structure with markdown headers (###) and bullet points.",
    "agreement_score": 0.0 to 1.0 (how much the models agreed with each other),
    "final_analysis": {{
        "quadrant_1": {{
            "quadrant_number": 1,
            "missing_teeth": [],
            "present_teeth": [],
            "impacted_teeth": [],
            "not_visualized_teeth": [],
            "notes": "Detailed clinical observation"
        }},
        "quadrant_2": {{
            "quadrant_number": 2,
            "missing_teeth": [],
            "present_teeth": [],
            "impacted_teeth": [],
            "not_visualized_teeth": [],
            "notes": ""
        }},
        "quadrant_3": {{
            "quadrant_number": 3,
            "missing_teeth": [],
            "present_teeth": [],
            "impacted_teeth": [],
            "not_visualized_teeth": [],
            "notes": ""
        }},
        "quadrant_4": {{
            "quadrant_number": 4,
            "missing_teeth": [],
            "present_teeth": [],
            "impacted_teeth": [],
            "not_visualized_teeth": [],
            "notes": ""
        }},
        "confidence": 0.9
    }}
}}

Respond ONLY with valid JSON."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": deciding_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            logger.info(f"🟡 GPT-5.2 Raw Response:\n{raw_response}")
            result = json.loads(raw_response)
            
            final_analysis = result["final_analysis"]
            
            logger.info(f"🟡 GPT-5.2 Decision:")
            logger.info(f"   Selected Model: {result.get('selected_model', 'Own Analysis')}")
            logger.info(f"   Agreement Score: {result.get('agreement_score', 'N/A')}")
            logger.info(f"   Reasoning: {result.get('reasoning', 'N/A')[:200]}...")
            logger.info(f"   Final Q1 Missing: {final_analysis['quadrant_1'].get('missing_teeth', [])}")
            logger.info(f"   Final Q2 Missing: {final_analysis['quadrant_2'].get('missing_teeth', [])}")
            logger.info(f"   Final Q3 Missing: {final_analysis['quadrant_3'].get('missing_teeth', [])}")
            logger.info(f"   Final Q4 Missing: {final_analysis['quadrant_4'].get('missing_teeth', [])}")
            
            return DecidingModelResult(
                selected_model=result.get("selected_model"),
                final_analysis=ModelAnalysisResult(
                    model_name="GPT-5.2 (Deciding Model)",
                    quadrant_1=QuadrantAnalysis(**final_analysis["quadrant_1"]),
                    quadrant_2=QuadrantAnalysis(**final_analysis["quadrant_2"]),
                    quadrant_3=QuadrantAnalysis(**final_analysis["quadrant_3"]),
                    quadrant_4=QuadrantAnalysis(**final_analysis["quadrant_4"]),
                    confidence=final_analysis.get("confidence", 0.9),
                    raw_response=raw_response
                ),
                reasoning=result.get("reasoning", "No reasoning provided"),
                agreement_score=result.get("agreement_score", 0.0)
            )
        except Exception as e:
            logger.error(f"🟡 GPT-5.2 Error: {str(e)}")
            return self._create_error_result(str(e), gpt4o_result)
    
    def _create_error_result(self, error: str, fallback: ModelAnalysisResult) -> DecidingModelResult:
        return DecidingModelResult(
            selected_model="GPT-4o",
            final_analysis=ModelAnalysisResult(
                model_name="GPT-5.2 (Error - Using Fallback)",
                quadrant_1=fallback.quadrant_1,
                quadrant_2=fallback.quadrant_2,
                quadrant_3=fallback.quadrant_3,
                quadrant_4=fallback.quadrant_4,
                confidence=fallback.confidence * 0.5,
                raw_response=f"Error in deciding model: {error}. Using GPT-4o as fallback."
            ),
            reasoning=f"Deciding model encountered an error: {error}. Defaulting to GPT-4o result.",
            agreement_score=0.0
        )
