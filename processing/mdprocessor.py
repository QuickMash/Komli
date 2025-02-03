import markdown
import re

codeblockid = 0

def extract_code_blocks(html):
    """ Extracts content inside <pre><code> blocks and replaces them with placeholders """
    code_blocks = []
    
    def replacer(match):
        code_blocks.append(match.group(1))  # Store only the content inside <code>
        return f"<!--CODE_BLOCK_{len(code_blocks)-1}-->"
    
    html = re.sub(r'<pre><code.*?>(.*?)</code></pre>', replacer, html, flags=re.DOTALL)
    return html, code_blocks

def restore_code_blocks(html, code_blocks):
    """ Restores saved code content inside <pre><code> blocks """
    global codeblockid  # Ensure we're modifying the global codeblockid
    for i, block in enumerate(code_blocks):
        html = html.replace(
            f"<!--CODE_BLOCK_{codeblockid}-->",
            f'<div class="copybtn"><button onclick="copyToClipboard(\'codeblock-{codeblockid}\')" id="copybtn-{codeblockid}">copy <i class="fa-regular fa-copy"></i></button></div>'
            f'<div class="codeblock"<pre><code id="codeblock-{codeblockid}">{block}</code></pre></div>'
        )
        codeblockid += 1
    return html

def convert(markdown_text):
    """
    Converts Markdown to HTML while:
    - Preserving code blocks
    - Removing <p> tags outside of code blocks
    - Adding copy buttons for code blocks
    """
    global codeblockid  # Ensure we're modifying the global codeblockid
    codeblockid = 0  # Reset the codeblockid for each new Markdown processing
    # Convert Markdown to HTML with fenced code blocks enabled
    html_output = markdown.markdown(markdown_text, extensions=['fenced_code'])

    # Step 1: Extract and save code blocks
    html_output, code_blocks = extract_code_blocks(html_output)

    # Step 2: Remove all <p> tags from the remaining content
    html_output = re.sub(r'<p>(.*?)</p>', r'\1', html_output)

    # Step 3: Restore code blocks with copy buttons
    html_output = restore_code_blocks(html_output, code_blocks)

    return html_output

# JavaScript function for copying
js_copy_script = """
<script>
function copyToClipboard(id) {
    var codeElement = document.getElementById(id);
    var textArea = document.createElement("textarea");
    textArea.value = codeElement.innerText;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy");
    document.body.removeChild(textArea);
    document.getElementById("copybtn-" + id.split("-")[1]).innerHTML = "Copied <i class='fa-regular fa-check'></i>";
}
</script>
"""

