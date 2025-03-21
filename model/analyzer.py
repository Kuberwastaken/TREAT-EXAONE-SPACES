import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from datetime import datetime
import gradio as gr
from typing import Dict, List, Union, Optional
import logging
import traceback
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentAnalyzer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.batch_size = 2  # Reduced batch size for deeper thinking
        self.max_thinking_time = 30  # Maximum seconds per batch for reasoning
        self.trigger_categories = {
            "Violence": {
                "mapped_name": "Violence",
                "description": "Physical force, aggression, or actions causing harm to living beings or property."
            },
            "Death": {
                "mapped_name": "Death References",
                "description": "Direct or implied loss of life, mortality discussions, or death-related events."
            },
            "Substance_Use": {
                "mapped_name": "Substance Use",
                "description": "Usage or discussion of drugs, alcohol, or addictive substances."
            },
            "Gore": {
                "mapped_name": "Gore",
                "description": "Graphic depictions of injuries, blood, or severe bodily harm."
            },
            "Sexual_Content": {
                "mapped_name": "Sexual Content",
                "description": "Sexual activity, intimacy, or explicit sexual references."
            },
            "Sexual_Abuse": {
               "mapped_name": "Sexual Abuse",
               "description": "Non-consensual sexual acts, exploitation, or sexual violence."
            },
            "Self_Harm": {
                "mapped_name": "Self-Harm",
                "description": "Self-inflicted injury, suicidal thoughts, or destructive behaviors."
            },
            "Mental_Health": {
                "mapped_name": "Mental Health Issues",
                "description": "Psychological distress, mental disorders, or emotional trauma."
            }
        }
        logger.info(f"Initialized analyzer with device: {self.device}")

    async def load_model(self, progress=None) -> None:
        """Load the model and tokenizer with progress updates."""
        try:
            if progress:
                progress(0.1, "Loading tokenizer...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                "LGAI-EXAONE/EXAONE-Deep-2.4B",
                use_fast=True,
                trust_remote_code=True
            )
            
            if progress:
                progress(0.3, "Loading model...")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                "LGAI-EXAONE/EXAONE-Deep-2.4B",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
            
            if self.device == "cuda":
                self.model.eval()
                torch.cuda.empty_cache()
                
            if progress:
                progress(0.5, "Model loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def _chunk_text(self, text: str, chunk_size: int = 20000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def _validate_response(self, response: str) -> str:
        """Validate and clean model response."""
        valid_responses = {"YES", "NO", "MAYBE"}
        response = response.strip().upper()
        first_word = response.split()[0] if response else "NO"
        return first_word if first_word in valid_responses else "NO"

    async def _generate_outputs(self, inputs):
        """Helper method to generate outputs with torch.no_grad()."""
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=500, 
                temperature=0.3,   # Lower temperature for more focused responses
                top_p=0.95,       # Slightly higher to ensure valid responses
                top_k=10,         # Reduced to limit vocabulary to relevant tokens
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=True    # Keep sampling for slight variation
            )
        return outputs

    async def analyze_chunks_batch(
        self,
        chunks: List[str],
        progress: Optional[gr.Progress] = None,
        current_progress: float = 0,
        progress_step: float = 0
    ) -> Dict[str, float]:
        """Analyze multiple chunks in batches."""
        all_triggers = {}
        
        for category, info in self.trigger_categories.items():
            mapped_name = info["mapped_name"]
            description = info["description"]
            
            for i in range(0, len(chunks), self.batch_size):
                batch_chunks = chunks[i:i + self.batch_size]
                prompts = []
                
                for chunk in batch_chunks:
                    prompt = f"Analyze text for {mapped_name}. Definition: {description}. Content: \"{chunk}\". Answer YES/NO/MAYBE based on clear evidence."
                    prompts.append(prompt)

                try:
                    inputs = self.tokenizer(
                        prompts,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=512
                    ).to(self.device)
                    
                    outputs = await asyncio.wait_for(
                    self._generate_outputs(inputs),
                    timeout=self.max_thinking_time
                )
                    
                    responses = [
                        self.tokenizer.decode(output, skip_special_tokens=True)
                        for output in outputs
                    ]
                    
                    for response in responses:
                        validated_response = self._validate_response(response)
                        if validated_response == "YES":
                            all_triggers[mapped_name] = all_triggers.get(mapped_name, 0) + 1
                        elif validated_response == "MAYBE":
                            all_triggers[mapped_name] = all_triggers.get(mapped_name, 0) + 0.5
                
                except asyncio.TimeoutError:
                    logger.error(f"Timeout processing batch for {mapped_name}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing batch for {mapped_name}: {str(e)}")
                    continue
                
                if progress:
                    current_progress += progress_step
                    progress(min(current_progress, 0.9), f"Analyzing {mapped_name}...")
                    
        return all_triggers

    async def analyze_script(self, script: str, progress: Optional[gr.Progress] = None) -> List[str]:
        """Analyze the entire script."""
        if not self.model or not self.tokenizer:
            await self.load_model(progress)
        
        chunks = self._chunk_text(script)
        identified_triggers = await self.analyze_chunks_batch(
            chunks,
            progress,
            current_progress=0.5,
            progress_step=0.4 / (len(chunks) * len(self.trigger_categories))
        )
        
        if progress:
            progress(0.95, "Finalizing results...")

        final_triggers = []
        chunk_threshold = max(1, len(chunks) * 0.1)
        
        for mapped_name, count in identified_triggers.items():
            if count >= chunk_threshold:
                final_triggers.append(mapped_name)

        return final_triggers if final_triggers else ["None"]

async def analyze_content(
    script: str,
    progress: Optional[gr.Progress] = None
) -> Dict[str, Union[List[str], str]]:
    """Main analysis function for the Gradio interface."""
    logger.info("Starting content analysis")
    
    analyzer = ContentAnalyzer()
    
    try:
        # Fix: Use the analyzer instance's method instead of undefined function
        triggers = await analyzer.analyze_script(script, progress)
        
        if progress:
            progress(1.0, "Analysis complete!")

        result = {
            "detected_triggers": triggers,
            "confidence": "High - Content detected" if triggers != ["None"] else "High - No concerning content detected",
            "model": "LGAI-EXAONE/EXAONE-Deep-2.4B",
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        logger.info(f"Analysis complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return {
            "detected_triggers": ["Error occurred during analysis"],
            "confidence": "Error", 
            "model": "LGAI-EXAONE/EXAONE-Deep-2.4B",
            "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e)
        }

if __name__ == "__main__":
    iface = gr.Interface(
        fn=analyze_content,
        inputs=gr.Textbox(lines=8, label="Input Text"),
        outputs=gr.JSON(),
        title="Content Trigger Analysis",
        description="Analyze text content for sensitive topics and trigger warnings"
    )
    iface.launch()