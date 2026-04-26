"""
Test script to add a debug endpoint to mcp_server.py
This will help us see the exact PDF generation error
"""

debug_endpoint_code = '''

@app.get("/mcp/debug-pdf")
def debug_pdf_generation():
    """Debug endpoint to test PDF generation and return detailed errors"""
    import traceback
    from config.settings import OUTPUT_DIR
    import json
    
    try:
        # Load insights
        insights_file = OUTPUT_DIR / "clustered_insights.json"
        if not insights_file.exists():
            return {"error": "No insights file found", "path": str(insights_file)}
        
        with open(insights_file, 'r') as f:
            insights = json.load(f)
        
        # Try to generate PDFs
        from tools.pdf_note import generate_all_pdf_notes
        
        action_ideas = insights.get("action_ideas", [])
        if isinstance(action_ideas, str):
            action_ideas = [action_ideas]
        
        pdf_paths = generate_all_pdf_notes(insights, action_ideas)
        
        return {
            "status": "success",
            "pdfs_generated": len(pdf_paths),
            "pdf_files": pdf_paths,
            "output_dir": str(OUTPUT_DIR)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

'''

print("="*60)
print("DEBUG ENDPOINT CODE")
print("="*60)
print("\nAdd this code to backend/mcp_server.py before the line:")
print('# ==================== Existing Endpoints ====================')
print("\nHere's the code to add:\n")
print(debug_endpoint_code)
print("\n" + "="*60)
print("After adding this code:")
print("1. Commit and push to GitHub")
print("2. Deploy on Render")
print("3. Visit: https://kuvera-pulse.onrender.com/mcp/debug-pdf")
print("4. Share the error message you see")
print("="*60)
