import gradio as gr
from model.analyzer import analyze_content
import asyncio
import time
import httpx
import subprocess
import atexit

# Start the API server
def start_api_server():
    # Start uvicorn in a subprocess
    process = subprocess.Popen(["uvicorn", "script_search_api:app", "--reload"])
    return process

# Stop the API server
def stop_api_server(process):
    process.terminate()

# Register the exit handler
api_process = start_api_server()
atexit.register(stop_api_server, api_process)

custom_css = """
* {
    font-family: 'Inter', system-ui, sans-serif;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.gradio-container {
    background: #0a0a0f !important;
    color: #fff !important;
    min-height: 100vh;
    position: relative;
    overflow: hidden;
}

/* Animated Background */
.gradio-container::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        linear-gradient(125deg, 
            #db2777 0%, 
            rgba(219, 39, 119, 0.05) 30%,
            rgba(219, 39, 119, 0.1) 50%,
            rgba(219, 39, 119, 0.05) 70%,
            #db2777 100%);
    animation: gradientMove 15s ease infinite;
    background-size: 400% 400%;
    z-index: 0;
}

/* Floating Particles */
.gradio-container::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, transparent 0%, #0a0a0f 70%),
                url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='50' cy='50' r='1' fill='rgba(219, 39, 119, 0.15)'/%3E%3C/svg%3E");
    opacity: 0.5;
    animation: floatingParticles 20s linear infinite;
    z-index: 1;
}

/* Futuristic Header */
.treat-title {
    text-align: center;
    padding: 3rem 1rem;
    position: relative;
    overflow: hidden;
    z-index: 2;
    background: linear-gradient(180deg, 
        rgba(219, 39, 119, 0.1),
        transparent 70%);
}

.treat-title::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    width: 80%;
    height: 1px;
    background: linear-gradient(90deg, 
        transparent,
        rgba(219, 39, 119, 0.5),
        transparent);
    transform: translateX(-50%);
    animation: scanline 3s ease-in-out infinite;
}

.treat-title h1 {
    font-size: 4.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, 
        #db2777 0%,
        #db2777 50%,
        #db2777 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    letter-spacing: -0.05em;
    animation: gradientFlow 8s ease infinite;
    position: relative;
}

.treat-title h1::after {
    content: attr(data-text);
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, 
        transparent 0%,
        rgba(219, 39, 119, 0.4) 50%,
        transparent 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    opacity: 0.5;
    animation: textGlow 4s ease-in-out infinite;
}

.treat-title p {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.7);
    max-width: 600px;
    margin: 0 auto;
    position: relative;
    animation: fadeInUp 1s ease-out;
}

/* Tabs Styling */
.tabs {
    background: rgba(17, 17, 27, 0.7);
    border: 1px solid rgba(219, 39, 119, 0.2);
    border-radius: 16px;
    padding: 1rem;
    margin: 0 1rem 2rem 1rem;
    position: relative;
    z-index: 2;
    backdrop-filter: blur(10px);
    box-shadow: 0 0 30px rgba(219, 39, 119, 0.1);
    animation: floatIn 1s ease-out;
}

.tabs::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(45deg,
        rgba(219, 39, 119, 0.1),
        transparent,
        rgba(219, 39, 119, 0.1));
    border-radius: 16px;
    z-index: -1;
    animation: borderGlow 4s ease-in-out infinite;
}

/* Content Area */
.content-area {
    background: rgba(17, 17, 27, 0.7) !important;
    border: 1px solid rgba(219, 39, 119, 0.2) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
    animation: fadeScale 0.5s ease-out;
}

.content-area::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at center,
        rgba(219, 39, 119, 0.1) 0%,
        transparent 70%);
    animation: rotateGradient 10s linear infinite;
}

/* Input Fields */
.gradio-textbox textarea {
    background: rgba(17, 17, 27, 0.6) !important;
    border: 1px solid rgba(219, 39, 119, 0.3) !important;
    border-radius: 8px !important;
    color: rgba(255, 255, 255, 0.9) !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    padding: 1rem !important;
    transition: all 0.3s ease;
    position: relative;
    z-index: 2;
}

.gradio-textbox textarea:focus {
    border-color: #db2777 !important;
    box-shadow: 0 0 20px rgba(219, 39, 119, 0.2) !important;
    background: rgba(17, 17, 27, 0.8) !important;
    transform: translateY(-2px);
}

/* Buttons */
.gradio-button {
    background: linear-gradient(45deg, 
        #db2777,
        #db2777,
        #db2777) !important;
    background-size: 200% auto !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1.5rem !important;
    letter-spacing: 0.025em !important;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease !important;
    animation: gradientFlow 3s ease infinite;
}

/* Rest of the CSS remains the same until the footer link color */

.footer .name {
    color: #db2777;
    text-decoration: none;
    position: relative;
    transition: all 0.3s ease;
    padding: 0 4px;
}

.footer .name:hover {
    color: #db2777;
}

/* Rest of the code remains exactly the same */
"""

