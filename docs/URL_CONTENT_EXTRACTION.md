# URL Content Extraction & Summarization 🔗

Your AI Coding Assistant can now **automatically detect links** in your messages, fetch their content, and summarize them!

## How It Works

### Automatic Detection ✨
The system automatically:
1. **Detects URLs** in your message using regex pattern matching
2. **Fetches content** from each URL (up to 3 URLs per message)
3. **Extracts readable text** using BeautifulSoup4 (removes scripts, styles, navigation)
4. **Feeds content to the model** as additional context
5. **Generates a summary** based on your question and the URL content

### Example Usage

**Just paste a URL in your message:**

```
Summarize this article: https://example.com/article-about-ai
```

**Ask questions about the content:**

```
What are the key points from https://blog.techcrunch.com/latest-ai-news?
```

**Multiple URLs:**

```
Compare these two articles:
https://site1.com/article-a
https://site2.com/article-b
```

**With context:**

```
I'm building a Python web app. What best practices are mentioned here?
https://realpython.com/flask-best-practices/
```

---

## Features

### ✅ What It Can Do:
- **Extract article text** from news sites, blogs, documentation
- **Fetch webpage content** (HTML pages)
- **Remove clutter** (navigation, ads, scripts)
- **Handle up to 3 URLs** per message
- **Process any HTTP/HTTPS link**
- **Show you which URLs were processed** with toast notifications
- **Truncate long content** (max 5000 chars per URL, 2000 in prompt)

### ❌ Limitations:
- Cannot process **PDFs** directly (only HTML)
- Cannot access **password-protected** pages
- Cannot render **JavaScript-heavy** SPA content (use server-side rendering)
- Limited to **3 URLs** per message to avoid overload
- **10 second timeout** per URL fetch

---

## Technical Details

### URL Detection Pattern
```python
url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
```

### Content Extraction Process

1. **HTTP Request** with user agent
   ```python
   headers = {'User-Agent': 'Mozilla/5.0 ...'}
   response = requests.get(url, timeout=10, headers=headers)
   ```

2. **Parse HTML** with BeautifulSoup4
   ```python
   soup = BeautifulSoup(response.content, 'html.parser')
   ```

3. **Remove unwanted elements**
   - Scripts (`<script>`)
   - Styles (`<style>`)
   - Navigation (`<nav>`)
   - Headers & Footers (`<header>`, `<footer>`)

4. **Extract clean text**
   ```python
   text = soup.get_text()
   # Clean whitespace and format
   ```

5. **Include in prompt**
   ```python
   enriched_prompt = f"""
   {original_prompt}
   
   --- Fetched URL Content ---
   Content from {url}:
   Title: {title}
   {content}
   --- End of URL Content ---
   
   Please analyze and summarize...
   """
   ```

---

## Usage Examples

### Example 1: Documentation Research

**Your message:**
```
How do I use FastAPI middleware? https://fastapi.tiangolo.com/tutorial/middleware/
```

**What happens:**
1. ✅ URL detected: `https://fastapi.tiangolo.com/tutorial/middleware/`
2. 📥 Fetches page content
3. 📄 Extracts text from the documentation
4. 🤖 Model reads the content and explains it to you
5. 💬 You get a summary + answer to your question

---

### Example 2: News Article Summary

**Your message:**
```
Summarize the key points: https://www.theverge.com/latest-tech-article
```

**System response:**
- 🔗 Shows toast: "Fetched content from 1 URL(s): [Article Title]"
- 💬 Provides summary of the article
- ✅ Answers based on actual content (not hallucination!)

---

### Example 3: Code Comparison

**Your message:**
```
Compare these two approaches:
https://realpython.com/flask-tutorial/
https://fastapi.tiangolo.com/tutorial/
```

**System response:**
- 🔗 Fetches both URLs
- 📊 Compares the content
- 💡 Highlights differences
- 🎯 Recommends which to use

---

## Advanced Use Cases

### Research & Learning
```
Explain the concepts from these three articles:
https://blog1.com/article1
https://blog2.com/article2
https://blog3.com/article3
```

### Code Examples
```
Show me how to implement the pattern described here:
https://github.com/repo/README.md
```

### Documentation Help
```
I'm getting an error. What does this error mean?
https://docs.python.org/3/library/exceptions.html
```

### Troubleshooting
```
Fix my code based on these recommendations:
https://stackoverflow.com/questions/12345/solution
```

---

## How to See It Working

### Visual Indicators

1. **Console Output** (Server logs)
   ```
   🔗 Found 1 URL(s) in prompt: ['https://example.com']
   📎 Processed 1 URL(s) and enriched prompt with content
   ```

2. **Browser Toast Notification**
   ```
   🔗 Fetched content from 1 URL(s): Page Title
   ```

