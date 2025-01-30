import os

markdown_enabled = False
markdown_install_fail = False

def configure(markdown_status):
    global markdown_enabled
    if markdown_status.lower() == "yes":
        markdown_enabled = True
    elif markdown_status.lower() == "no":
        markdown_enabled = False
    else:
        print("Unknown Setting")
        markdown_enabled = False

configure("yes")  # Example to set markdown_enabled, can be changed as needed

if markdown_enabled:
    try:
        import markdown
    except ImportError:
        print("Markdown failed to import.\nAttempting to install it.")
        try:
            os.system("pip install markdown")
            import markdown  # Try importing again after installation
        except:
            print("Error: Could Not install Markdown\nUsing basic built-in interpreting")
            markdown_install_fail = True

def basic_markdown_to_html(text):
    text = text.replace("**", "<b>").replace("**", "</b>")
    text = text.replace("```html", "<pre><code>").replace("```", "</code></pre>")
    return text

def convert(text):
    if markdown_enabled and not markdown_install_fail:
        print("Converting to Markdown...")
        return markdown.markdown(text)
    else:
        print("Using basic Markdown to HTML conversion...")
        return basic_markdown_to_html(text)