# The rest of the Python code remains exactly the same
async def analyze_with_progress(movie_name, progress=gr.Progress()):
    """Handle analysis with progress updates in Gradio"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Start the analysis
            response = await client.get(
                "http://localhost:8000/api/start_analysis",
                params={"movie_name": movie_name}
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            
            # Poll for progress
            while True:
                progress_response = await client.get(
                    f"http://localhost:8000/api/progress/{task_id}"
                )
                progress_response.raise_for_status()
                status = progress_response.json()
                
                # Update Gradio progress
                progress(status["progress"], desc=status["status"])
                
                if status["is_complete"]:
                    if status["error"]:
                        return f"Error: {status['error']}"
                    elif status["result"]:
                        triggers = status["result"].get("detected_triggers", [])
                        if not triggers or triggers == ["None"]:
                            return "✓ No triggers detected in the content."
                        else:
                            trigger_list = "\n".join([f"• {trigger}" for trigger in triggers])
                            return f"⚠ Triggers Detected:\n{trigger_list}"
                    break
                
                await asyncio.sleep(0.5)
    
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_with_loading(text, progress=gr.Progress()):
    """
    Synchronous wrapper for the async analyze_content function with smooth progress updates
    """
    # Initialize progress
    progress(0, desc="Starting analysis...")
    
    # Initial setup phase - smoother progression
    for i in range(25):
        time.sleep(0.04)  # Slightly longer sleep for smoother animation
        progress((i + 1) / 100, desc="Initializing analysis...")
    
    # Pre-processing phase
    for i in range(25, 45):
        time.sleep(0.03)
        progress((i + 1) / 100, desc="Pre-processing content...")
    
    # Perform analysis
    progress(0.45, desc="Analyzing content...")
    try:
        result = asyncio.run(analyze_content(text))
        
        # Analysis progress simulation
        for i in range(45, 75):
            time.sleep(0.03)
            progress((i + 1) / 100, desc="Processing results...")
            
    except Exception as e:
        return f"Error during analysis: {str(e)}"
    
    # Final processing with smooth progression
    for i in range(75, 100):
        time.sleep(0.02)
        progress((i + 1) / 100, desc="Finalizing results...")
    
    # Format the results
    triggers = result["detected_triggers"]
    if triggers == ["None"]:
        return "✓ No triggers detected in the content."
    else:
        trigger_list = "\n".join([f"• {trigger}" for trigger in triggers])
        return f"⚠ Triggers Detected:\n{trigger_list}"

# Update the Gradio interface with new styling
with gr.Blocks(css=custom_css, theme=gr.themes.Base()) as iface:
    # Title section
    gr.HTML("""
        <div class="treat-title">
            <h1 data-text="TREAT">TREAT</h1>
            <p>Trigger Recognition for Enjoyable and Appropriate Television</p>
        </div>
    """)
    
    with gr.Tabs() as tabs:
        with gr.Tab("Content Analysis"):
            with gr.Column():
                input_text = gr.Textbox(
                    label="ANALYZE CONTENT",
                    placeholder="Enter the content you want to analyze...",
                    lines=8
                )
                analyze_btn = gr.Button("✨ Analyze")
        
        with gr.Tab("Movie Search"):
            with gr.Column():
                search_query = gr.Textbox(
                    label="SEARCH MOVIES",
                    placeholder="Type a movie title to search...",
                    lines=1
                )
                search_button = gr.Button("🔍 Search")
    
    output_text = gr.Textbox(
        label="ANALYSIS RESULTS",
        lines=5,
        interactive=False
    )
    
    status_text = gr.Markdown(
        value=""
    )
    
    # Define click events
    analyze_btn.click(
        fn=analyze_with_loading,
        inputs=input_text,
        outputs=output_text
    )
    
    search_button.click(
        fn=analyze_with_progress,
        inputs=search_query,
        outputs=output_text
    )

    gr.HTML("""
        <div class="footer">
            <p>Made with <span class="heart">💖</span> by <a href="https://www.linkedin.com/in/kubermehta/" target="_blank">Kuber Mehta</a></p>
        </div>
    """)

if __name__ == "__main__":
    iface.launch(
        share=False,
        debug=True,
        show_error=True
    )