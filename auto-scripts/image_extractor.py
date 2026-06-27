import os
import fitz  # PyMuPDF
import logging
from pathlib import Path
from alert import send_discord_alert


# Keep console logging active so it shows up in the GitHub Actions UI logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_scheme_pages(input_dir: str = "syllabus_pdfs", output_dir: str = "extracted_tables") -> bool:
    """
    SLICING ENGINE: Slices out scheme/index pages and converts them to high-res images.
    Returns True if execution passes flawlessly, False if a critical system failure occurs.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        error_msg = f"### 🚨 Phase 3 ABORTED: System Error\nFailed to create image output directory `{output_dir}`: `{str(e)}`"
        logging.error(error_msg)
        send_discord_alert(error_msg)
        return False

    target_phrase = "scheme of instruction and examination"
    exclude_bridge = "bridge course" 
    exclude_service = "service courses offered by"
    
    zoom_x, zoom_y = 2.0, 2.0  
    mat = fitz.Matrix(zoom_x, zoom_y)

    total_images_extracted = 0
    processed_depts = set()
    base_path = Path(input_dir)

    pdf_files = sorted(list(base_path.glob("*/*.pdf")))

    if not pdf_files:
        error_msg = f"### 🚨 Phase 3 ABORTED: Data Insufficiency\nNo PDF documents located in `{input_dir}/*/*.pdf`"
        logging.error(error_msg)
        send_discord_alert(error_msg)
        return False

    for pdf_path in pdf_files:
        dept_name = pdf_path.parent.name
        file_name = pdf_path.name
        doc_image_count = 0
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").lower()
                
                if (target_phrase in text and 
                    exclude_bridge not in text and 
                    exclude_service not in text):
                    
                    pix = page.get_pixmap(matrix=mat)
                    
                    safe_filename = file_name.replace('.pdf', '')
                    output_filename = f"{dept_name}__{safe_filename}__p{page_num + 1}.png"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    pix.save(output_path)
                    doc_image_count += 1
                    total_images_extracted += 1
                    processed_depts.add(dept_name)
                    
            doc.close()
            logging.info(f"Processed '{dept_name} -> {file_name}': Extracted {doc_image_count} images.")
            
        except Exception as e:
            error_msg = (
                f"### 🚨 Phase 3 ABORTED: Extraction Failure\n"
                f"- **Department:** `{dept_name}`\n"
                f"- **Document:** `{file_name}`\n"
                f"- **Details:** PyMuPDF rendering exception. `{str(e)}`"
            )
            logging.error(error_msg)
            send_discord_alert(error_msg)
            return False

    if total_images_extracted == 0:
        error_msg = f"### 🚨 Phase 3 ABORTED: Target Not Found\nScanned all files, but zero pages matched the phrase: '{target_phrase}'."
        logging.error(error_msg)
        send_discord_alert(error_msg)
        return False

    # Send persistent summary to Discord
    summary_msg = (
        f"### ✅ Phase 3 Completed: Image Extraction\n"
        f"- **Departments Processed:** {len(processed_depts)} ({', '.join(processed_depts)})\n"
        f"- **Total Target Pages Sliced:** {total_images_extracted}\n"
        f"- **Status:** Ready for LLM Vision parsing."
    )
    logging.info("Sending execution summary to Discord...")
    send_discord_alert(summary_msg)

    return True

if __name__ == "__main__":
    success = extract_scheme_pages()
    print(f"Execution complete status verification: {success}")