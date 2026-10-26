# Video → FAQ

Turn a screen recording of a product walkthrough into a ready-to-publish help-center article, in one click on Google Colab.

Upload an MP4 and get back a ZIP with:
- **An FAQ article in HTML**, structured for both humans and AI (chatbots and AI search read it cleanly)
- **GIFs cut automatically** at the key steps, with placeholders showing where to drop each one in your help center

Built for support teams who record a quick video for every new feature and never find the time to write the article.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/paupz313/video-to-faq/blob/main/video_to_faq.ipynb)

## How to use

1. Open the notebook in Colab with the button above.
2. Add your Gemini API key as a Colab secret named `GEMINI_API_KEY` (🔑 icon in the left sidebar), or paste it when prompted. You can get a key from [Google AI Studio](https://aistudio.google.com/apikey).
3. Fill in the form: your company name, the article language, formal or informal tone.
4. Click ▶️, upload your MP4, and the ZIP downloads at the end.

## How it works

1. The video is sent to Gemini, which watches it and writes the article following strict style rules: short sentences, consistent names for interface elements, H1 > H2 > list structure.
2. Gemini also returns the timestamps of the steps worth showing visually.
3. ffmpeg cuts those segments into optimized GIFs.
4. The uploaded video is deleted from Gemini and from the Colab session when the run ends.

## Privacy

Your video is processed by the Gemini API under your own key. Don't upload recordings that show customer data.

## Stack

Python · Google Gemini (video understanding) · ffmpeg · Google Colab