3. **Response includes URL context**
   - Model's answer will be based on the actual URL content
   - Will reference specific information from the page

---

## Configuration

### Limits (in `web_server.py`)

```python
# Maximum URLs to process per message
MAX_URLS = 3  # Line: for url in urls[:3]

# Maximum characters per URL
MAX_CHARS_PER_URL = 5000  # Line: max_chars=5000

# Content included in prompt per URL  
PROMPT_CHARS_PER_URL = 2000  # Line: [:2000]

# Request timeout
TIMEOUT = 10  # seconds
```

### To Adjust Limits:

1. Open `web_server.py`
2. Find `fetch_url_content(url, max_chars=5000)`
3. Change the `max_chars` parameter
4. Find `item['content'][:2000]`
5. Change the slice limit
6. Restart server

---

## Troubleshooting

### "Failed to fetch URL"

**Possible causes:**
- Website blocks bots
- Page requires JavaScript
- Timeout (>10 seconds)
- Network error
- Invalid SSL certificate

**Solutions:**
```python
# Already implemented in code:
- Custom User-Agent header
- 10 second timeout
- SSL verification (can be disabled if needed)
- Redirect following enabled
```

### "Content not relevant"

Make sure:
- URL is accessible (not behind paywall)
- Page is in English (or your target language)
- Content is text-based (not image/video heavy)

### "No content extracted"

Check if:
- Page is JavaScript-rendered (use archive.org version)
- Content is in iframe
- Page has anti-scraping protection

---

## Code Locations

### Backend (web_server.py)

```python
# Line ~70-77: URL detection
def detect_urls(text: str) -> list[str]

# Line ~80-135: Content extraction  
def fetch_url_content(url: str, max_chars: int = 5000) -> dict

# Line ~138-170: URL processing pipeline
def process_urls_in_prompt(prompt: str) -> tuple[str, list[dict]]

# Line ~623-627: Integration in generation flow
url_enriched_prompt, fetched_urls = process_urls_in_prompt(...)
```

### Frontend (templates/index.html)

```javascript
// Line ~819-830: Toast notification for processed URLs
if (event.payload?.urls_processed && ...) {
    showToast(`🔗 Fetched content from ${urlCount} URL(s)...`)
}
```

---

## Benefits

### ✅ Accurate Information
- No hallucination - model reads actual content
- Up-to-date information from live pages
- Specific details from documentation

### ✅ Time Saving
- No need to manually copy/paste content
- Instant summaries of long articles
- Quick comparison of multiple sources

### ✅ Better Context
- Model understands your specific resource
- Can reference exact sections
- Provides targeted answers

---

## Comparison with Search Mode

| Feature | URL Detection | Search Mode |
|---------|--------------|-------------|
| **Trigger** | Automatic (detects URLs) | Manual toggle |
| **Source** | Specific URLs you provide | DuckDuckGo/News APIs |
| **Content** | Full page text | Search snippets |
| **Accuracy** | Very high (actual content) | Good (search results) |
| **Use Case** | Specific pages | General queries |

**Use URL detection when:**
- You have a specific link to analyze
- You want detailed content extraction
- You need exact information from a source

**Use Search Mode when:**
- You want general information
- You need latest news/weather
- You don't have specific URLs

---

## Privacy & Security

### What is sent to the model:
- ✅ The URL itself
- ✅ Page title
- ✅ Extracted text content
- ❌ Images, scripts, or other media
- ❌ Cookies or session data

### Safety:
- Only fetches public pages
- Does not submit forms or POST data
- Does not execute JavaScript
- Respects robots.txt (if needed, can be added)

---

## Examples in Production

Try these real URLs:

### Documentation
```
Explain FastAPI dependency injection: https://fastapi.tiangolo.com/tutorial/dependencies/
```

### GitHub README
```
Summarize this project: https://github.com/user/repo
```

### Blog Posts
```
What are the main points? https://realpython.com/python-gil/
```

### Stack Overflow
```
How does this solution work? https://stackoverflow.com/questions/123456
```

---

## Future Enhancements

Potential improvements:
- [ ] PDF content extraction
- [ ] Image OCR for text in images
- [ ] Support for more than 3 URLs
- [ ] Caching of fetched content
- [ ] Respect for robots.txt
- [ ] Rate limiting protection
- [ ] Parallel URL fetching
- [ ] Content quality scoring
- [ ] Language detection & translation

---

## Related Features

- **Search Mode** - Global web search for queries
- **Context Memory** - Conversation history feeding
- **Export Training Data** - Custom model fine-tuning

---

**Your AI assistant now browses the web for you!** 🌐  
Just include a URL in your message and watch it work!
